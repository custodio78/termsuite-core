# OPTIMIZACIÓN UNIFICADA DE OLLAMA
## Combinando Llamadas Unificadas + Procesamiento Asíncrono + Lotes Inteligentes

---

## 🎯 OBJETIVO
Reducir el tiempo total de procesamiento en **70-80%** mediante:
- **Llamadas unificadas** (traducción + clasificación en una sola petición)
- **Procesamiento completamente asíncrono** (todo en background)
- **Lotes inteligentes** con mayor concurrencia
- **Descarga instantánea** de resultados pre-calculados

---

## 🏗️ ARQUITECTURA PROPUESTA

### **FLUJO ACTUAL (LENTO):**
```
1. Usuario sube TMX → Extracción TermSuite
2. Background: Traducciones Ollama (3 concurrent, solo traducción)
3. Usuario descarga → Clasificación Ollama (3 concurrent, solo clasificación)
4. Generar Excel → Descarga
```
**Tiempo total:** ~5-10 minutos para 100 términos

### **FLUJO OPTIMIZADO (RÁPIDO):**
```
1. Usuario sube TMX → Extracción TermSuite
2. Background: Procesamiento Unificado Ollama (10 concurrent, traducción + clasificación)
3. Background: Excel pre-generado y cacheado
4. Usuario descarga → Descarga instantánea (0 segundos)
```
**Tiempo total:** ~1-2 minutos para 100 términos + descarga instantánea

---

## 🔧 COMPONENTES DE LA SOLUCIÓN

### **1. LLAMADA UNIFICADA A OLLAMA** (Opción 1)

#### Nuevo método en `OllamaTranslator`:
```python
async def translate_and_classify_unified_batch(
    self, 
    terms_data: List[Dict], 
    source_lang: str, 
    target_lang: str,
    domain_description: str,
    max_concurrent: int = 10  # Aumentado de 3 a 10
) -> Dict[str, dict]:
    """
    Procesar traducción Y clasificación en una sola llamada por término
    con lotes inteligentes y mayor concurrencia
    """
```

#### Prompt unificado optimizado:
```python
def _create_unified_prompt(self, term: str, source_lang: str, target_lang: str, 
                          context: str, domain_description: str) -> str:
    """
    Prompt que hace traducción + clasificación en una sola llamada
    """
    return f"""You are a technical translator and domain classifier.

TASK: For the term "{term}" ({source_lang} → {target_lang}):
1. TRANSLATE based on TMX context: {context}
2. CLASSIFY relevance to domain: "{domain_description}"

RESPOND in this EXACT JSON format:
{{
    "translation": "clean translation here",
    "domain_relevance": "Sí|No|Incierto",
    "confidence": 85,
    "reason": "brief explanation in {source_lang}"
}}

CRITICAL: Respond ONLY with valid JSON, no explanations."""
```

### **2. PROCESAMIENTO COMPLETAMENTE ASÍNCRONO** (Opción 2)

#### Nuevo flujo de procesamiento:
```python
# En main.py - Al subir TMX
async def process_tmx_complete_unified(
    tmx_id: str, 
    language: str, 
    target_language: str, 
    domain_description: str
):
    """
    Procesar TODO en background:
    1. Extracción TermSuite
    2. Traducción + Clasificación unificada (Ollama)
    3. Generar Excel completo
    4. Cachear resultado
    """
    
    # Fase 1: Extracción (ya existe)
    terms_data = extract_terms_with_termsuite(tmx_id, language)
    
    # Fase 2: Procesamiento unificado Ollama
    unified_results = await ollama_translator.translate_and_classify_unified_batch(
        terms_data, language, target_language, domain_description,
        max_concurrent=10  # Mayor concurrencia
    )
    
    # Fase 3: Generar Excel completo pre-calculado
    excel_data = build_complete_excel_data(terms_data, unified_results)
    excel_path = generate_excel_file(tmx_id, excel_data)
    
    # Fase 4: Cachear resultado para descarga instantánea
    cache_complete_result(tmx_id, excel_path, excel_data)
```

