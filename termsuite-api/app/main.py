from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import json
from pathlib import Path
from typing import Dict, Optional

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

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

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


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Página principal con interfaz web"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api")
async def api_info():
    """Información de la API"""
    return {
        "message": "TermSuite API",
        "version": "1.0.0",
        "endpoints": {
            "upload_tmx": "/api/upload-tmx",
            "upload_corpus": "/api/upload-corpus",
            "extract": "/api/extract",
            "status": "/api/status/{job_id}",
            "export": "/api/export/excel/{job_id}",
            "export_tmx": "/api/export/tmx-excel/{tmx_id}"
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
    
    # Parsear TMX para obtener idiomas disponibles y términos
    try:
        # Obtener idiomas disponibles en el TMX
        available_languages = tmx_parser.get_available_languages(file_path)
        
        # Si se especificó idioma, extraer términos
        if language:
            terms = tmx_parser.parse(file_path, language=language)
            terms_freq = tmx_parser.parse_with_frequency(file_path, language=language)
            
            # Guardar términos parseados con información del idioma y frecuencias
            terms_data = {
                "language": language,
                "terms": terms,
                "frequencies": terms_freq,
                "total": len(terms),
                "total_occurrences": sum(terms_freq.values()),
                "available_languages": available_languages
            }
            terms_path = file_handler.get_path("tmx", f"{file_id}_terms.json")
            with open(terms_path, 'w', encoding='utf-8') as f:
                json.dump(terms_data, f, ensure_ascii=False, indent=2)
            
            lang_msg = f" del idioma '{language}'"
            message = f"TMX subido exitosamente. {len(terms)} términos{lang_msg} encontrados."
        else:
            # Solo guardar idiomas disponibles
            terms_data = {
                "available_languages": available_languages
            }
            terms_path = file_handler.get_path("tmx", f"{file_id}_terms.json")
            with open(terms_path, 'w', encoding='utf-8') as f:
                json.dump(terms_data, f, ensure_ascii=False, indent=2)
            
            message = f"TMX subido exitosamente. Idiomas disponibles: {', '.join(available_languages)}"
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al parsear TMX: {str(e)}")
    
    return UploadResponse(
        file_id=file_id,
        filename=file.filename,
        size=os.path.getsize(file_path),
        message=message
    )


@app.get("/api/tmx-languages/{tmx_id}")
async def get_tmx_languages(tmx_id: str):
    """Obtener idiomas disponibles en un TMX subido"""
    tmx_terms_path = file_handler.get_path("tmx", f"{tmx_id}_terms.json")
    if not tmx_terms_path.exists():
        raise HTTPException(status_code=404, detail="TMX no encontrado")
    
    with open(tmx_terms_path, 'r', encoding='utf-8') as f:
        tmx_data = json.load(f)
    
    available_languages = tmx_data.get('available_languages', [])
    
    return {
        "tmx_id": tmx_id,
        "available_languages": available_languages
    }


@app.post("/api/extract-tmx-language")
async def extract_tmx_language(tmx_id: str, language: str):
    """Extraer términos de un TMX para un idioma específico"""
    # Buscar archivo TMX
    tmx_dir = file_handler.uploads_dir / 'tmx'
    tmx_file_path = None
    
    if tmx_dir.exists():
        for file in tmx_dir.glob(f"{tmx_id}*"):
            if file.suffix == '.tmx':
                tmx_file_path = file
                break
    
    if not tmx_file_path or not tmx_file_path.exists():
        raise HTTPException(status_code=404, detail="TMX no encontrado")
    
    # Extraer términos del idioma especificado
    try:
        terms = tmx_parser.parse(str(tmx_file_path), language=language)
        terms_freq = tmx_parser.parse_with_frequency(str(tmx_file_path), language=language)
        
        # Actualizar archivo de términos
        terms_data = {
            "language": language,
            "terms": terms,
            "frequencies": terms_freq,
            "total": len(terms),
            "total_occurrences": sum(terms_freq.values())
        }
        terms_path = file_handler.get_path("tmx", f"{tmx_id}_terms.json")
        with open(terms_path, 'w', encoding='utf-8') as f:
            json.dump(terms_data, f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "language": language,
            "total_terms": len(terms),
            "message": f"{len(terms)} términos del idioma '{language}' extraídos"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


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
async def export_tmx_to_excel(
    tmx_id: str,
    min_frequency: Optional[int] = None,
    top_n: Optional[int] = None,
    min_words: Optional[int] = None,
    max_words: Optional[int] = None,
    sort_by: str = "frequency",
    sort_order: str = "desc",
    format: str = "excel",
    columns: Optional[str] = None,
    exclude_numbers: bool = False,
    contains: Optional[str] = None,
    include_translation: bool = False
):
    """
    Exportar términos de TMX directamente a Excel con opciones de filtrado
    
    Args:
        tmx_id: ID del TMX subido previamente
        min_frequency: Frecuencia mínima (ej: 5)
        top_n: Top N términos más frecuentes (ej: 100)
        min_words: Mínimo número de palabras (ej: 2)
        max_words: Máximo número de palabras (ej: 5)
        sort_by: Ordenar por: frequency, alphabetical, length, words
        sort_order: Orden: asc o desc
        format: Formato de salida: excel, csv, json
        columns: Columnas a incluir (separadas por coma)
        exclude_numbers: Excluir términos con números
        contains: Filtrar términos que contengan este texto
        include_translation: Incluir traducción si está disponible
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
    
    # Crear estructura para Excel
    terms_for_excel = []
    for term in terms_list:
        freq = frequencies.get(term, 1)
        word_count = len(term.split())
        
        # Aplicar filtros
        # Filtro de frecuencia mínima
        if min_frequency and freq < min_frequency:
            continue
        
        # Filtro de palabras
        if min_words and word_count < min_words:
            continue
        if max_words and word_count > max_words:
            continue
        
        # Filtro de números
        if exclude_numbers and any(char.isdigit() for char in term):
            continue
        
        # Filtro de contenido
        if contains and contains.lower() not in term.lower():
            continue
        
        terms_for_excel.append({
            'Término': term,
            'Frecuencia': freq,
            'Longitud': len(term),
            'Palabras': word_count,
            'Idioma': language
        })
    
    # Ordenar según parámetros
    if sort_by == "frequency":
        terms_for_excel.sort(key=lambda x: x['Frecuencia'], reverse=(sort_order == "desc"))
    elif sort_by == "alphabetical":
        terms_for_excel.sort(key=lambda x: x['Término'].lower(), reverse=(sort_order == "desc"))
    elif sort_by == "length":
        terms_for_excel.sort(key=lambda x: x['Longitud'], reverse=(sort_order == "desc"))
    elif sort_by == "words":
        terms_for_excel.sort(key=lambda x: x['Palabras'], reverse=(sort_order == "desc"))
    
    # Aplicar top_n después de ordenar
    if top_n:
        terms_for_excel = terms_for_excel[:top_n]
    
    # Agregar número después de filtrar y ordenar
    for idx, item in enumerate(terms_for_excel, 1):
        item['Número'] = idx
    
    # Si no hay términos después de filtrar
    if not terms_for_excel:
        raise HTTPException(
            status_code=404, 
            detail="No se encontraron términos con los filtros aplicados"
        )
    
    # Incluir traducción si se solicita
    if include_translation:
        # Buscar el archivo TMX original en uploads/tmx/
        tmx_dir = file_handler.uploads_dir / 'tmx'
        tmx_file_path = None
        
        # Buscar archivo con el ID
        if tmx_dir.exists():
            for file in tmx_dir.glob(f"{tmx_id}*"):
                if file.suffix == '.tmx':
                    tmx_file_path = file
                    break
        
        if tmx_file_path and tmx_file_path.exists():
            try:
                # Pasar el idioma para identificar correctamente source y target
                translations = tmx_parser.parse_with_translations(str(tmx_file_path), source_lang=language)
                
                # Crear diccionario de traducciones exactas
                trans_dict_exact = {}
                # Crear lista de segmentos para búsqueda parcial
                trans_segments = []
                
                for trans in translations:
                    source = trans.get('source', '').strip()
                    target = trans.get('target', '').strip()
                    if source and target:
                        # Guardar traducción exacta
                        trans_dict_exact[source.lower()] = target
                        # Guardar para búsqueda parcial
                        trans_segments.append({
                            'source': source,
                            'target': target,
                            'source_lower': source.lower()
                        })
                
                # Agregar traducción a cada término
                for item in terms_for_excel:
                    term = item['Término']
                    term_lower = term.lower()
                    
                    # 1. Buscar coincidencia exacta
                    if term_lower in trans_dict_exact:
                        item['Traducción'] = trans_dict_exact[term_lower]
                        item['Tipo Match'] = 'Exacto'
                    else:
                        # 2. Buscar en segmentos (coincidencia parcial)
                        found = False
                        for seg in trans_segments:
                            if term_lower in seg['source_lower']:
                                # Encontrado en un segmento
                                item['Traducción'] = f"[Segmento] {seg['target']}"
                                item['Tipo Match'] = 'Parcial'
                                found = True
                                break
                        
                        if not found:
                            item['Traducción'] = ''
                            item['Tipo Match'] = 'No encontrado'
                
            except Exception as e:
                # Si hay error al parsear traducciones, agregar columna vacía
                for item in terms_for_excel:
                    item['Traducción'] = f'Error: {str(e)}'
                    item['Tipo Match'] = 'Error'
        else:
            # Si no se encuentra el archivo TMX, agregar columna vacía
            for item in terms_for_excel:
                item['Traducción'] = 'TMX no encontrado'
    
    # Seleccionar columnas si se especifica
    if columns:
        selected_cols = [col.strip().capitalize() for col in columns.split(',')]
        # Mapeo de nombres de columnas
        col_mapping = {
            'Term': 'Término',
            'Frequency': 'Frecuencia',
            'Length': 'Longitud',
            'Words': 'Palabras',
            'Language': 'Idioma',
            'Translation': 'Traducción',
            'Number': 'Número'
        }
        # Convertir nombres en inglés a español
        selected_cols = [col_mapping.get(col, col) for col in selected_cols]
        # Filtrar solo columnas existentes
        available_cols = list(terms_for_excel[0].keys()) if terms_for_excel else []
        selected_cols = [col for col in selected_cols if col in available_cols]
        if selected_cols:
            terms_for_excel = [{k: v for k, v in item.items() if k in selected_cols} 
                              for item in terms_for_excel]
    
    import pandas as pd
    df = pd.DataFrame(terms_for_excel)
    
    # Exportar según formato
    if format == "json":
        output_filename = f"tmx_{tmx_id}.json"
        output_path = file_handler.get_path("outputs", output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(terms_for_excel, f, ensure_ascii=False, indent=2)
        return FileResponse(
            path=output_path,
            filename=f"terminos_tmx_{language}.json",
            media_type="application/json"
        )
    
    elif format == "csv":
        output_filename = f"tmx_{tmx_id}.csv"
        output_path = file_handler.get_path("outputs", output_filename)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        return FileResponse(
            path=output_path,
            filename=f"terminos_tmx_{language}.csv",
            media_type="text/csv"
        )
    
    # Formato Excel (por defecto)
    excel_filename = f"tmx_{tmx_id}.xlsx"
    excel_path = file_handler.get_path("outputs", excel_filename)
    
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    
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
    preferred_order = ['Número', 'Término', 'Frecuencia', 'Longitud', 'Palabras', 'Idioma', 'Traducción']
    existing_cols = [col for col in preferred_order if col in df.columns]
    other_cols = [col for col in df.columns if col not in existing_cols]
    df = df[existing_cols + other_cols]
    
    # Ajustar anchos dinámicamente
    column_widths = {
        'Número': 10,
        'Término': 50,
        'Frecuencia': 12,
        'Longitud': 12,
        'Palabras': 12,
        'Idioma': 12,
        'Traducción': 50
    }
    
    for idx, col in enumerate(df.columns, 1):
        col_letter = chr(64 + idx)  # A, B, C, etc.
        width = column_widths.get(col, 15)
        ws.column_dimensions[col_letter].width = width
    
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
