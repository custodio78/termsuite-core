from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import json
from pathlib import Path
from typing import Dict

from app.models import (
    ExtractionRequest, ExtractionResponse, JobStatusResponse,
    UploadResponse, JobStatus
)
from app.services.termsuite import TermSuiteService
from app.services.tmx_parser import TMXParser
from app.services.excel_export import ExcelExporter
from app.utils.file_handler import FileHandler

app = FastAPI(
    title="TermSuite API",
    description="API REST para extracción terminológica con TermSuite",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servicios
termsuite_service = TermSuiteService()
tmx_parser = TMXParser()
excel_exporter = ExcelExporter()
file_handler = FileHandler()

# Estado de trabajos en memoria (en producción usar Redis/DB)
jobs: Dict[str, dict] = {}


@app.get("/")
async def root():
    return {
        "message": "TermSuite API",
        "version": "1.0.0",
        "endpoints": {
            "upload_tmx": "/api/upload-tmx",
            "upload_corpus": "/api/upload-corpus",
            "extract": "/api/extract",
            "status": "/api/status/{job_id}",
            "export": "/api/export/excel/{job_id}"
        }
    }


@app.post("/api/upload-tmx", response_model=UploadResponse)
async def upload_tmx(file: UploadFile = File(...)):
    """Subir memoria de traducción TMX"""
    if not file.filename.endswith('.tmx'):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos .tmx")
    
    file_id = str(uuid.uuid4())
    file_path = file_handler.save_upload(file_id, file, "tmx")
    
    # Parsear TMX para validar
    try:
        terms = tmx_parser.parse(file_path)
        # Guardar términos parseados
        terms_path = file_handler.get_path("tmx", f"{file_id}_terms.json")
        with open(terms_path, 'w', encoding='utf-8') as f:
            json.dump(terms, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al parsear TMX: {str(e)}")
    
    return UploadResponse(
        file_id=file_id,
        filename=file.filename,
        size=os.path.getsize(file_path),
        message=f"TMX subido exitosamente. {len(terms)} términos encontrados."
    )


@app.post("/api/upload-corpus", response_model=UploadResponse)
async def upload_corpus(file: UploadFile = File(...)):
    """Subir corpus de texto (.txt o .zip con múltiples .txt)"""
    allowed_extensions = ['.txt', '.zip']
    if not any(file.filename.endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=400, 
            detail="Solo se permiten archivos .txt o .zip"
        )
    
    corpus_id = str(uuid.uuid4())
    file_path = file_handler.save_upload(corpus_id, file, "corpus")
    
    # Si es ZIP, extraer
    if file.filename.endswith('.zip'):
        file_handler.extract_zip(file_path, corpus_id)
    
    return UploadResponse(
        file_id=corpus_id,
        filename=file.filename,
        size=os.path.getsize(file_path),
        message="Corpus subido exitosamente"
    )


@app.post("/api/extract", response_model=ExtractionResponse)
async def extract_terms(
    request: ExtractionRequest,
    background_tasks: BackgroundTasks
):
    """Extraer términos del corpus"""
    job_id = str(uuid.uuid4())
    
    # Validar que existe el corpus
    corpus_path = file_handler.get_corpus_path(request.corpus_id)
    if not corpus_path.exists():
        raise HTTPException(status_code=404, detail="Corpus no encontrado")
    
    # Validar TMX si se especifica
    if request.use_tmx and request.tmx_id:
        tmx_terms_path = file_handler.get_path("tmx", f"{request.tmx_id}_terms.json")
        if not tmx_terms_path.exists():
            raise HTTPException(status_code=404, detail="TMX no encontrado")
    
    # Crear trabajo
    jobs[job_id] = {
        "status": JobStatus.PENDING,
        "progress": 0,
        "message": "Trabajo en cola",
        "request": request.dict()
    }
    
    # Ejecutar en background
    background_tasks.add_task(
        process_extraction,
        job_id,
        request
    )
    
    return ExtractionResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Extracción iniciada"
    )


@app.get("/api/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Obtener estado del trabajo"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    
    job = jobs[job_id]
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job.get("progress", 0),
        message=job.get("message", ""),
        result_file=job.get("result_file"),
        error=job.get("error")
    )


@app.get("/api/export/excel/{job_id}")
async def export_excel(job_id: str):
    """Exportar resultados a Excel"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    
    job = jobs[job_id]
    if job["status"] != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400, 
            detail=f"El trabajo está en estado: {job['status']}"
        )
    
    excel_path = file_handler.get_path("outputs", f"{job_id}.xlsx")
    if not excel_path.exists():
        raise HTTPException(status_code=404, detail="Archivo Excel no encontrado")
    
    return FileResponse(
        path=excel_path,
        filename=f"terms_{job_id}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


async def process_extraction(job_id: str, request: ExtractionRequest):
    """Procesar extracción de términos (background task)"""
    try:
        jobs[job_id]["status"] = JobStatus.PROCESSING
        jobs[job_id]["progress"] = 10
        jobs[job_id]["message"] = "Iniciando TermSuite..."
        
        # Ejecutar TermSuite
        corpus_path = file_handler.get_corpus_path(request.corpus_id)
        output_json = file_handler.get_path("outputs", f"{job_id}.json")
        
        jobs[job_id]["progress"] = 30
        jobs[job_id]["message"] = "Extrayendo términos..."
        
        termsuite_service.extract_terms(
            corpus_path=str(corpus_path),
            output_path=str(output_json),
            language=request.language.value,
            min_frequency=request.min_frequency
        )
        
        jobs[job_id]["progress"] = 70
        jobs[job_id]["message"] = "Procesando resultados..."
        
        # Cargar resultados
        with open(output_json, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # Filtrar con TMX si se especifica
        if request.use_tmx and request.tmx_id:
            tmx_terms_path = file_handler.get_path("tmx", f"{request.tmx_id}_terms.json")
            with open(tmx_terms_path, 'r', encoding='utf-8') as f:
                tmx_terms = json.load(f)
            results = filter_with_tmx(results, tmx_terms)
        
        jobs[job_id]["progress"] = 90
        jobs[job_id]["message"] = "Generando Excel..."
        
        # Exportar a Excel
        excel_path = file_handler.get_path("outputs", f"{job_id}.xlsx")
        excel_exporter.export(results, str(excel_path))
        
        jobs[job_id]["status"] = JobStatus.COMPLETED
        jobs[job_id]["progress"] = 100
        jobs[job_id]["message"] = "Extracción completada"
        jobs[job_id]["result_file"] = f"{job_id}.xlsx"
        
    except Exception as e:
        jobs[job_id]["status"] = JobStatus.FAILED
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["message"] = f"Error: {str(e)}"


def filter_with_tmx(results: dict, tmx_terms: list) -> dict:
    """Filtrar resultados marcando términos que están en TMX"""
    tmx_set = set(term.lower() for term in tmx_terms)
    
    if "terms" in results:
        for term in results["terms"]:
            term["in_tmx"] = term.get("groupingKey", "").lower() in tmx_set
    
    return results