#### Descarga instantánea:
```python
@app.get("/api/export/tmx-excel-instant/{tmx_id}")
async def export_tmx_instant(tmx_id: str):
    """
    Descarga instantánea de Excel pre-generado
    """
    cached_excel = get_cached_excel(tmx_id)
    if cached_excel:
        return FileResponse(cached_excel.path)
    else:
        # Fallback al método tradicional si no está cacheado
        return await export_tmx_to_excel_async(tmx_id)
```

### **3. LOTES INTELIGENTES CON MAYOR CONCURRENCIA** (Opción 3)

#### Configuración optimizada:
```python
# En ollama_translator.py
class OllamaTranslator:
    def __init__(self):
        # Configuración optimizada para mayor throughput
        self.batch_size = int(os.getenv('OLLAMA_BATCH_SIZE', '10'))  # 5 → 10
        self.max_concurrent = int(os.getenv('OLLAMA_MAX_CONCURRENT', '10'))  # 3 → 10
        self.timeout = int(os.getenv('OLLAMA_TIMEOUT', '45'))  # 30 → 45
        self.chunk_size = int(os.getenv('OLLAMA_CHUNK_SIZE', '20'))  # Nuevo
```

#### Procesamiento en chunks inteligentes:
```python
async def process_terms_in_smart_chunks(
    self, 
    terms: List[Dict], 
    chunk_size: int = 20
) -> Dict[str, dict]:
    """
    Procesar términos en chunks inteligentes para optimizar throughput
    """
    # Dividir términos en chunks
    chunks = [terms[i:i+chunk_size] for i in range(0, len(terms), chunk_size)]
    
    # Procesar chunks en paralelo con límite de concurrencia
    semaphore = asyncio.Semaphore(self.max_concurrent)
    
    async def process_chunk(chunk):
        async with semaphore:
            return await self.translate_and_classify_unified_batch(
                chunk, source_lang, target_lang, domain_description
            )
    
    # Ejecutar todos los chunks en paralelo
    chunk_tasks = [process_chunk(chunk) for chunk in chunks]
    chunk_results = await asyncio.gather(*chunk_tasks)
    
    # Combinar resultados
    final_results = {}
    for chunk_result in chunk_results:
        final_results.update(chunk_result)
    
    return final_results
```

---

## 📊 COMPARACIÓN DE RENDIMIENTO

### **ESCENARIO: 100 términos con traducción + clasificación**

| Método | Llamadas HTTP | Tiempo Procesamiento | Tiempo Descarga | Total |
|--------|---------------|---------------------|-----------------|-------|
| **Actual** | 200 (100 trad + 100 clas) | 8-10 min | 2-3 min | **10-13 min** |
| **Unificado** | 100 (trad + clas juntos) | 3-4 min | 0 seg | **3-4 min** |
| **Mejora** | **50% menos** | **60% menos** | **100% menos** | **70-75% menos** |

### **ESCENARIO: 500 términos con traducción + clasificación**

| Método | Llamadas HTTP | Tiempo Procesamiento | Tiempo Descarga | Total |
|--------|---------------|---------------------|-----------------|-------|
| **Actual** | 1000 (500 trad + 500 clas) | 25-30 min | 8-10 min | **35-40 min** |
| **Unificado** | 500 (trad + clas juntos) | 8-10 min | 0 seg | **8-10 min** |
| **Mejora** | **50% menos** | **70% menos** | **100% menos** | **75-80% menos** |

---

## 🔄 FLUJO DE IMPLEMENTACIÓN

### **FASE 1: Método Unificado**
```python
# Nuevo método en ollama_translator.py
async def translate_and_classify_unified_batch(...)
def _create_unified_prompt(...)
def _parse_unified_response(...)
```

