"""
Router para endpoints de Ollama (traducción y clasificación)
"""
from fastapi import APIRouter, HTTPException
from typing import Optional

from app.models import BatchTranslationRequest, DomainClassificationRequest
from app.dependencies import ollama_translator, ollama_logs

router = APIRouter(prefix="/api/ollama", tags=["ollama"])


@router.get("/status")
async def ollama_status():
    """Verificar estado de conexión con Ollama"""
    return ollama_translator.test_connection()


@router.post("/translate")
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


@router.get("/cache/stats")
async def ollama_cache_stats():
    """Obtener estadísticas del caché de Ollama"""
    return ollama_translator.get_cache_stats()


@router.get("/logs")
async def get_ollama_logs(limit: int = 50):
    """Obtener logs recientes de Ollama en tiempo real"""
    return {
        "logs": ollama_logs[-limit:] if ollama_logs else [],
        "total_logs": len(ollama_logs)
    }


@router.delete("/cache")
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


@router.post("/classify-domain")
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


@router.post("/translate-batch")
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
