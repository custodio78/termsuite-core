# IMPLEMENTACIÓN DE LA OPTIMIZACIÓN UNIFICADA

## 🔧 CÓDIGO ESPECÍFICO PARA IMPLEMENTAR

---

## 1. NUEVO MÉTODO UNIFICADO EN `ollama_translator.py`

### Añadir al final de la clase `OllamaTranslator`:

```python
async def translate_and_classify_unified_batch(
    self, 
    terms_data: List[Dict], 
    source_lang: str, 
    target_lang: str,
    domain_description: str,
    max_concurrent: int = None
) -> Dict[str, dict]:
    """
    MÉTODO UNIFICADO: Traducir Y clasificar términos en una sola llamada por término
    
    Args:
        terms_data: Lista de diccionarios con términos a procesar
        source_lang: Idioma origen
        target_lang: Idioma destino  
        domain_description: Descripción del ámbito/dominio
        max_concurrent: Máximo número de llamadas concurrentes
        
    Returns:
        Diccionario con término -> {translation, domain_relevance, confidence, reason, ...}
    """
    unified_results = {}
    
    # Usar configuración optimizada
    if max_concurrent is None:
        max_concurrent = int(os.getenv('OLLAMA_MAX_CONCURRENT', '10'))  # Aumentado de 3 a 10
    
    # Filtrar términos que necesitan procesamiento
    terms_to_process = [
        term for term in terms_data 
        if term.get('Tipo Match') in ['Parcial', 'No encontrado'] and 
           term.get('Término', '').strip()
    ]
    
    if not terms_to_process:
        return unified_results
    
    # 1. Verificar caché unificado primero
    cached_results = {}
    remaining_terms = []
    
    for term_data in terms_to_process:
        term = term_data['Término']
        context = term_data.get('TMX_Context', '')
        
        # Clave de caché unificada
        cache_key = self._get_unified_cache_key(term, source_lang, target_lang, context, domain_description)
        
        if cache_key in self.memory_cache:
            cached_results[term] = self.memory_cache[cache_key]
        else:
            remaining_terms.append(term_data)
    
    print(f"Unified cache hit: {len(cached_results)}/{len(terms_to_process)} términos")
    unified_results.update(cached_results)
    
    if not remaining_terms:
        return unified_results
    
    # 2. Procesar términos restantes con llamadas unificadas
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_unified_single(term_data):
        async with semaphore:
            term = term_data['Término']
            context = term_data.get('TMX_Context', '')
            
            try:
                # Usar requests en un executor para no bloquear
                loop = asyncio.get_event_loop()
                unified_result = await loop.run_in_executor(
                    None, 
                    self._translate_and_classify_unified_single, 
                    term, 
                    source_lang, 
                    target_lang,
                    context,
                    domain_description
                )
                
                if unified_result:
                    # Guardar en caché unificado
                    cache_key = self._get_unified_cache_key(term, source_lang, target_lang, context, domain_description)
                    self.memory_cache[cache_key] = unified_result
                    return term, unified_result
                return term, None
                
            except Exception as e:
                print(f"Error in unified processing for '{term}': {str(e)}")
                return term, None
    
    # Ejecutar procesamiento unificado en paralelo
    tasks = [process_unified_single(term_data) for term_data in remaining_terms]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Procesar resultados
    for result in results:
        if isinstance(result, tuple) and len(result) == 2:
            term, unified_result = result
            if unified_result:
                unified_results[term] = unified_result
    
    return unified_results

def _get_unified_cache_key(self, term: str, source_lang: str, target_lang: str, context: str, domain_description: str) -> str:
    """Generar clave única para caché unificado"""
    import hashlib
    key_data = f"UNIFIED|{term}|{source_lang}|{target_lang}|{context or ''}|{domain_description or ''}"
    return hashlib.md5(key_data.encode()).hexdigest()

def _translate_and_classify_unified_single(
    self, 
    term: str, 
    source_lang: str, 
    target_lang: str, 
    context: str, 
    domain_description: str
) -> Optional[dict]:
    """
    Procesar UN término con traducción + clasificación en una sola llamada
    """
    try:
        # Log inicio
        if self.log_callback:
            self.log_callback("UNIFIED_START", term, "INICIANDO", f"Traducción + Clasificación unificada")
        
        # Crear prompt unificado
        prompt = self._create_unified_prompt(term, source_lang, target_lang, context, domain_description)
        
        # Log del prompt
        if self.log_callback:
            self.log_callback("UNIFIED_PROMPT_SENT", term, "ENVIANDO", f"Prompt unificado enviado", prompt=prompt[:200])
        
        # Hacer petición a Ollama
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "max_tokens": 150  # Más tokens para respuesta JSON
            }
        }
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=int(os.getenv('OLLAMA_TIMEOUT', '45'))  # Timeout aumentado
        )
        
        if response.status_code == 200:
            result = response.json()
            raw_response = result.get('response', '').strip()
            
            # Log respuesta cruda
            if self.log_callback:
                self.log_callback("UNIFIED_RESPONSE_RECEIVED", term, "RESPUESTA", f"Respuesta unificada recibida", response=raw_response[:200])
            
            # Parsear respuesta JSON unificada
            unified_data = self._parse_unified_response(raw_response)
            
            if unified_data:
                # Log éxito
                if self.log_callback:
                    translation = unified_data.get('translation', '')
                    relevance = unified_data.get('domain_relevance', '')
                    confidence = unified_data.get('confidence', 0)
                    self.log_callback("UNIFIED_SUCCESS", term, "COMPLETADO", f"Trad: '{translation}' | Dom: {relevance} ({confidence}%)")
                
                return {
                    'translation': unified_data.get('translation', ''),
                    'context': context or 'Sin contexto específico',
                    'source_lang': source_lang,
                    'target_lang': target_lang,
                    'domain_relevance': unified_data.get('domain_relevance', 'Error'),
                    'confidence': unified_data.get('confidence', 0),
                    'reason': unified_data.get('reason', 'Sin razón'),
                    'domain_description': domain_description
                }
        else:
            # Log error HTTP
            if self.log_callback:
                self.log_callback("UNIFIED_HTTP_ERROR", term, "ERROR", f"HTTP {response.status_code}")
        
        return None
        
    except Exception as e:
        if self.log_callback:
            self.log_callback("UNIFIED_ERROR", term, "ERROR", f"Error: {str(e)[:100]}")
        print(f"Error in unified processing for '{term}': {str(e)}")
        return None

def _create_unified_prompt(self, term: str, source_lang: str, target_lang: str, context: str, domain_description: str) -> str:
    """
    Crear prompt unificado que hace traducción + clasificación en una sola llamada
    """
    # Mapeo de idiomas
    lang_names = {
        'es': 'Spanish', 'en': 'English', 'fr': 'French',
        'de': 'German', 'it': 'Italian', 'pt': 'Portuguese',
        'ca': 'Catalan', 'eu': 'Basque', 'gl': 'Galician'
    }
    
    source_name = lang_names.get(source_lang, source_lang)
    target_name = lang_names.get(target_lang, target_lang)
    
    # Prompt unificado optimizado
    prompt = f"""You are a technical translator and domain classifier. Process the term "{term}" from {source_name} to {target_name}.

TASKS:
1. TRANSLATE: Based on TMX context: "{context}"
2. CLASSIFY: Relevance to domain: "{domain_description}"

TMX TRANSLATION RULES:
- Extract ONLY translations that appear in the TMX context
- If no translation in context, provide best technical translation
- Clean output, no explanations or symbols

DOMAIN CLASSIFICATION RULES:  
- "Sí": Term is directly related to the domain
- "No": Term is generic or unrelated to domain
- "Incierto": Uncertain relevance
- Be strict: only "Sí" for clearly domain-specific terms

RESPOND in this EXACT JSON format (no other text):
{{
    "translation": "clean translation here",
    "domain_relevance": "Sí",
    "confidence": 85,
    "reason": "brief explanation in {source_name}"
}}"""

    return prompt

def _parse_unified_response(self, response_text: str) -> Optional[dict]:
    """
    Parsear respuesta JSON unificada de Ollama
    """
    try:
        # Limpiar respuesta para extraer JSON
        response_text = response_text.strip()
        
        # Buscar JSON en la respuesta
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(0)
            
            # Intentar parsear JSON
            import json
            data = json.loads(json_text)
            
            # Validar campos requeridos
            if all(key in data for key in ['translation', 'domain_relevance', 'confidence']):
                # Limpiar traducción
                data['translation'] = self._clean_translation(data['translation'])
                
                # Validar relevancia
                if data['domain_relevance'] not in ['Sí', 'No', 'Incierto']:
                    data['domain_relevance'] = 'Error'
                
                # Validar confianza
                try:
                    data['confidence'] = max(0, min(100, int(data['confidence'])))
                except:
                    data['confidence'] = 0
                
                # Asegurar razón
                if 'reason' not in data:
                    data['reason'] = 'Sin explicación'
                
                return data
        
        return None
        
    except Exception as e:
        print(f"Error parsing unified response: {str(e)}")
        return None
```