### **FASE 2: Procesamiento Asíncrono Completo**
```python
# Modificar main.py
async def process_tmx_complete_unified(...)
def cache_complete_result(...)
@app.get("/api/export/tmx-excel-instant/{tmx_id}")
```

### **FASE 3: Optimización de Concurrencia**
```python
# Actualizar configuración
OLLAMA_BATCH_SIZE=10
OLLAMA_MAX_CONCURRENT=10
OLLAMA_TIMEOUT=45
OLLAMA_CHUNK_SIZE=20
```

### **FASE 4: Frontend Adaptado**
```javascript
// Modificar app_v2.js
async function checkProcessingStatus(tmx_id) {
    // Verificar si el procesamiento completo está listo
    const status = await fetch(`/api/tmx/${tmx_id}/complete-status`);
    if (status.ready) {
        showInstantDownloadButton();
    } else {
        showProgressBar(status.progress);
    }
}
```

---

## 🎯 BENEFICIOS ESPERADOS

### **RENDIMIENTO:**
- ✅ **70-80% reducción** en tiempo total
- ✅ **50% menos llamadas HTTP** a Ollama
- ✅ **Descarga instantánea** (0 segundos)
- ✅ **Mayor throughput** de Ollama

### **EXPERIENCIA DE USUARIO:**
- ✅ **Procesamiento transparente** en background
- ✅ **Descarga inmediata** cuando está listo
- ✅ **Progreso visible** durante procesamiento
- ✅ **Menos esperas** para el usuario

### **EFICIENCIA TÉCNICA:**
- ✅ **Mejor utilización** de recursos Ollama
- ✅ **Caché inteligente** de resultados
- ✅ **Paralelización optimizada**
- ✅ **Menos carga** en el servidor

---

## 🔧 CONFIGURACIÓN RECOMENDADA

### **Variables de entorno optimizadas:**
```bash
# En docker-compose.yml o .env
OLLAMA_BATCH_SIZE=10          # Aumentado de 5
OLLAMA_MAX_CONCURRENT=10      # Aumentado de 3  
OLLAMA_TIMEOUT=45             # Aumentado de 30
OLLAMA_CHUNK_SIZE=20          # Nuevo
OLLAMA_CACHE_ENABLED=true     # Mantener
OLLAMA_UNIFIED_MODE=true      # Nuevo - habilitar modo unificado
```

### **Límites recomendados:**
- **Términos pequeños (≤50):** Procesamiento síncrono unificado
- **Términos medianos (51-200):** Procesamiento asíncrono con chunks de 20
- **Términos grandes (>200):** Procesamiento asíncrono con chunks de 50

---

## 📋 PLAN DE IMPLEMENTACIÓN

### **PRIORIDAD ALTA:**
1. ✅ Implementar método unificado `translate_and_classify_unified_batch()`
2. ✅ Crear prompt unificado optimizado
3. ✅ Aumentar concurrencia a 10

### **PRIORIDAD MEDIA:**
4. ✅ Implementar procesamiento asíncrono completo
5. ✅ Crear sistema de caché de Excel pre-generado
6. ✅ Endpoint de descarga instantánea

### **PRIORIDAD BAJA:**
7. ✅ Optimizar frontend para mostrar progreso
8. ✅ Implementar chunks inteligentes
9. ✅ Métricas y monitoreo de rendimiento

---

## 🧪 TESTING REQUERIDO

### **Tests de rendimiento:**
```python
# test_unified_performance.py
def test_unified_vs_separate_calls()
def test_concurrent_processing_limits()
def test_cache_effectiveness()
def test_large_batch_processing()
```

### **Tests de funcionalidad:**
```python
# test_unified_functionality.py  
def test_unified_translation_accuracy()
def test_unified_classification_accuracy()
def test_json_response_parsing()
def test_error_handling()
```

---

**🎉 RESULTADO ESPERADO:** Una aplicación **3-4x más rápida** con descarga instantánea y mejor experiencia de usuario.