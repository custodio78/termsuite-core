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
async def upload_tmx(
    file: UploadFile = File(...),
    language: str = None
):
    """
    Subir memoria de traducción TMX
    
    Args:
        file: Archivo TMX
        language: Código de idioma para extraer términos (en, es, fr, de, etc.)
                 Si no se especifica, extrae todos los términos.
    """
    if not file.filename.endswith('.tmx'):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos .tmx")
    
    file_id = str(uuid.uuid4())
    file_path = file_handler.save_upload(file_id, file, "tmx")
    
    # Parsear TMX para validar y extraer términos del idioma especificado
    try:
        terms = tmx_parser.parse(file_path, language=language)
        terms_freq = tmx_parser.parse_with_frequency(file_path, language=language)
        
        # Guardar términos parseados con información del idioma y frecuencias
        terms_data = {
            "language": language,
            "terms": terms,
            "frequencies": terms_freq,
            "total": len(terms),
            "total_occurrences": sum(terms_freq.values())
        }
        terms_path = file_handler.get_path("tmx", f"{file_id}_terms.json")
        with open(terms_path, 'w', encoding='utf-8') as f:
            json.dump(terms_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al parsear TMX: {str(e)}")
    
    lang_msg = f" del idioma '{language}'" if language else ""
    return UploadResponse(
        file_id=file_id,
        filename=file.filename,
        size=os.path.getsize(file_path),
        message=f"TMX subido exitosamente. {len(terms)} términos{lang_msg} encontrados."
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


@app.get("/api/export/tmx-excel/{tmx_id}")
async def export_tmx_to_excel(tmx_id: str):
    """
    Exportar términos de TMX directamente a Excel
    
    Args:
        tmx_id: ID del TMX subido previamente
    """
    # Verificar que existe el TMX
    tmx_terms_path = file_handler.get_path("tmx", f"{tmx_id}_terms.json")
    if not tmx_terms_path.exists():
        raise HTTPException(status_code=404, detail="TMX no encontrado")
    
    # Cargar términos del TMX
    with open(tmx_terms_path, 'r', encoding='utf-8') as f:
        tmx_data = json.load(f)
    
    # Extraer términos (compatible con formato nuevo y antiguo)
    if isinstance(tmx_data, dict):
        terms_list = tmx_data.get('terms', [])
        frequencies = tmx_data.get('frequencies', {})
        language = tmx_data.get('language', 'unknown')
        total_occurrences = tmx_data.get('total_occurrences', 0)
    else:
        terms_list = tmx_data
        frequencies = {}
        language = 'unknown'
        total_occurrences = 0
    
    # Crear estructura para Excel ordenada por frecuencia
    terms_for_excel = []
    for term in terms_list:
        freq = frequencies.get(term, 1)
        terms_for_excel.append({
            'Término': term,
            'Frecuencia': freq,
            'Longitud': len(term),
            'Palabras': len(term.split()),
            'Idioma': language
        })
    
    # Ordenar por frecuencia descendente
    terms_for_excel.sort(key=lambda x: x['Frecuencia'], reverse=True)
    
    # Agregar número después de ordenar
    for idx, item in enumerate(terms_for_excel, 1):
        item['Número'] = idx
    
    # Generar Excel
    excel_filename = f"tmx_{tmx_id}.xlsx"
    excel_path = file_handler.get_path("outputs", excel_filename)
    
    import pandas as pd
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    
    df = pd.DataFrame(terms_for_excel)
    
    # Crear Excel con formato
    wb = Workbook()
    ws = wb.active
    ws.title = "Términos TMX"
    
    # Estilos
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=11)
    
    # Escribir encabezados
    for col_idx, column in enumerate(df.columns, 1):
        cell = ws.cell(row=1, column=col_idx, value=column)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Escribir datos
    for row_idx, row in enumerate(df.values, 2):
        for col_idx, value in enumerate(row, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.alignment = Alignment(vertical='center')
    
    # Reordenar columnas para mejor visualización
    df = df[['Número', 'Término', 'Frecuencia', 'Longitud', 'Palabras', 'Idioma']]
    
    # Ajustar anchos
    ws.column_dimensions['A'].width = 10  # Número
    ws.column_dimensions['B'].width = 50  # Término
    ws.column_dimensions['C'].width = 12  # Frecuencia
    ws.column_dimensions['D'].width = 12  # Longitud
    ws.column_dimensions['E'].width = 12  # Palabras
    ws.column_dimensions['F'].width = 12  # Idioma
    
    # Congelar primera fila
    ws.freeze_panes = 'A2'
    
    # Guardar
    wb.save(excel_path)
    
    return FileResponse(
        path=excel_path,
        filename=f"terminos_tmx_{language}.xlsx",
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
                tmx_data = json.load(f)
            # Extraer lista de términos (compatible con formato antiguo y nuevo)
            tmx_terms = tmx_data.get('terms', tmx_data) if isinstance(tmx_data, dict) else tmx_data
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