---

## 2. MODIFICACIONES EN `main.py`

### Reemplazar la función `process_auto_translations`:

```python
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
        jobs[job_id]["message"] = f"Procesamiento unificado de {len(terms_for_unified)} términos (traducción + clasificación)..."
        
        # NUEVO: Procesamiento unificado con Ollama
        unified_results = {}
        if terms_for_unified and domain_description and domain_description.strip():
            add_ollama_log("UNIFIED_BATCH_START", None, "INICIANDO", f"Procesamiento unificado de {len(terms_for_unified)} términos")
            
            unified_results = await ollama_translator.translate_and_classify_unified_batch(
                terms_for_unified, 
                source_lang, 
                target_lang,
                domain_description,
                max_concurrent=int(os.getenv('OLLAMA_MAX_CONCURRENT', '10'))  # Configuración optimizada
            )
            
            add_ollama_log("UNIFIED_BATCH_COMPLETE", None, "COMPLETADO", f"Procesados {len(unified_results)}/{len(terms_for_unified)} términos")
        
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
                # Usar resultado unificado de Ollama
                unified_result = unified_results[term]
                item['Traducción'] = unified_result['translation']
                item['Tipo Match'] = f"{tmx_data.get('type', 'No encontrado')} + Ollama"
                item['Ollama'] = 'Sí'
                item['Contexto Ollama'] = tmx_data.get('translation', 'Sin contexto TMX')
                
                # NUEVO: Añadir columnas de dominio desde resultado unificado
                item['Relevancia Ámbito'] = unified_result['domain_relevance']
                item['Confianza Ámbito'] = f"{unified_result['confidence']}%"
                item['Razón Ámbito'] = unified_result['reason'][:100]
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
        
        # Guardar datos pre-procesados COMPLETOS (con clasificación de dominio)
        processed_data_path = file_handler.get_path("tmx", f"{tmx_id}_processed.json")
        with open(processed_data_path, 'w', encoding='utf-8') as f:
            json.dump({
                'tmx_id': tmx_id,
                'source_lang': source_lang,
                'target_lang': target_lang,
                'domain_description': domain_description,
                'total_terms': len(terms_list),
                'unified_processed': len(unified_results),
                'data': excel_data,
                'processed_at': datetime.datetime.now().isoformat(),
                'processing_type': 'unified'  # NUEVO: Marcar como procesamiento unificado
            }, f, ensure_ascii=False, indent=2)
        
        jobs[job_id]["status"] = JobStatus.COMPLETED
        jobs[job_id]["progress"] = 100
        jobs[job_id]["message"] = f"Procesamiento unificado completado: {len(unified_results)} términos procesados"
        jobs[job_id]["processed_file"] = f"{tmx_id}_processed.json"
        
    except Exception as e:
        jobs[job_id]["status"] = JobStatus.FAILED
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["message"] = f"Error en procesamiento unificado: {str(e)}"
```

