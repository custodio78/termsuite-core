from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import json
import datetime
from pathlib import Path
from typing import Dict, Optional, List

from app.models import (
    ExtractionRequest, ExtractionResponse, JobStatusResponse,
    UploadResponse, JobStatus, BatchTranslationRequest, ExtractTMXLanguageRequest,
    DomainClassificationRequest
)
from app.services.termsuite import TermSuiteService
from app.services.tmx_parser import TMXParser
from app.services.excel_export import ExcelExporter
from app.services.ollama_translator import OllamaTranslator
from app.utils.file_handler import FileHandler

app = FastAPI(
    title="LinguaTerms API",
    description="API REST para extracción inteligente de términos técnicos",
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
ollama_translator = OllamaTranslator()

# Configurar logging para Ollama (se hace después de definir add_ollama_log)
file_handler = FileHandler()

# Estado de trabajos en memoria (en producción usar Redis/DB)
jobs: Dict[str, dict] = {}

# Logs de Ollama en tiempo real
ollama_logs: List[dict] = []

def add_ollama_log(action: str, term: str = None, status: str = None, details: str = None, prompt: str = None, response: str = None):
    """Agregar log de Ollama con prompt y respuesta"""
    import datetime
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "action": action,
        "term": term,
        "status": status,
        "details": details,
        "prompt": prompt,
        "response": response
    }
    ollama_logs.append(log_entry)
    
    # Mantener solo los últimos 200 logs
    if len(ollama_logs) > 200:
        ollama_logs.pop(0)
    
    print(f"OLLAMA LOG: {action} - {term} - {status} - {details}")

# Configurar logging para Ollama ahora que add_ollama_log está definida
ollama_translator.log_callback = add_ollama_log


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Página principal con interfaz web mejorada"""
    return templates.TemplateResponse("index_v2.html", {"request": request})

@app.get("/classic", response_class=HTMLResponse)
async def classic_interface(request: Request):
    """Interfaz clásica (legacy)"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/monitor", response_class=HTMLResponse)
async def ollama_monitor(request: Request):
    """Monitor de Ollama en tiempo real"""
    return templates.TemplateResponse("ollama_monitor.html", {"request": request})


@app.get("/api")
async def api_info():
    """Información de la API"""
    return {
        "message": "LinguaTerms API",
        "version": "1.0.0",
        "endpoints": {
            "upload_tmx": "/api/upload-tmx",
            "upload_corpus": "/api/upload-corpus",
            "extract": "/api/extract",
            "status": "/api/status/{job_id}",
            "export": "/api/export/excel/{job_id}",
            "export_tmx": "/api/export/tmx-excel/{tmx_id}",
            "ollama_status": "/api/ollama/status"
        }
    }


@app.get("/api/ollama/status")
async def ollama_status():
    """Verificar estado de conexión con Ollama"""
    return ollama_translator.test_connection()


@app.post("/api/ollama/translate")
async def ollama_translate_single(
    term: str,
    source_lang: str,
    target_lang: str,
    context: Optional[str] = None
):
    """
    Traducir un término individual usando Ollama
    
    Args:
        term: Término a traducir
        source_lang: Idioma origen (es, en, fr, etc.)
        target_lang: Idioma destino
        context: Contexto adicional (opcional)
    """
    if not ollama_translator.is_available():
        raise HTTPException(
            status_code=503, 
            detail="Servicio Ollama no disponible"
        )
    
    translation_result = ollama_translator.translate_term(term, source_lang, target_lang, context)
    
    if translation_result:
        return {
            "term": term,
            "translation": translation_result['translation'],
            "context": translation_result['context'],
            "source_lang": source_lang,
            "target_lang": target_lang
        }
    else:
        raise HTTPException(
            status_code=400,
            detail="No se pudo traducir el término"
        )


@app.get("/api/ollama/cache/stats")
async def ollama_cache_stats():
    """Obtener estadísticas del caché de Ollama"""
    return ollama_translator.get_cache_stats()


@app.get("/api/ollama/logs")
async def get_ollama_logs(limit: int = 50):
    """Obtener logs recientes de Ollama en tiempo real"""
    return {
        "logs": ollama_logs[-limit:] if ollama_logs else [],
        "total_logs": len(ollama_logs)
    }


@app.delete("/api/ollama/cache")
async def clear_ollama_cache(
    source_lang: Optional[str] = None,
    target_lang: Optional[str] = None
):
    """
    Limpiar caché de traducciones de Ollama
    
    Args:
        source_lang: Idioma origen (opcional, para limpiar caché específico)
        target_lang: Idioma destino (opcional, para limpiar caché específico)
    """
    ollama_translator.clear_cache(source_lang, target_lang)
    
    if source_lang and target_lang:
        message = f"Caché limpiado para {source_lang} → {target_lang}"
    else:
        message = "Todo el caché de traducciones ha sido limpiado"
    
    return {
        "success": True,
        "message": message
    }


@app.post("/api/ollama/classify-domain")
async def ollama_classify_domain(request: DomainClassificationRequest):
    """
    Clasificar múltiples términos por relevancia al dominio usando Ollama
    
    Args:
        terms: Lista de términos a clasificar
        domain_description: Descripción del ámbito/dominio
        language: Idioma de los términos
    """
    if not ollama_translator.is_available():
        raise HTTPException(
            status_code=503, 
            detail="Servicio Ollama no disponible"
        )
    
    if len(request.terms) > 100:
        raise HTTPException(
            status_code=400,
            detail="Máximo 100 términos por lote"
        )
    
    if not request.domain_description.strip():
        raise HTTPException(
            status_code=400,
            detail="La descripción del dominio es requerida"
        )
    
    # Clasificar términos usando el método asíncrono
    import asyncio
    classifications = await ollama_translator.classify_terms_domain_batch(
        request.terms, 
        request.domain_description, 
        request.language
    )
    
    return {
        "domain_description": request.domain_description,
        "language": request.language,
        "total_terms": len(request.terms),
        "classified_terms": len(classifications),
        "classifications": classifications
    }


