"""
Router para endpoints de estado y verificación
"""
from fastapi import APIRouter, HTTPException

from app.models import JobStatusResponse, JobStatus
from app.dependencies import jobs, file_handler, ollama_translator

router = APIRouter(prefix="/api", tags=["status"])


@router.get("/status/{job_id}", response_model=JobStatusResponse)
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


@router.get("/tmx/{tmx_id}/export-ready")
async def check_tmx_export_ready(tmx_id: str):
    """
    Verificar si un TMX está listo para descarga rápida
    Considera datos pre-procesados, número de términos y columnas de dominio
    """
    import json
    
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
    
    # Verificar si los datos pre-procesados incluyen columnas de dominio
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
        not has_domain_columns
    )
    
    # Determinar si está listo para descarga rápida
    ready_for_fast_download = (
        has_processed_data and
        total_terms <= 100 and
        not needs_domain_processing
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


@router.get("/tmx/{tmx_id}/translation-status")
async def get_translation_status(tmx_id: str):
    """Verificar si las traducciones automáticas están listas para un TMX"""
    import json
    
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


@router.get("/tmx/{tmx_id}/unified-status")
async def check_unified_status(tmx_id: str):
    """
    Verificar estado del procesamiento unificado
    """
    import json
    
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