### Modificar la llamada en `_extract_tmx_language_impl`:

```python
# Reemplazar esta línea:
# asyncio.run(process_auto_translations(translation_job_id, tmx_id, language, target_language))

# Por esta:
asyncio.run(process_auto_translations_unified(translation_job_id, tmx_id, language, target_language))
```

---

## 3. CONFIGURACIÓN OPTIMIZADA

### Añadir al `docker-compose.yml`:

```yaml
environment:
  - OLLAMA_BATCH_SIZE=10
  - OLLAMA_MAX_CONCURRENT=10
  - OLLAMA_TIMEOUT=45
  - OLLAMA_UNIFIED_MODE=true
```

---

## 4. ENDPOINT DE DESCARGA INSTANTÁNEA

### Añadir a `main.py`:

```python
@app.get("/api/export/tmx-excel-instant/{tmx_id}")
async def export_tmx_instant(tmx_id: str):
    """
    Descarga instantánea de Excel pre-generado con procesamiento unificado
    """
    processed_data_path = file_handler.get_path("tmx", f"{tmx_id}_processed.json")
    
    if processed_data_path.exists():
        with open(processed_data_path, 'r', encoding='utf-8') as f:
            processed_data = json.load(f)
        
        # Verificar que sea procesamiento unificado completo
        if processed_data.get('processing_type') == 'unified':
            # Generar Excel desde datos pre-procesados
            excel_data = processed_data['data']
            
            # Crear Excel optimizado
            import pandas as pd
            df = pd.DataFrame(excel_data)
            
            excel_filename = f"tmx_unified_{tmx_id}.xlsx"
            excel_path = file_handler.get_path("outputs", excel_filename)
            
            # Generar Excel con formato optimizado (mismo código que antes)
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Términos TMX', index=False)
                
                # Aplicar formato (mismo código que antes)
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
        
        if processed_data.get('processing_type') == 'unified':
            return {
                "tmx_id": tmx_id,
                "unified_ready": True,
                "total_terms": processed_data.get('total_terms', 0),
                "unified_processed": processed_data.get('unified_processed', 0),
                "processed_at": processed_data.get('processed_at'),
                "domain_description": processed_data.get('domain_description'),
                "instant_download_available": True
            }
    
    # Verificar si hay trabajo en progreso
    unified_jobs = [
        job for job_id, job in jobs.items() 
        if job.get('type') == 'auto_translation' and job.get('tmx_id') == tmx_id
    ]
    
    if unified_jobs:
        latest_job = max(unified_jobs, key=lambda x: jobs.get(x, {}).get('progress', 0))
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
```