@app.post("/api/ollama/translate-batch")
async def ollama_translate_batch(request: BatchTranslationRequest):
    """
    Traducir múltiples términos en una sola petición (optimizado)
    """
    if not ollama_translator.is_available():
        raise HTTPException(
            status_code=503, 
            detail="Servicio Ollama no disponible"
        )
    
    if len(request.terms) > 50:
        raise HTTPException(
            status_code=400,
            detail="Máximo 50 términos por lote"
        )
    
    translations = ollama_translator.translate_batch_single_request(request.terms, request.source_lang, request.target_lang)
    
    return {
        "source_lang": request.source_lang,
        "target_lang": request.target_lang,
        "total_terms": len(request.terms),
        "translated_terms": len(translations),
        "translations": translations
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
    # Buscar archivo TMX directamente
    tmx_dir = file_handler.uploads_dir / 'tmx'
    tmx_file_path = None
    
    if tmx_dir.exists():
        for file in tmx_dir.glob(f"{tmx_id}*"):
            if file.suffix == '.tmx':
                tmx_file_path = file
                break
    
    if not tmx_file_path or not tmx_file_path.exists():
        raise HTTPException(status_code=404, detail="TMX no encontrado")
    
    try:
        # Obtener idiomas directamente del TMX
        available_languages = tmx_parser.get_available_languages(str(tmx_file_path))
        
        return {
            "tmx_id": tmx_id,
            "available_languages": available_languages
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al leer TMX: {str(e)}")


@app.get("/api/tmx-debug/{tmx_id}")
async def debug_tmx(tmx_id: str, search: Optional[str] = None):
    """
    Endpoint de diagnóstico para verificar términos en TMX
    
    Args:
        tmx_id: ID del TMX
        search: Término a buscar (opcional)
    """
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
    
    try:
        # Obtener idiomas
        languages = tmx_parser.get_available_languages(str(tmx_file_path))
        
        result = {
            "tmx_id": tmx_id,
            "languages": languages,
            "details": {}
        }
        
        # Extraer información por idioma
        for lang in languages:
            terms = tmx_parser.parse(str(tmx_file_path), language=lang)
            terms_freq = tmx_parser.parse_with_frequency(str(tmx_file_path), language=lang)
            
            lang_info = {
                "total_unique_terms": len(terms),
                "total_occurrences": sum(terms_freq.values()),
                "top_10": sorted(terms_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            }
            
            # Si hay búsqueda, buscar el término
            if search:
                search_lower = search.lower()
                exact_match = search in terms
                partial_matches = [t for t in terms if search_lower in t.lower()][:10]
                
                lang_info["search"] = {
                    "term": search,
                    "exact_match": exact_match,
                    "frequency": terms_freq.get(search, 0) if exact_match else 0,
                    "partial_matches": [
                        {"term": t, "frequency": terms_freq.get(t, 0)} 
                        for t in partial_matches
                    ]
                }
            
            result["details"][lang] = lang_info
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al analizar TMX: {str(e)}")


@app.post("/api/extract-tmx-language")
async def extract_tmx_language_post(request: ExtractTMXLanguageRequest):
    """
    Extraer términos de un TMX para un idioma específico con traducción opcional (POST con JSON)
    """
    return await _extract_tmx_language_impl(
        request.tmx_id, 
        request.language, 
        request.target_language, 
        request.use_termsuite,
        request.domain_description
    )


@app.get("/api/extract-tmx-language")
async def extract_tmx_language_get(
    tmx_id: str, 
    language: str, 
    target_language: Optional[str] = None,
    use_termsuite: bool = False,
    domain_description: Optional[str] = None
):
    """
    Extraer términos de un TMX para un idioma específico con traducción opcional (GET con query params)
    """
    return await _extract_tmx_language_impl(tmx_id, language, target_language, use_termsuite, domain_description)


async def _extract_tmx_language_impl(
    tmx_id: str, 
    language: str, 
    target_language: Optional[str] = None,
    use_termsuite: bool = False,
    domain_description: Optional[str] = None
):
    """
    Implementación común para extraer términos de un TMX para un idioma específico
    
    Args:
        tmx_id: ID del TMX
        language: Idioma origen
        target_language: Idioma destino (opcional)
        use_termsuite: Si True, usa TermSuite para extraer términos individuales
        domain_description: Descripción del ámbito/dominio para clasificar términos (opcional)
    """
    
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
        if use_termsuite:
            # Modo TermSuite: Extraer términos individuales de los segmentos
            segments = tmx_parser.parse(str(tmx_file_path), language=language)
            
            # Crear directorio temporal para el corpus
            temp_corpus_dir = file_handler.get_path("tmx", f"{tmx_id}_corpus_{language}")
            temp_corpus_dir.mkdir(exist_ok=True)
            
            # Crear archivo de texto con los segmentos
            temp_corpus_file = temp_corpus_dir / "segments.txt"
            with open(temp_corpus_file, 'w', encoding='utf-8') as f:
                for segment in segments:
                    f.write(segment + '\n')
            
            # Ejecutar TermSuite sobre los segmentos
            temp_output_path = file_handler.get_path("tmx", f"{tmx_id}_termsuite_{language}.json")
            termsuite_service.extract_terms(
                corpus_path=str(temp_corpus_dir),
                output_path=str(temp_output_path),
                language=language,
                min_frequency=1
            )
            
            # Leer resultados de TermSuite
            with open(temp_output_path, 'r', encoding='utf-8') as f:
                termsuite_results = json.load(f)
            
            # Extraer términos y frecuencias
            terms = []
            terms_freq = {}
            
            if "terms" in termsuite_results:
                for term_obj in termsuite_results["terms"]:
                    term = term_obj.get("groupingKey", "")
                    freq = term_obj.get("frequency", 1)
                    if term:
                        terms.append(term)
                        terms_freq[term] = freq
            
            # Limpiar archivos temporales
            import shutil
            if temp_corpus_dir.exists():
                shutil.rmtree(temp_corpus_dir)
            temp_output_path.unlink(missing_ok=True)
            
        else:
            # Modo directo: Extraer segmentos completos
            terms = tmx_parser.parse(str(tmx_file_path), language=language)
            terms_freq = tmx_parser.parse_with_frequency(str(tmx_file_path), language=language)
        
        # Actualizar archivo de términos
        terms_data = {
            "language": language,
            "terms": terms,
            "frequencies": terms_freq,
            "total": len(terms),
            "total_occurrences": sum(terms_freq.values()),
            "extraction_mode": "termsuite" if use_termsuite else "direct"
        }
        
        # Si se especifica idioma destino, guardarlo también
        if target_language:
            terms_data["target_language"] = target_language
        
        # Si se especifica descripción del dominio, guardarla también
        if domain_description:
            terms_data["domain_description"] = domain_description.strip()
        
        terms_path = file_handler.get_path("tmx", f"{tmx_id}_terms.json")
        with open(terms_path, 'w', encoding='utf-8') as f:
            json.dump(terms_data, f, ensure_ascii=False, indent=2)
        
        mode_msg = " (con TermSuite)" if use_termsuite else ""
        msg = f"{len(terms)} términos del idioma '{language}' extraídos{mode_msg}"
        if target_language:
            msg += f" (traducción: {target_language})"
        
        # NUEVO: Si hay idioma destino, iniciar traducciones automáticamente
        translation_job_id = None
        if target_language and ollama_translator.is_available():
            translation_job_id = str(uuid.uuid4())
            
            # Crear trabajo de traducción en background
            jobs[translation_job_id] = {
                "status": JobStatus.PENDING,
                "progress": 0,
                "message": "Iniciando traducciones automáticas...",
                "type": "auto_translation",
                "tmx_id": tmx_id,
                "language": language,
                "target_language": target_language
            }
            
            # Iniciar traducciones en background
            import asyncio
            from threading import Thread
            
            def run_auto_translations():
                asyncio.run(process_auto_translations_unified(translation_job_id, tmx_id, language, target_language))
            
            thread = Thread(target=run_auto_translations)
            thread.daemon = True
            thread.start()
            
            msg += f" - Traducciones iniciadas automáticamente (Job ID: {translation_job_id})"
        
        return {
            "success": True,
            "language": language,
            "target_language": target_language,
            "total_terms": len(terms),
            "extraction_mode": "termsuite" if use_termsuite else "direct",
            "translation_job_id": translation_job_id,
            "message": msg
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


@app.get("/api/tmx/{tmx_id}/export-ready")
async def check_tmx_export_ready(tmx_id: str):
    """
    Verificar si un TMX está listo para descarga rápida
    Considera datos pre-procesados, número de términos y columnas de dominio
    """
    # Verificar datos pre-procesados
    processed_data_path = file_handler.get_path("tmx", f"{tmx_id}_processed.json")
    has_processed_data = processed_data_path.exists()
    
    # Verificar términos básicos
    tmx_terms_path = file_handler.get_path("tmx", f"{tmx_id}_terms.json")
    if not tmx_terms_path.exists():
        raise HTTPException(status_code=404, detail="TMX no encontrado")
    
    with open(tmx_terms_path, 'r', encoding='utf-8') as f:
        tmx_data = json.load(f)
    
    # Contar términos
    if isinstance(tmx_data, dict):
        terms_list = tmx_data.get('terms', [])
        domain_description = tmx_data.get('domain_description')
    else:
        terms_list = tmx_data
        domain_description = None
    
    total_terms = len(terms_list)
    
    # NUEVO: Verificar si los datos pre-procesados incluyen columnas de dominio
    has_domain_columns = False
    if has_processed_data:
        try:
            with open(processed_data_path, 'r', encoding='utf-8') as f:
                processed_data = json.load(f)
            
            if processed_data.get('data') and len(processed_data['data']) > 0:
                has_domain_columns = 'Relevancia Ámbito' in processed_data['data'][0]
        except Exception:
            has_domain_columns = False
    
    # Determinar si necesita procesamiento de dominio
    needs_domain_processing = (
        domain_description and 
        domain_description.strip() and 
        ollama_translator.is_available() and
        not has_domain_columns  # NUEVO: Solo si no tiene las columnas ya
    )
    
    # Determinar si está listo para descarga rápida
    ready_for_fast_download = (
        has_processed_data and  # Tiene datos pre-procesados
        total_terms <= 100 and  # No demasiados términos
        not needs_domain_processing  # NUEVO: Solo si no necesita procesamiento adicional
    )
    
    return {
        "tmx_id": tmx_id,
        "ready_for_fast_download": ready_for_fast_download,
        "has_processed_data": has_processed_data,
        "has_domain_columns": has_domain_columns,
        "total_terms": total_terms,
        "needs_domain_processing": needs_domain_processing,
        "domain_description": domain_description,
        "recommendation": (
            "fast" if ready_for_fast_download else 
            "async" if total_terms > 100 or needs_domain_processing else 
            "basic"
        )
    }


@app.get("/api/tmx/{tmx_id}/translation-status")
async def get_translation_status(tmx_id: str):
    """Verificar si las traducciones automáticas están listas para un TMX"""
    processed_data_path = file_handler.get_path("tmx", f"{tmx_id}_processed.json")
    
    if processed_data_path.exists():
        with open(processed_data_path, 'r', encoding='utf-8') as f:
            processed_data = json.load(f)
        
        return {
            "tmx_id": tmx_id,
            "translations_ready": True,
            "total_terms": processed_data.get('total_terms', 0),
            "ollama_translations": processed_data.get('ollama_translations', 0),
            "processed_at": processed_data.get('processed_at'),
            "source_lang": processed_data.get('source_lang'),
            "target_lang": processed_data.get('target_lang')
        }
    else:
        # Buscar trabajos de traducción en progreso
        translation_jobs = [
            job for job_id, job in jobs.items() 
            if job.get('type') == 'auto_translation' and job.get('tmx_id') == tmx_id
        ]
        
        if translation_jobs:
            latest_job = max(translation_jobs, key=lambda x: jobs.get(x, {}).get('progress', 0))
            return {
                "tmx_id": tmx_id,
                "translations_ready": False,
                "in_progress": True,
                "progress": latest_job.get('progress', 0),
                "message": latest_job.get('message', ''),
                "status": latest_job.get('status')
            }
        else:
            return {
                "tmx_id": tmx_id,
                "translations_ready": False,
                "in_progress": False,
                "message": "No se han iniciado traducciones automáticas"
            }


@app.get("/api/export/tmx-excel-instant/{tmx_id}")
async def export_tmx_instant(tmx_id: str):
    """
    Descarga instantánea de Excel pre-generado con procesamiento unificado
    """
    processed_data_path = file_handler.get_path("tmx", f"{tmx_id}_processed.json")
    
    if processed_data_path.exists():
        with open(processed_data_path, 'r', encoding='utf-8') as f:
            processed_data = json.load(f)
        
        # Verificar que sea procesamiento optimizado (unificado o tradicional mejorado)
        processing_type = processed_data.get('processing_type')
        if processing_type in ['unified', 'traditional']:
            # Generar Excel desde datos pre-procesados
            excel_data = processed_data['data']
            
            # Crear Excel optimizado
            import pandas as pd
            df = pd.DataFrame(excel_data)
            
            excel_filename = f"tmx_unified_{tmx_id}.xlsx"
            excel_path = file_handler.get_path("outputs", excel_filename)
            
            # Generar Excel con formato optimizado
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Términos TMX', index=False)
                
                # Aplicar formato
                workbook = writer.book
                worksheet = writer.sheets['Términos TMX']
                
                from openpyxl.styles import Font, PatternFill
                header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                header_font = Font(color="FFFFFF", bold=True, size=11)
                
                for col_idx in range(1, len(df.columns) + 1):
                    cell = worksheet.cell(row=1, column=col_idx)
                    cell.fill = header_fill
                    cell.font = header_font
            
            return FileResponse(
                path=excel_path,
                filename=f"terminos_unificado_{processed_data['source_lang']}_{processed_data['target_lang']}.xlsx",
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    # Fallback al método tradicional si no hay datos unificados
    raise HTTPException(
        status_code=404, 
        detail="Procesamiento unificado no disponible. Use descarga asíncrona."
    )


@app.get("/api/tmx/{tmx_id}/unified-status")
async def check_unified_status(tmx_id: str):
    """
    Verificar estado del procesamiento unificado
    """
    processed_data_path = file_handler.get_path("tmx", f"{tmx_id}_processed.json")
    
    if processed_data_path.exists():
        with open(processed_data_path, 'r', encoding='utf-8') as f:
            processed_data = json.load(f)
        
        processing_type = processed_data.get('processing_type')
        if processing_type in ['unified', 'traditional']:
            return {
                "tmx_id": tmx_id,
                "unified_ready": True,
                "processing_type": processing_type,
                "total_terms": processed_data.get('total_terms', 0),
                "unified_processed": processed_data.get('unified_processed', 0),
                "traditional_translated": processed_data.get('traditional_translated', 0),
                "processed_at": processed_data.get('processed_at'),
                "domain_description": processed_data.get('domain_description'),
                "instant_download_available": True
            }
    
    # Verificar si hay trabajo en progreso
    unified_jobs = [
        job_id for job_id, job in jobs.items() 
        if job.get('type') == 'auto_translation' and job.get('tmx_id') == tmx_id
    ]
    
    if unified_jobs:
        latest_job_id = max(unified_jobs, key=lambda x: jobs.get(x, {}).get('progress', 0))
        latest_job = jobs[latest_job_id]
        return {
            "tmx_id": tmx_id,
            "unified_ready": False,
            "in_progress": True,
            "progress": latest_job.get('progress', 0),
            "message": latest_job.get('message', ''),
            "status": latest_job.get('status')
        }
    
    return {
        "tmx_id": tmx_id,
        "unified_ready": False,
        "in_progress": False,
        "message": "Procesamiento unificado no iniciado"
    }


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
    Exportar términos de TMX a Excel usando datos pre-procesados (FLUJO MEJORADO)
    
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
    # Verificar si existen datos pre-procesados (con traducciones)
    processed_data_path = file_handler.get_path("tmx", f"{tmx_id}_processed.json")
    
    if processed_data_path.exists() and include_translation:
        # FLUJO RÁPIDO: Usar datos pre-procesados con traducciones
        with open(processed_data_path, 'r', encoding='utf-8') as f:
            processed_data = json.load(f)
        
        terms_for_excel = processed_data['data'].copy()
        language = processed_data['source_lang']
        
        # NUEVO: Verificar si los datos pre-procesados incluyen columnas de dominio
        # Si no las tienen, añadirlas SOLO si realmente se necesitan
        if (terms_for_excel and 
            'Relevancia Ámbito' not in terms_for_excel[0] and
            domain_description and 
            domain_description.strip() and 
            ollama_translator.is_available()):
            
            # Cargar datos originales para obtener domain_description
            tmx_terms_path = file_handler.get_path("tmx", f"{tmx_id}_terms.json")
            if tmx_terms_path.exists():
                with open(tmx_terms_path, 'r', encoding='utf-8') as f:
                    tmx_data = json.load(f)
                
                domain_description = tmx_data.get('domain_description') if isinstance(tmx_data, dict) else None
                
                if domain_description and domain_description.strip() and ollama_translator.is_available():
                    # Extraer términos para clasificar
                    terms_to_classify = [item['Término'] for item in terms_for_excel]
                    
                    if terms_to_classify:
                        # Clasificar términos
                        domain_classifications = await ollama_translator.classify_terms_domain_batch(
                            terms_to_classify, 
                            domain_description, 
                            language,
                            max_concurrent=3
                        )
                        
                        # Añadir columnas de dominio
                        for item in terms_for_excel:
                            term = item['Término']
                            if term in domain_classifications:
                                classification = domain_classifications[term]
                                item['Relevancia Ámbito'] = classification['relevance']
                                item['Confianza Ámbito'] = f"{classification['confidence']}%"
                                item['Razón Ámbito'] = classification.get('reason', '')[:100]
                            else:
                                item['Relevancia Ámbito'] = 'Error'
                                item['Confianza Ámbito'] = '0%'
                                item['Razón Ámbito'] = 'Error en clasificación'
                    else:
                        # Sin términos para clasificar
                        for item in terms_for_excel:
                            item['Relevancia Ámbito'] = 'No disponible'
                            item['Confianza Ámbito'] = 'N/A'
                            item['Razón Ámbito'] = 'No hay términos para clasificar'
                else:
                    # Sin dominio especificado o Ollama no disponible
                    for item in terms_for_excel:
                        item['Relevancia Ámbito'] = 'No especificado'
                        item['Confianza Ámbito'] = 'N/A'
                        item['Razón Ámbito'] = 'No se especificó ámbito'
        elif terms_for_excel and 'Relevancia Ámbito' not in terms_for_excel[0]:
            # Añadir columnas de dominio como 'No especificado' si no se solicitan
            for item in terms_for_excel:
                item['Relevancia Ámbito'] = 'No especificado'
                item['Confianza Ámbito'] = 'N/A'
                item['Razón Ámbito'] = 'No se especificó ámbito'
        
    else:
        # FLUJO TRADICIONAL: Cargar términos básicos sin traducciones
        tmx_terms_path = file_handler.get_path("tmx", f"{tmx_id}_terms.json")
        if not tmx_terms_path.exists():
            raise HTTPException(status_code=404, detail="TMX no encontrado")
        
        with open(tmx_terms_path, 'r', encoding='utf-8') as f:
            tmx_data = json.load(f)
        
        # Extraer términos (compatible con formato nuevo y antiguo)
        if isinstance(tmx_data, dict):
            terms_list = tmx_data.get('terms', [])
            frequencies = tmx_data.get('frequencies', {})
            language = tmx_data.get('language', 'unknown')
        else:
            terms_list = tmx_data
            frequencies = {}
            language = 'unknown'
        
        # Crear estructura básica para Excel
        terms_for_excel = []
        for idx, term in enumerate(terms_list, 1):
            freq = frequencies.get(term, 1)
            word_count = len(term.split())
            
            terms_for_excel.append({
                'Número': idx,
                'Término': term,
                'Frecuencia': freq,
                'Longitud': len(term),
                'Palabras': word_count,
                'Idioma': language,
                'Traducción': '',
                'Tipo Match': 'Sin procesar',
                'Variantes': 0,
                'Ollama': 'No procesado',
                'Contexto Ollama': 'No procesado'
            })
    
    # NUEVO: Añadir clasificación de dominio si hay descripción de ámbito
    # PERO SOLO si no hay muchos términos (para evitar bloquear la descarga)
    # Cargar datos originales para obtener domain_description
    tmx_terms_path = file_handler.get_path("tmx", f"{tmx_id}_terms.json")
    if tmx_terms_path.exists():
        with open(tmx_terms_path, 'r', encoding='utf-8') as f:
            tmx_data = json.load(f)
        domain_description = tmx_data.get('domain_description') if isinstance(tmx_data, dict) else None
    else:
        domain_description = None
    
    if (domain_description and domain_description.strip() and ollama_translator.is_available() 
        and len(terms_for_excel) <= 100):  # LÍMITE: Solo procesar si hay 100 términos o menos
        
        # Extraer solo los términos para clasificar
        terms_to_classify = [item['Término'] for item in terms_for_excel]
        
        if terms_to_classify:
            # Clasificar términos usando el método asíncrono
            domain_classifications = await ollama_translator.classify_terms_domain_batch(
                terms_to_classify, 
                domain_description, 
                language,
                max_concurrent=3  # Limitar concurrencia
            )
            
            # Actualizar términos con clasificaciones de dominio
            for item in terms_for_excel:
                term = item['Término']
                if term in domain_classifications:
                    classification = domain_classifications[term]
                    item['Relevancia Ámbito'] = classification['relevance']
                    item['Confianza Ámbito'] = f"{classification['confidence']}%"
                    item['Razón Ámbito'] = classification.get('reason', '')[:100]  # Limitar longitud
                else:
                    item['Relevancia Ámbito'] = 'Error'
                    item['Confianza Ámbito'] = '0%'
                    item['Razón Ámbito'] = 'Error en clasificación'
        else:
            # Añadir columnas de dominio como 'No disponible' si no hay términos
            for item in terms_for_excel:
                item['Relevancia Ámbito'] = 'No disponible'
                item['Confianza Ámbito'] = 'N/A'
                item['Razón Ámbito'] = 'No hay términos para clasificar'
    else:
        # Añadir columnas de dominio como 'No especificado' o 'Usar descarga asíncrona'
        for item in terms_for_excel:
            if domain_description and domain_description.strip():
                if len(terms_for_excel) > 100:
                    item['Relevancia Ámbito'] = 'Usar descarga asíncrona'
                    item['Confianza Ámbito'] = 'N/A'
                    item['Razón Ámbito'] = 'Demasiados términos para descarga rápida'
                elif not ollama_translator.is_available():
                    item['Relevancia Ámbito'] = 'No disponible'
                    item['Confianza Ámbito'] = 'N/A'
                    item['Razón Ámbito'] = 'Servicio Ollama no disponible'
                else:
                    item['Relevancia Ámbito'] = 'Error'
                    item['Confianza Ámbito'] = 'N/A'
                    item['Razón Ámbito'] = 'Error en configuración'
            else:
                item['Relevancia Ámbito'] = 'No especificado'
                item['Confianza Ámbito'] = 'N/A'
                item['Razón Ámbito'] = 'No se especificó ámbito'
    
    # Aplicar filtros a los datos (pre-procesados o básicos)
    filtered_terms = []
    for item in terms_for_excel:
        term = item['Término']
        freq = item['Frecuencia']
        word_count = item['Palabras']
        
        # Aplicar filtros
        if min_frequency and freq < min_frequency:
            continue
        if min_words and word_count < min_words:
            continue
        if max_words and word_count > max_words:
            continue
        if exclude_numbers and any(char.isdigit() for char in term):
            continue
        if contains and contains.lower() not in term.lower():
            continue
        
        filtered_terms.append(item)
    
    # Ordenar según parámetros
    if sort_by == "frequency":
        filtered_terms.sort(key=lambda x: x['Frecuencia'], reverse=(sort_order == "desc"))
    elif sort_by == "alphabetical":
        filtered_terms.sort(key=lambda x: x['Término'].lower(), reverse=(sort_order == "desc"))
    elif sort_by == "length":
        filtered_terms.sort(key=lambda x: x['Longitud'], reverse=(sort_order == "desc"))
    elif sort_by == "words":
        filtered_terms.sort(key=lambda x: x['Palabras'], reverse=(sort_order == "desc"))
    
    # Aplicar top_n después de ordenar
    if top_n:
        filtered_terms = filtered_terms[:top_n]
    
    # Renumerar después de filtrar y ordenar
    for idx, item in enumerate(filtered_terms, 1):
        item['Número'] = idx
    
    # Si no hay términos después de filtrar
    if not filtered_terms:
        raise HTTPException(
            status_code=404, 
            detail="No se encontraron términos con los filtros aplicados"
        )
    
    terms_for_excel = filtered_terms
    
    # Las traducciones ya están incluidas si se usaron datos pre-procesados
    # No se necesita procesamiento adicional
    
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
    
    # Formato Excel (por defecto) - OPTIMIZADO
    excel_filename = f"tmx_{tmx_id}.xlsx"
    excel_path = file_handler.get_path("outputs", excel_filename)
    
    # Reordenar columnas para mejor visualización
    preferred_order = ['Número', 'Término', 'Frecuencia', 'Longitud', 'Palabras', 'Idioma', 'Traducción', 'Tipo Match', 'Variantes', 'Ollama', 'Contexto Ollama', 'Relevancia Ámbito', 'Confianza Ámbito', 'Razón Ámbito']
    existing_cols = [col for col in preferred_order if col in df.columns]
    other_cols = [col for col in df.columns if col not in existing_cols]
    df = df[existing_cols + other_cols]
    
    # Usar pandas para escribir Excel más rápido
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Términos TMX', index=False)
        
        # Obtener workbook y worksheet para aplicar formato
        workbook = writer.book
        worksheet = writer.sheets['Términos TMX']
        
        # Aplicar formato solo a encabezados (más rápido)
        from openpyxl.styles import Font, PatternFill, Alignment
        
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True, size=11)
        
        # Formatear solo la primera fila (encabezados)
        for col_idx in range(1, len(df.columns) + 1):
            cell = worksheet.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Ajustar anchos de columna
        column_widths = {
            'Número': 10,
            'Término': 50,
            'Frecuencia': 12,
            'Longitud': 12,
            'Palabras': 12,
            'Idioma': 12,
            'Traducción': 80,  # Más ancho para traducciones de Ollama
            'Tipo Match': 20,
            'Variantes': 12,
            'Ollama': 15,
            'Contexto Ollama': 60,  # Ancho para contexto TMX
            'Relevancia Ámbito': 18,
            'Confianza Ámbito': 15,
            'Razón Ámbito': 60
        }
        
        for idx, col in enumerate(df.columns, 1):
            col_letter = chr(64 + idx) if idx <= 26 else chr(64 + idx // 26) + chr(64 + idx % 26)
            width = column_widths.get(col, 15)
            worksheet.column_dimensions[col_letter].width = width
        
        # Congelar primera fila
        worksheet.freeze_panes = 'A2'
    
    return FileResponse(
        path=excel_path,
        filename=f"terminos_tmx_{language}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.post("/api/export/tmx-excel-async/{tmx_id}")
async def export_tmx_to_excel_async(
    tmx_id: str,
    background_tasks: BackgroundTasks,
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
    include_translation: bool = False,
    use_ollama: bool = True
):
    """
    Exportar términos de TMX a Excel de forma asíncrona (para archivos grandes)
    """
    export_job_id = str(uuid.uuid4())
    
    # Verificar que existe el TMX
    tmx_terms_path = file_handler.get_path("tmx", f"{tmx_id}_terms.json")
    if not tmx_terms_path.exists():
        raise HTTPException(status_code=404, detail="TMX no encontrado")
    
    # Crear trabajo de exportación
    jobs[export_job_id] = {
        "status": JobStatus.PENDING,
        "progress": 0,
        "message": "Preparando exportación...",
        "type": "export",
        "tmx_id": tmx_id
    }
    
    # Ejecutar en background
    background_tasks.add_task(
        process_tmx_export,
        export_job_id,
        tmx_id,
        {
            "min_frequency": min_frequency,
            "top_n": top_n,
            "min_words": min_words,
            "max_words": max_words,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "format": format,
            "columns": columns,
            "exclude_numbers": exclude_numbers,
            "contains": contains,
            "include_translation": include_translation,
            "use_ollama": use_ollama
        }
    )
    
    return {
        "export_job_id": export_job_id,
        "status": "started",
        "message": "Exportación iniciada en segundo plano"
    }


def process_tmx_export(export_job_id: str, tmx_id: str, params: dict):
    """Procesar exportación TMX en background con traducción Ollama"""
    try:
        jobs[export_job_id]["status"] = JobStatus.PROCESSING
        jobs[export_job_id]["progress"] = 5
        jobs[export_job_id]["message"] = "Cargando términos..."
        
        # Cargar términos del TMX
        tmx_terms_path = file_handler.get_path("tmx", f"{tmx_id}_terms.json")
        with open(tmx_terms_path, 'r', encoding='utf-8') as f:
            tmx_data = json.load(f)
        
        # Extraer términos (compatible con formato nuevo y antiguo)
        if isinstance(tmx_data, dict):
            terms_list = tmx_data.get('terms', [])
            frequencies = tmx_data.get('frequencies', {})
            language = tmx_data.get('language', 'unknown')
            target_language = tmx_data.get('target_language')
        else:
            terms_list = tmx_data
            frequencies = {}
            language = 'unknown'
            target_language = None
        
        jobs[export_job_id]["progress"] = 15
        jobs[export_job_id]["message"] = "Aplicando filtros..."
        
        # Crear estructura para Excel (misma lógica que endpoint síncrono)
        terms_for_excel = []
        for term in terms_list:
            freq = frequencies.get(term, 1)
            word_count = len(term.split())
            
            # Aplicar filtros
            if params.get('min_frequency') and freq < params['min_frequency']:
                continue
            if params.get('min_words') and word_count < params['min_words']:
                continue
            if params.get('max_words') and word_count > params['max_words']:
                continue
            if params.get('exclude_numbers') and any(char.isdigit() for char in term):
                continue
            if params.get('contains') and params['contains'].lower() not in term.lower():
                continue
            
            terms_for_excel.append({
                'Término': term,
                'Frecuencia': freq,
                'Longitud': len(term),
                'Palabras': word_count,
                'Idioma': language
            })
        
        # Ordenar según parámetros
        sort_by = params.get('sort_by', 'frequency')
        sort_order = params.get('sort_order', 'desc')
        
        if sort_by == "frequency":
            terms_for_excel.sort(key=lambda x: x['Frecuencia'], reverse=(sort_order == "desc"))
        elif sort_by == "alphabetical":
            terms_for_excel.sort(key=lambda x: x['Término'].lower(), reverse=(sort_order == "desc"))
        elif sort_by == "length":
            terms_for_excel.sort(key=lambda x: x['Longitud'], reverse=(sort_order == "desc"))
        elif sort_by == "words":
            terms_for_excel.sort(key=lambda x: x['Palabras'], reverse=(sort_order == "desc"))
        
        # Aplicar top_n después de ordenar
        if params.get('top_n'):
            terms_for_excel = terms_for_excel[:params['top_n']]
        
        # Agregar número después de filtrar y ordenar
        for idx, item in enumerate(terms_for_excel, 1):
            item['Número'] = idx
        
        jobs[export_job_id]["progress"] = 25
        
        # Incluir traducción si se solicita
        if params.get('include_translation') and target_language:
            jobs[export_job_id]["message"] = "Buscando traducciones en TMX..."
            
            # Verificar si ya existe un archivo de traducciones en caché
            translations_cache_path = file_handler.get_path("tmx", f"{tmx_id}_translations.json")
            
            if translations_cache_path.exists():
                # Usar caché
                with open(translations_cache_path, 'r', encoding='utf-8') as f:
                    translations_data = json.load(f)
            else:
                # Buscar el archivo TMX original y procesar traducciones
                tmx_dir = file_handler.uploads_dir / 'tmx'
                tmx_file_path = None
                
                if tmx_dir.exists():
                    for file in tmx_dir.glob(f"{tmx_id}*"):
                        if file.suffix == '.tmx':
                            tmx_file_path = file
                            break
                
                if tmx_file_path and tmx_file_path.exists():
                    try:
                        translations = tmx_parser.parse_with_translations(
                            str(tmx_file_path), 
                            source_lang=language,
                            target_lang=target_language
                        )
                        
                        # Procesar traducciones y crear índices optimizados
                        from collections import defaultdict
                        trans_dict_exact = defaultdict(set)
                        trans_dict_partial = defaultdict(set)
                        
                        for trans in translations:
                            source = trans.get('source', '').strip()
                            target = trans.get('target', '').strip()
                            if source and target:
                                source_lower = source.lower()
                                # Índice exacto
                                trans_dict_exact[source_lower].add(target)
                                # Índice parcial (palabras individuales)
                                for word in source_lower.split():
                                    if len(word) > 2:
                                        trans_dict_partial[word].add(target)
                        
                        # Convertir sets a listas para JSON
                        translations_data = {
                            'exact': {k: list(v) for k, v in trans_dict_exact.items()},
                            'partial': {k: list(v) for k, v in trans_dict_partial.items()}
                        }
                        
                        # Guardar en caché
                        with open(translations_cache_path, 'w', encoding='utf-8') as f:
                            json.dump(translations_data, f, ensure_ascii=False, indent=2)
                    except Exception as e:
                        translations_data = {'exact': {}, 'partial': {}}
                else:
                    translations_data = {'exact': {}, 'partial': {}}
            
            jobs[export_job_id]["progress"] = 40
            
            if translations_data and (translations_data.get('exact') or translations_data.get('partial')):
                trans_dict_exact = translations_data.get('exact', {})
                trans_dict_partial = translations_data.get('partial', {})
                
                # Agregar traducción a cada término
                for item in terms_for_excel:
                    term = item['Término']
                    term_lower = term.lower()
                    
                    # 1. Buscar coincidencia exacta
                    if term_lower in trans_dict_exact:
                        translations_list = trans_dict_exact[term_lower]
                        item['Traducción'] = ' | '.join(translations_list)
                        item['Tipo Match'] = 'Exacto'
                        item['Variantes'] = len(translations_list)
                    else:
                        # 2. Buscar coincidencia parcial
                        partial_translations = set()
                        words = term_lower.split()
                        
                        for word in words:
                            if len(word) > 2 and word in trans_dict_partial:
                                partial_translations.update(trans_dict_partial[word])
                        
                        if partial_translations:
                            item['Traducción'] = ' | '.join(list(partial_translations)[:3])
                            item['Tipo Match'] = 'Parcial'
                            item['Variantes'] = len(partial_translations)
                        else:
                            item['Traducción'] = ''
                            item['Tipo Match'] = 'No encontrado'
                            item['Variantes'] = 0
            
            jobs[export_job_id]["progress"] = 50
            
            # NUEVO: Traducir términos con Match Parcial usando Ollama
            if params.get('use_ollama', True) and ollama_translator.is_available() and target_language:
                jobs[export_job_id]["message"] = "Traduciendo términos con Ollama..."
                
                # Filtrar términos que necesitan traducción con Ollama
                terms_to_translate = [
                    item for item in terms_for_excel 
                    if item.get('Tipo Match') in ['Parcial', 'No encontrado']
                ]
                
                if terms_to_translate:
                    jobs[export_job_id]["message"] = f"Traduciendo {len(terms_to_translate)} términos con Ollama..."
                    add_ollama_log("BATCH_START", None, "INICIANDO", f"Iniciando traducción de {len(terms_to_translate)} términos")
                    
                    # Preparar términos con traducción parcial TMX como contexto
                    terms_with_context = []
                    for item in terms_to_translate:
                        term_data = {
                            'Término': item['Término'],
                            'Frecuencia': item.get('Frecuencia', 1),
                            'Palabras': item.get('Palabras', 1),
                            'Tipo Match': item.get('Tipo Match', 'No encontrado')
                        }
                        
                        # Incluir traducción parcial del TMX como contexto para Ollama
                        tmx_translation = item.get('Traducción', '').strip()
                        if tmx_translation:
                            term_data['TMX_Context'] = tmx_translation
                        
                        terms_with_context.append(term_data)
                    
                    # Traducir en lotes usando el método asíncrono
                    import asyncio
                    ollama_translations = asyncio.run(ollama_translator.translate_terms_batch(
                        terms_with_context, 
                        language, 
                        target_language,
                        max_concurrent=2  # Limitar concurrencia para no sobrecargar Ollama
                    ))
                    
                    add_ollama_log("BATCH_COMPLETE", None, "COMPLETADO", f"Traducidos {len(ollama_translations)}/{len(terms_to_translate)} términos")
                    
                    # Actualizar términos con traducciones de Ollama
                    for item in terms_for_excel:
                        if item.get('Tipo Match') in ['Parcial', 'No encontrado']:
                            term = item['Término']
                            if term in ollama_translations:
                                # Obtener resultado completo de Ollama
                                ollama_result = ollama_translations[term]
                                ollama_translation = ollama_result['translation']
                                
                                # REEMPLAZAR completamente la traducción con Ollama (no combinar)
                                item['Traducción'] = ollama_translation
                                
                                # Actualizar tipo de match
                                if item.get('Tipo Match') == 'Parcial':
                                    item['Tipo Match'] = 'Parcial + Ollama'
                                else:
                                    item['Tipo Match'] = 'Ollama'
                                
                                item['Ollama'] = 'Sí'
                                
                                # Contexto Ollama: mostrar la traducción parcial TMX que se usó como contexto
                                tmx_translation = ""
                                for term_ctx in terms_with_context:
                                    if term_ctx['Término'] == term and term_ctx.get('TMX_Context'):
                                        tmx_translation = term_ctx['TMX_Context']
                                        break
                                
                                item['Contexto Ollama'] = tmx_translation if tmx_translation else "Sin contexto TMX"
                            else:
                                item['Ollama'] = 'Error'
                                item['Contexto Ollama'] = 'Error en traducción'
                        else:
                            item['Ollama'] = 'No necesario'
                            item['Contexto Ollama'] = 'No aplicable'
                    
                    jobs[export_job_id]["progress"] = 80
                    jobs[export_job_id]["message"] = f"Traducciones Ollama completadas: {len(ollama_translations)}/{len(terms_to_translate)}"
                else:
                    jobs[export_job_id]["message"] = "No hay términos para traducir con Ollama"
            else:
                if not ollama_translator.is_available():
                    jobs[export_job_id]["message"] = "Ollama no disponible, continuando sin traducciones adicionales..."
                # Agregar columnas Ollama como 'No disponible'
                for item in terms_for_excel:
                    item['Ollama'] = 'No disponible'
                    item['Contexto Ollama'] = 'Servicio no disponible'
        
        # NUEVO: Clasificación de dominio si se especifica
        domain_description = tmx_data.get('domain_description')
        if domain_description and domain_description.strip() and ollama_translator.is_available():
            jobs[export_job_id]["progress"] = 82
            jobs[export_job_id]["message"] = "Clasificando términos por relevancia al ámbito..."
            
            # Extraer solo los términos para clasificar
            terms_to_classify = [item['Término'] for item in terms_for_excel]
            
            if terms_to_classify:
                add_ollama_log("DOMAIN_BATCH_START", None, "INICIANDO", f"Iniciando clasificación de {len(terms_to_classify)} términos para ámbito: {domain_description[:50]}...")
                
                # Clasificar términos usando el método asíncrono
                import asyncio
                domain_classifications = asyncio.run(ollama_translator.classify_terms_domain_batch(
                    terms_to_classify, 
                    domain_description, 
                    language,
                    max_concurrent=3  # Limitar concurrencia
                ))
                
                add_ollama_log("DOMAIN_BATCH_COMPLETE", None, "COMPLETADO", f"Clasificados {len(domain_classifications)}/{len(terms_to_classify)} términos")
                
                # Actualizar términos con clasificaciones de dominio
                for item in terms_for_excel:
                    term = item['Término']
                    if term in domain_classifications:
                        classification = domain_classifications[term]
                        item['Relevancia Ámbito'] = classification['relevance']
                        item['Confianza Ámbito'] = f"{classification['confidence']}%"
                        item['Razón Ámbito'] = classification.get('reason', '')[:100]  # Limitar longitud
                    else:
                        item['Relevancia Ámbito'] = 'Error'
                        item['Confianza Ámbito'] = '0%'
                        item['Razón Ámbito'] = 'Error en clasificación'
                
                jobs[export_job_id]["message"] = f"Clasificación de ámbito completada: {len(domain_classifications)}/{len(terms_to_classify)}"
            else:
                jobs[export_job_id]["message"] = "No hay términos para clasificar"
        else:
            # Añadir columnas de dominio como 'No disponible' si no se especifica dominio
            for item in terms_for_excel:
                if domain_description and domain_description.strip():
                    item['Relevancia Ámbito'] = 'No disponible'
                    item['Confianza Ámbito'] = 'N/A'
                    item['Razón Ámbito'] = 'Servicio Ollama no disponible'
                else:
                    item['Relevancia Ámbito'] = 'No especificado'
                    item['Confianza Ámbito'] = 'N/A'
                    item['Razón Ámbito'] = 'No se especificó ámbito'
        
        jobs[export_job_id]["progress"] = 85
        jobs[export_job_id]["message"] = "Generando Excel..."
        
        # Generar archivo Excel
        import pandas as pd
        
        # Reordenar columnas para mejor visualización
        preferred_order = ['Número', 'Término', 'Frecuencia', 'Longitud', 'Palabras', 'Idioma', 'Traducción', 'Tipo Match', 'Variantes', 'Ollama', 'Contexto Ollama', 'Relevancia Ámbito', 'Confianza Ámbito', 'Razón Ámbito']
        existing_cols = [col for col in preferred_order if col in (terms_for_excel[0].keys() if terms_for_excel else [])]
        other_cols = [col for col in (terms_for_excel[0].keys() if terms_for_excel else []) if col not in existing_cols]
        
        if terms_for_excel:
            # Reordenar datos
            reordered_data = []
            for item in terms_for_excel:
                reordered_item = {}
                for col in existing_cols + other_cols:
                    reordered_item[col] = item.get(col, '')
                reordered_data.append(reordered_item)
            
            df = pd.DataFrame(reordered_data)
        else:
            df = pd.DataFrame()
        
        # Crear archivo Excel
        excel_filename = f"tmx_{tmx_id}.xlsx"
        excel_path = file_handler.get_path("outputs", excel_filename)
        
        if not df.empty:
            # Usar pandas para escribir Excel más rápido
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Términos TMX', index=False)
                
                # Obtener workbook y worksheet para aplicar formato
                workbook = writer.book
                worksheet = writer.sheets['Términos TMX']
                
                # Aplicar formato solo a encabezados
                from openpyxl.styles import Font, PatternFill, Alignment
                
                header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                header_font = Font(color="FFFFFF", bold=True, size=11)
                
                # Formatear solo la primera fila (encabezados)
                for col_idx in range(1, len(df.columns) + 1):
                    cell = worksheet.cell(row=1, column=col_idx)
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                
                # Ajustar anchos de columna
                column_widths = {
                    'Número': 10,
                    'Término': 50,
                    'Frecuencia': 12,
                    'Longitud': 12,
                    'Palabras': 12,
                    'Idioma': 12,
                    'Traducción': 80,  # Más ancho para múltiples traducciones
                    'Tipo Match': 20,
                    'Variantes': 12,
                    'Ollama': 15,
                    'Contexto Ollama': 40,
                    'Relevancia Ámbito': 18,
                    'Confianza Ámbito': 15,
                    'Razón Ámbito': 60
                }
                
                for idx, col in enumerate(df.columns, 1):
                    col_letter = chr(64 + idx) if idx <= 26 else chr(64 + idx // 26) + chr(64 + idx % 26)
                    width = column_widths.get(col, 15)
                    worksheet.column_dimensions[col_letter].width = width
                
                # Congelar primera fila
                worksheet.freeze_panes = 'A2'
        else:
            # Crear Excel vacío si no hay datos
            from openpyxl import Workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "Términos TMX"
            ws['A1'] = "No se encontraron términos con los filtros aplicados"
            wb.save(excel_path)
        
        jobs[export_job_id]["status"] = JobStatus.COMPLETED
        jobs[export_job_id]["progress"] = 100
        jobs[export_job_id]["message"] = "Exportación completada con traducciones Ollama"
        jobs[export_job_id]["result_file"] = excel_filename
        
    except Exception as e:
        jobs[export_job_id]["status"] = JobStatus.FAILED
        jobs[export_job_id]["error"] = str(e)
        jobs[export_job_id]["message"] = f"Error: {str(e)}"


@app.get("/api/download/export/{export_job_id}")
async def download_export_result(export_job_id: str):
    """Descargar resultado de exportación asíncrona"""
    if export_job_id not in jobs:
        raise HTTPException(status_code=404, detail="Trabajo de exportación no encontrado")
    
    job = jobs[export_job_id]
    if job["status"] != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400, 
            detail=f"La exportación está en estado: {job['status']}"
        )
    
    result_file = job.get("result_file")
    if not result_file:
        raise HTTPException(status_code=404, detail="Archivo de resultado no encontrado")
    
    file_path = file_handler.get_path("outputs", result_file)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado en disco")
    
    # Determinar tipo de archivo y nombre
    tmx_id = job.get("tmx_id", "unknown")
    if result_file.endswith('.xlsx'):
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"terminos_tmx_{tmx_id}.xlsx"
    elif result_file.endswith('.csv'):
        media_type = "text/csv"
        filename = f"terminos_tmx_{tmx_id}.csv"
    else:
        media_type = "application/json"
        filename = f"terminos_tmx_{tmx_id}.json"
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )


async def process_auto_translations_unified(job_id: str, tmx_id: str, source_lang: str, target_lang: str):
    """
    VERSIÓN UNIFICADA: Procesar traducciones + clasificación en background
    """
    try:
        jobs[job_id]["status"] = JobStatus.PROCESSING
        jobs[job_id]["progress"] = 10
        jobs[job_id]["message"] = "Cargando términos para procesamiento unificado..."
        
        # Cargar términos del TMX
        terms_path = file_handler.get_path("tmx", f"{tmx_id}_terms.json")
        with open(terms_path, 'r', encoding='utf-8') as f:
            terms_data = json.load(f)
        
        terms_list = terms_data.get('terms', [])
        frequencies = terms_data.get('frequencies', {})
        domain_description = terms_data.get('domain_description', '')
        
        jobs[job_id]["progress"] = 20
        jobs[job_id]["message"] = "Obteniendo traducciones TMX..."
        
        # Obtener traducciones TMX existentes (mismo código que antes)
        tmx_dir = file_handler.uploads_dir / 'tmx'
        tmx_file_path = None
        
        if tmx_dir.exists():
            for file in tmx_dir.glob(f"{tmx_id}*"):
                if file.suffix == '.tmx':
                    tmx_file_path = file
                    break
        
        # Procesar traducciones TMX (mismo código que antes)
        tmx_translations = {}
        if tmx_file_path and tmx_file_path.exists():
            try:
                translations = tmx_parser.parse_with_translations(
                    str(tmx_file_path), 
                    source_lang=source_lang,
                    target_lang=target_lang
                )
                
                # Crear índices de traducciones TMX (mismo código que antes)
                from collections import defaultdict
                trans_dict_exact = defaultdict(set)
                trans_dict_partial = defaultdict(set)
                
                for trans in translations:
                    source = trans.get('source', '').strip()
                    target = trans.get('target', '').strip()
                    if source and target:
                        source_lower = source.lower()
                        trans_dict_exact[source_lower].add(target)
                        for word in source_lower.split():
                            if len(word) > 2:
                                trans_dict_partial[word].add(target)
                
                # Procesar cada término
                for term in terms_list:
                    term_lower = term.lower()
                    
                    # Buscar coincidencia exacta
                    if term_lower in trans_dict_exact:
                        translations_list = list(trans_dict_exact[term_lower])
                        tmx_translations[term] = {
                            'translation': ' | '.join(translations_list),
                            'type': 'Exacto',
                            'variants': len(translations_list)
                        }
                    else:
                        # Buscar coincidencia parcial
                        partial_translations = set()
                        words = term_lower.split()
                        
                        for word in words:
                            if len(word) > 2 and word in trans_dict_partial:
                                partial_translations.update(trans_dict_partial[word])
                        
                        if partial_translations:
                            tmx_translations[term] = {
                                'translation': ' | '.join(list(partial_translations)[:3]),
                                'type': 'Parcial',
                                'variants': len(partial_translations)
                            }
                        else:
                            tmx_translations[term] = {
                                'translation': '',
                                'type': 'No encontrado',
                                'variants': 0
                            }
            
            except Exception as e:
                print(f"Error procesando traducciones TMX: {e}")
        
        jobs[job_id]["progress"] = 40
        jobs[job_id]["message"] = "Preparando términos para procesamiento unificado Ollama..."
        
        # Preparar términos que necesitan procesamiento unificado
        terms_for_unified = []
        for term in terms_list:
            tmx_data = tmx_translations.get(term, {})
            if tmx_data.get('type') in ['Parcial', 'No encontrado']:
                term_data = {
                    'Término': term,
                    'Frecuencia': frequencies.get(term, 1),
                    'Palabras': len(term.split()),
                    'Tipo Match': tmx_data.get('type', 'No encontrado'),
                    'TMX_Context': tmx_data.get('translation', '')
                }
                terms_for_unified.append(term_data)
        
        jobs[job_id]["progress"] = 50
        jobs[job_id]["message"] = f"Procesamiento de {len(terms_for_unified)} términos con Ollama..."
        
        # DECISIÓN: Método unificado vs tradicional
        unified_results = {}
        traditional_translations = {}
        
        if terms_for_unified:
            if domain_description and domain_description.strip():
                # MÉTODO UNIFICADO: Traducción + Clasificación en una sola llamada
                jobs[job_id]["message"] = f"Procesamiento unificado de {len(terms_for_unified)} términos (traducción + clasificación)..."
                add_ollama_log("UNIFIED_BATCH_START", None, "INICIANDO", f"Procesamiento unificado de {len(terms_for_unified)} términos")
                
                unified_results = await ollama_translator.translate_and_classify_unified_batch(
                    terms_for_unified, 
                    source_lang, 
                    target_lang,
                    domain_description,
                    max_concurrent=int(os.getenv('OLLAMA_MAX_CONCURRENT', '10'))
                )
                
                add_ollama_log("UNIFIED_BATCH_COMPLETE", None, "COMPLETADO", f"Procesados {len(unified_results)}/{len(terms_for_unified)} términos")
            else:
                # MÉTODO TRADICIONAL: Solo traducción (sin clasificación de dominio)
                jobs[job_id]["message"] = f"Traduciendo {len(terms_for_unified)} términos con Ollama..."
                add_ollama_log("TRADITIONAL_BATCH_START", None, "INICIANDO", f"Traducción tradicional de {len(terms_for_unified)} términos")
                
                traditional_translations = await ollama_translator.translate_terms_batch(
                    terms_for_unified, 
                    source_lang, 
                    target_lang,
                    max_concurrent=int(os.getenv('OLLAMA_MAX_CONCURRENT', '10'))
                )
                
                add_ollama_log("TRADITIONAL_BATCH_COMPLETE", None, "COMPLETADO", f"Traducidos {len(traditional_translations)}/{len(terms_for_unified)} términos")
        
        jobs[job_id]["progress"] = 80
        jobs[job_id]["message"] = "Generando Excel completo pre-calculado..."
        
        # Crear estructura final para Excel con datos unificados
        excel_data = []
        for idx, term in enumerate(terms_list, 1):
            freq = frequencies.get(term, 1)
            word_count = len(term.split())
            tmx_data = tmx_translations.get(term, {})
            
            item = {
                'Número': idx,
                'Término': term,
                'Frecuencia': freq,
                'Longitud': len(term),
                'Palabras': word_count,
                'Idioma': source_lang,
                'Tipo Match': tmx_data.get('type', 'No encontrado'),
                'Variantes': tmx_data.get('variants', 0)
            }
            
            # Determinar traducción y clasificación final
            if term in unified_results:
                # MÉTODO UNIFICADO: Usar resultado unificado de Ollama
                unified_result = unified_results[term]
                item['Traducción'] = unified_result['translation']
                item['Tipo Match'] = f"{tmx_data.get('type', 'No encontrado')} + Ollama Unificado"
                item['Ollama'] = 'Sí (Unificado)'
                item['Contexto Ollama'] = tmx_data.get('translation', 'Sin contexto TMX')
                
                # Añadir columnas de dominio desde resultado unificado
                item['Relevancia Ámbito'] = unified_result['domain_relevance']
                item['Confianza Ámbito'] = f"{unified_result['confidence']}%"
                item['Razón Ámbito'] = unified_result['reason'][:100]
            elif term in traditional_translations:
                # MÉTODO TRADICIONAL: Usar solo traducción de Ollama
                traditional_result = traditional_translations[term]
                item['Traducción'] = traditional_result['translation']
                item['Tipo Match'] = f"{tmx_data.get('type', 'No encontrado')} + Ollama"
                item['Ollama'] = 'Sí (Solo traducción)'
                item['Contexto Ollama'] = tmx_data.get('translation', 'Sin contexto TMX')
                
                # Sin clasificación de dominio
                item['Relevancia Ámbito'] = 'No especificado'
                item['Confianza Ámbito'] = 'N/A'
                item['Razón Ámbito'] = 'No se especificó ámbito'
            else:
                # Usar traducción TMX si existe
                item['Traducción'] = tmx_data.get('translation', '')
                item['Ollama'] = 'No necesario' if tmx_data.get('type') == 'Exacto' else 'No disponible'
                item['Contexto Ollama'] = 'No aplicable' if tmx_data.get('type') == 'Exacto' else 'Sin traducción'
                
                # Columnas de dominio para términos no procesados
                if domain_description and domain_description.strip():
                    item['Relevancia Ámbito'] = 'No procesado'
                    item['Confianza Ámbito'] = 'N/A'
                    item['Razón Ámbito'] = 'Término con traducción exacta TMX'
                else:
                    item['Relevancia Ámbito'] = 'No especificado'
                    item['Confianza Ámbito'] = 'N/A'
                    item['Razón Ámbito'] = 'No se especificó ámbito'
            
            excel_data.append(item)
        
        # Guardar datos pre-procesados COMPLETOS
        processed_data_path = file_handler.get_path("tmx", f"{tmx_id}_processed.json")
        with open(processed_data_path, 'w', encoding='utf-8') as f:
            json.dump({
                'tmx_id': tmx_id,
                'source_lang': source_lang,
                'target_lang': target_lang,
                'domain_description': domain_description,
                'total_terms': len(terms_list),
                'unified_processed': len(unified_results),
                'traditional_translated': len(traditional_translations),
                'data': excel_data,
                'processed_at': datetime.datetime.now().isoformat(),
                'processing_type': 'unified' if unified_results else 'traditional'
            }, f, ensure_ascii=False, indent=2)
        
        jobs[job_id]["status"] = JobStatus.COMPLETED
        jobs[job_id]["progress"] = 100
        
        # Mensaje final informativo
        if unified_results:
            jobs[job_id]["message"] = f"Procesamiento unificado completado: {len(unified_results)} términos (traducción + clasificación)"
        elif traditional_translations:
            jobs[job_id]["message"] = f"Traducción completada: {len(traditional_translations)} términos traducidos"
        else:
            jobs[job_id]["message"] = "Procesamiento completado: Solo traducciones TMX utilizadas"
        jobs[job_id]["processed_file"] = f"{tmx_id}_processed.json"
        
    except Exception as e:
        jobs[job_id]["status"] = JobStatus.FAILED
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["message"] = f"Error en procesamiento unificado: {str(e)}"


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
