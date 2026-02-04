"""
Router para endpoints de TMX (memorias de traducción)
"""
import os
import uuid
import json
import asyncio
import shutil
from pathlib import Path
from typing import Optional
from threading import Thread
from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from app.models import UploadResponse, ExtractTMXLanguageRequest, JobStatus
from app.dependencies import (
    tmx_parser, file_handler, ollama_translator, 
    termsuite_service, jobs
)

router = APIRouter(prefix="/api", tags=["tmx"])


@router.post("/upload-tmx", response_model=UploadResponse)
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
                "available_languages": available_languages,
                "original_filename": file.filename,
                "uploaded_at": datetime.utcnow().isoformat() + "Z"
            }
            terms_path = file_handler.get_path("tmx", f"{file_id}_terms.json")
            with open(terms_path, 'w', encoding='utf-8') as f:
                json.dump(terms_data, f, ensure_ascii=False, indent=2)
            
            lang_msg = f" del idioma '{language}'"
            message = f"TMX subido exitosamente. {len(terms)} términos{lang_msg} encontrados."
        else:
            # Solo guardar idiomas disponibles
            terms_data = {
                "available_languages": available_languages,
                "original_filename": file.filename,
                "uploaded_at": datetime.utcnow().isoformat() + "Z"
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


@router.get("/analyses")
async def list_analyses(limit: int = 50):
    """
    Listar historial de análisis TMX realizados (para recuperar o re-descargar).
    Ordenado por fecha de subida, más reciente primero.
    """
    tmx_dir = file_handler.uploads_dir / 'tmx'
    if not tmx_dir.exists():
        return {"analyses": [], "total": 0}

    analyses = []
    for path in tmx_dir.glob("*_terms.json"):
        try:
            tmx_id = path.stem.replace("_terms", "")
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                uploaded_at = data.get("uploaded_at") or datetime.utcfromtimestamp(path.stat().st_mtime).isoformat() + "Z"
                original_filename = data.get("original_filename") or f"tmx_{tmx_id[:8]}.tmx"
                source_language = data.get("language", "")
                total_terms = data.get("total", 0)
                total_occurrences = data.get("total_occurrences", 0)
            else:
                uploaded_at = datetime.utcfromtimestamp(path.stat().st_mtime).isoformat() + "Z"
                original_filename = f"tmx_{tmx_id[:8]}.tmx"
                source_language = ""
                total_terms = 0
                total_occurrences = 0

            processed_path = file_handler.get_path("tmx", f"{tmx_id}_processed.json")
            has_processed = processed_path.exists()
            target_language = ""
            if has_processed:
                try:
                    with open(processed_path, 'r', encoding='utf-8') as pf:
                        proc = json.load(pf)
                    if isinstance(proc, dict):
                        target_language = proc.get("target_lang", "")
                except Exception:
                    pass

            analyses.append({
                "tmx_id": tmx_id,
                "original_filename": original_filename,
                "uploaded_at": uploaded_at,
                "source_language": source_language,
                "target_language": target_language,
                "total_terms": total_terms,
                "total_occurrences": total_occurrences,
                "has_processed": has_processed
            })
        except Exception as e:
            continue

    analyses.sort(key=lambda x: x["uploaded_at"], reverse=True)
    analyses = analyses[:limit]
    return {"analyses": analyses, "total": len(analyses)}


@router.get("/analyses/{tmx_id}/summary")
async def get_analysis_summary(tmx_id: str):
    """
    Resumen de un análisis (para restaurar vista de resultados).
    """
    terms_path = file_handler.get_path("tmx", f"{tmx_id}_terms.json")
    if not terms_path.exists():
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    with open(terms_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise HTTPException(status_code=404, detail="Datos de análisis no válidos")
    processed_path = file_handler.get_path("tmx", f"{tmx_id}_processed.json")
    target_lang = ""
    if processed_path.exists():
        try:
            with open(processed_path, 'r', encoding='utf-8') as pf:
                proc = json.load(pf)
            if isinstance(proc, dict):
                target_lang = proc.get("target_lang", "")
        except Exception:
            pass
    return {
        "tmx_id": tmx_id,
        "original_filename": data.get("original_filename", f"tmx_{tmx_id[:8]}.tmx"),
        "source_language": data.get("language", ""),
        "target_language": target_lang,
        "total_terms": data.get("total", 0),
        "total_occurrences": data.get("total_occurrences", 0),
        "available_languages": data.get("available_languages", [])
    }


@router.get("/tmx-languages/{tmx_id}")
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


@router.get("/tmx-debug/{tmx_id}")
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


@router.post("/extract-tmx-language")
async def extract_tmx_language_post(request: ExtractTMXLanguageRequest):
    """
    Extraer términos de un TMX para un idioma específico con traducción opcional (POST con JSON)
    """
    return await _extract_tmx_language_impl(
        request.tmx_id, 
        request.language, 
        request.target_language, 
        request.use_termsuite,
        request.domain_description,
        request.min_words,
        request.max_words
    )


@router.get("/extract-tmx-language")
async def extract_tmx_language_get(
    tmx_id: str, 
    language: str, 
    target_language: Optional[str] = None,
    use_termsuite: bool = False,
    domain_description: Optional[str] = None,
    min_words: Optional[int] = None,
    max_words: Optional[int] = None
):
    """
    Extraer términos de un TMX para un idioma específico con traducción opcional (GET con query params)
    """
    return await _extract_tmx_language_impl(tmx_id, language, target_language, use_termsuite, domain_description, min_words, max_words)


async def _extract_tmx_language_impl(
    tmx_id: str, 
    language: str, 
    target_language: Optional[str] = None,
    use_termsuite: bool = False,
    domain_description: Optional[str] = None,
    min_words: Optional[int] = None,
    max_words: Optional[int] = None
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
            if temp_corpus_dir.exists():
                shutil.rmtree(temp_corpus_dir)
            temp_output_path.unlink(missing_ok=True)
            
        else:
            # Modo directo: Extraer segmentos completos
            terms = tmx_parser.parse(str(tmx_file_path), language=language)
            terms_freq = tmx_parser.parse_with_frequency(str(tmx_file_path), language=language)
        
        # Aplicar filtro min_words/max_words ANTES de guardar y antes de lanzar Ollama
        # (reduce mucho el tiempo total al evitar términos largos)
        if min_words is not None or max_words is not None:
            def _wc(s: str) -> int:
                return len((s or "").split())

            filtered_terms = []
            for t in terms:
                wc = _wc(t)
                if min_words is not None and wc < int(min_words):
                    continue
                if max_words is not None and wc > int(max_words):
                    continue
                filtered_terms.append(t)

            terms = filtered_terms
            if isinstance(terms_freq, dict) and terms_freq:
                terms_freq = {t: terms_freq.get(t, 1) for t in terms}

        # Actualizar archivo de términos (preservar original_filename y uploaded_at si existían)
        terms_path = file_handler.get_path("tmx", f"{tmx_id}_terms.json")
        existing_meta = {}
        if terms_path.exists():
            try:
                with open(terms_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                if isinstance(existing, dict):
                    for key in ("original_filename", "uploaded_at", "available_languages"):
                        if key in existing:
                            existing_meta[key] = existing[key]
            except Exception:
                pass
        
        terms_data = {
            "language": language,
            "terms": terms,
            "frequencies": terms_freq,
            "total": len(terms),
            "total_occurrences": sum(terms_freq.values()),
            "extraction_mode": "termsuite" if use_termsuite else "direct",
            "min_words": min_words,
            "max_words": max_words,
            **existing_meta
        }
        
        if target_language:
            terms_data["target_language"] = target_language
        if domain_description and domain_description.strip():
            terms_data["domain_description"] = domain_description.strip()
        
        with open(terms_path, 'w', encoding='utf-8') as f:
            json.dump(terms_data, f, ensure_ascii=False, indent=2)
        
        mode_msg = " (con TermSuite)" if use_termsuite else ""
        msg = f"{len(terms)} términos del idioma '{language}' extraídos{mode_msg}"
        if target_language:
            msg += f" (traducción: {target_language})"
        
        # NUEVO: Si hay idioma destino, iniciar traducciones automáticamente (solo si Ollama está disponible)
        translation_job_id = None
        if target_language:
            if ollama_translator.is_available():
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
                from app.routers.background_tasks import process_auto_translations_unified
                
                def run_auto_translations():
                    asyncio.run(process_auto_translations_unified(translation_job_id, tmx_id, language, target_language))
                
                thread = Thread(target=run_auto_translations)
                thread.daemon = True
                thread.start()
                
                msg += f" - Traducciones y clasificación iniciadas automáticamente (Job ID: {translation_job_id})"
            else:
                msg += " - Ollama no disponible: no se han iniciado traducciones ni clasificación. Comprueba que el servidor Ollama esté en marcha."
        
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