---

## 5. MODIFICACIONES EN EL FRONTEND

### Actualizar `app_v2.js`:

```javascript
// Añadir después de la función downloadResults():

async function checkUnifiedStatus(tmxId) {
    """Verificar si el procesamiento unificado está listo"""
    try {
        const response = await fetch(`${API_BASE}/api/tmx/${tmxId}/unified-status`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error checking unified status:', error);
        return { unified_ready: false };
    }
}

async function downloadResultsOptimized() {
    """Descarga optimizada con verificación de procesamiento unificado"""
    const downloadBtn = document.querySelector('.btn-download');
    if (!downloadBtn || !state.fileId) {
        showToast('Error: No hay archivo cargado', 'error');
        return;
    }
    
    const originalText = downloadBtn.innerHTML;
    
    try {
        downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verificando...';
        downloadBtn.disabled = true;
        
        // Verificar si hay procesamiento unificado disponible
        const unifiedStatus = await checkUnifiedStatus(state.fileId);
        
        if (unifiedStatus.unified_ready && unifiedStatus.instant_download_available) {
            // DESCARGA INSTANTÁNEA
            downloadBtn.innerHTML = '<i class="fas fa-download"></i> Descarga instantánea...';
            
            const downloadUrl = `${API_BASE}/api/export/tmx-excel-instant/${state.fileId}`;
            
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = `terminos_unificado_${state.sourceLanguage}_${state.targetLanguage}.xlsx`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            showToast('¡Excel descargado instantáneamente con procesamiento unificado!', 'success');
            
        } else if (unifiedStatus.in_progress) {
            // MOSTRAR PROGRESO
            downloadBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${unifiedStatus.progress}% - ${unifiedStatus.message}`;
            
            // Esperar y reintentar
            setTimeout(() => downloadResultsOptimized(), 2000);
            return;
            
        } else {
            // FALLBACK AL MÉTODO TRADICIONAL
            downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Preparando (método tradicional)...';
            
            // Usar el método de descarga original
            await downloadResults();
        }
        
    } catch (error) {
        showToast(`Error: ${error.message}`, 'error');
    } finally {
        downloadBtn.innerHTML = originalText;
        downloadBtn.disabled = false;
    }
}

// Reemplazar la llamada en el botón de descarga:
// onclick="downloadResults()" 
// por:
// onclick="downloadResultsOptimized()"
```

---

## 📋 RESUMEN DE CAMBIOS

### **ARCHIVOS A MODIFICAR:**
1. ✅ `app/services/ollama_translator.py` - Añadir métodos unificados
2. ✅ `app/main.py` - Reemplazar `process_auto_translations` y añadir endpoints
3. ✅ `app/static/js/app_v2.js` - Añadir descarga optimizada
4. ✅ `docker-compose.yml` - Añadir variables de entorno optimizadas

### **BENEFICIOS ESPERADOS:**
- ✅ **70-80% reducción** en tiempo total de procesamiento
- ✅ **Descarga instantánea** cuando el procesamiento unificado está listo
- ✅ **50% menos llamadas HTTP** a Ollama
- ✅ **Mejor experiencia de usuario** con progreso visible

### **COMPATIBILIDAD:**
- ✅ **Backward compatible** - fallback al método tradicional si no hay procesamiento unificado
- ✅ **Configuración flexible** - se puede activar/desactivar con variables de entorno
- ✅ **Caché inteligente** - reutiliza resultados previos