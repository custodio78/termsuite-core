# 🎯 Puntos de Mejora Priorizados

## ✅ Diseño Correcto (No Cambiar)

### Unificación TranslationService + DomainClassificationService
- **Estado actual**: ✅ Correcto
- **Razón**: El método `translate_and_classify_unified_batch` optimiza llamadas a Ollama haciendo ambas tareas en una sola petición
- **Beneficio**: Reduce latencia, coste computacional y número de llamadas a Ollama
- **Acción**: Mantener como está

---

## 🔴 Prioridad Alta (Impacto Alto, Esfuerzo Medio)

### 1. Refactorizar `main.py` en Routers Modulares

**Problema actual:**
- `main.py` tiene ~2135 líneas con todos los endpoints mezclados
- Difícil de mantener, testear y escalar
- Violación del principio de responsabilidad única

**Solución propuesta:**
```
app/
├── main.py                    # Solo configuración FastAPI y registro de routers
├── routers/
│   ├── __init__.py
│   ├── tmx.py                 # Endpoints de TMX
│   ├── corpus.py              # Endpoints de corpus
│   ├── ollama.py              # Endpoints de Ollama
│   ├── export.py              # Endpoints de exportación
│   └── status.py              # Endpoints de estado
```

**Beneficios:**
- Código más organizado y mantenible
- Facilita testing por módulo
- Permite escalar equipo trabajando en paralelo

**Esfuerzo estimado:** 2-3 horas

---

### 2. Arreglar Bug: Variable `domain_description` no definida

**Problema actual:**
En `export_tmx_to_excel` (línea ~990), se usa `domain_description` antes de cargarla:

```python
# Línea 990-994: Se usa domain_description pero aún no está definida
if (terms_for_excel and 
    'Relevancia Ámbito' not in terms_for_excel[0] and
    domain_description and  # ❌ Variable no definida aquí
    domain_description.strip() and
    ollama_translator.is_available()):
```

**Solución:**
Cargar `domain_description` ANTES de usarla (como se hace en línea 1090-1096):

```python
# Cargar domain_description PRIMERO
tmx_terms_path = file_handler.get_path("tmx", f"{tmx_id}_terms.json")
domain_description = None
if tmx_terms_path.exists():
    with open(tmx_terms_path, 'r', encoding='utf-8') as f:
        tmx_data = json.load(f)
    domain_description = tmx_data.get('domain_description') if isinstance(tmx_data, dict) else None

# AHORA sí usar domain_description
if (terms_for_excel and 
    'Relevancia Ámbito' not in terms_for_excel[0] and
    domain_description and domain_description.strip() and
    ollama_translator.is_available()):
```

**Esfuerzo estimado:** 15 minutos

---

### 3. Mejorar Manejo de Errores y Validación

**Problemas actuales:**
- Lecturas de JSON sin validación de estructura
- Errores de Ollama no siempre manejados correctamente
- Timeouts no configurados en todas las llamadas HTTP

**Mejoras propuestas:**

```python
# 1. Validar estructura de JSON antes de usar
def _validate_tmx_data(data: dict) -> bool:
    """Validar que el JSON tiene la estructura esperada"""
    required_keys = ['terms', 'frequencies', 'language']
    return all(key in data for key in required_keys)

# 2. Wrapper para llamadas HTTP con retry
async def _call_ollama_with_retry(self, payload: dict, max_retries: int = 3):
    """Llamar a Ollama con reintentos automáticos"""
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            if response.status_code == 200:
                return response.json()
        except requests.Timeout:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Backoff exponencial
                continue
            raise
    return None

# 3. Validar tamaño de archivos antes de procesar
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
if file.size > MAX_FILE_SIZE:
    raise HTTPException(status_code=413, detail="Archivo demasiado grande")
```

**Esfuerzo estimado:** 3-4 horas

---

## 🟡 Prioridad Media (Impacto Medio, Esfuerzo Medio)

### 4. Centralizar Configuración con Pydantic Settings

**Problema actual:**
- Variables de entorno esparcidas por el código
- Sin validación de valores
- Difícil de documentar y mantener

**Solución propuesta:**

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Ollama
    ollama_host: str = "192.168.0.88"
    ollama_port: int = 11434
    ollama_model: str = "llama3.2:latest"
    ollama_timeout: int = 30
    ollama_max_concurrent: int = 10
    ollama_cache_enabled: bool = True
    
    # TermSuite
    termsuite_jar: str = "/app/termsuite/termsuite-core-3.0.10.jar"
    java_opts: str = "-Xms1g -Xmx4g"
    
    # Límites
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    max_terms_per_batch: int = 100
    
    # Paths
    data_dir: Path = Path("/app/data")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

**Uso:**
```python
from app.config import settings

ollama_host = settings.ollama_host
```

**Esfuerzo estimado:** 1-2 horas

---

### 5. Implementar Logging Estructurado

**Problema actual:**
- Mezcla de `print()` y callbacks personalizados
- Sin niveles de log consistentes
- Difícil de filtrar y analizar

**Solución propuesta:**

```python
# app/utils/logger.py
import logging
from pathlib import Path

def setup_logger(name: str = "termsuite_api") -> logging.Logger:
    """Configurar logger estructurado"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Handler para archivo
    log_file = Path("data/logs/app.log")
    log_file.parent.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    # Formato estructurado
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Uso en servicios
logger = setup_logger()
logger.info("Procesando traducción", extra={"term": term, "lang": "es->en"})
```

**Esfuerzo estimado:** 2 horas

---

### 6. Factorizar Lógica Duplicada de Exportación

**Problema actual:**
- `export_tmx_to_excel` (síncrono) y `process_tmx_export` (asíncrono) tienen código duplicado
- Misma lógica de filtrado, ordenamiento y estructura de datos

**Solución propuesta:**

```python
# app/services/export_utils.py
def prepare_terms_for_excel(
    terms_list: List[str],
    frequencies: Dict[str, int],
    language: str,
    filters: Dict[str, Any]
) -> List[Dict]:
    """
    Función pura que prepara términos para Excel
    Reutilizable en ambos flujos (sync y async)
    """
    # Aplicar filtros
    # Ordenar
    # Crear estructura
    # Retornar lista de diccionarios
    pass

# Usar en ambos lugares
terms_for_excel = prepare_terms_for_excel(
    terms_list, frequencies, language, filters
)
```

**Esfuerzo estimado:** 2-3 horas

---

## 🟢 Prioridad Baja (Impacto Bajo, Esfuerzo Variable)

### 7. Agregar Tests Automatizados

**Cobertura sugerida:**
- Tests unitarios: `TMXParser`, `FileHandler`, lógica de filtrado
- Tests de integración: Endpoints principales con `TestClient`
- Tests de carga: Simular múltiples usuarios

**Esfuerzo estimado:** 4-6 horas

---

### 8. Mejorar Documentación de API

**Mejoras:**
- Agregar `description` y `summary` a todos los endpoints
- Documentar códigos de error posibles
- Ejemplos de request/response en docstrings

**Esfuerzo estimado:** 2 horas

---

### 9. Implementar Rate Limiting

**Para producción:**
- Limitar requests por IP/usuario
- Proteger endpoints costosos (Ollama, exportaciones)

**Esfuerzo estimado:** 2-3 horas

---

### 10. Migrar Estado de Jobs a Redis/DB

**Problema actual:**
- Estado en memoria se pierde al reiniciar
- No escala a múltiples instancias

**Solución:**
- Redis para estado temporal
- Base de datos para historial

**Esfuerzo estimado:** 4-6 horas

---

## 📊 Resumen de Prioridades

| Prioridad | Tarea | Impacto | Esfuerzo | ROI |
|-----------|-------|---------|----------|-----|
| 🔴 Alta | Refactorizar routers | Alto | Medio | ⭐⭐⭐⭐⭐ |
| 🔴 Alta | Arreglar bug domain_description | Alto | Bajo | ⭐⭐⭐⭐⭐ |
| 🔴 Alta | Mejorar manejo de errores | Alto | Medio | ⭐⭐⭐⭐ |
| 🟡 Media | Configuración centralizada | Medio | Bajo | ⭐⭐⭐⭐ |
| 🟡 Media | Logging estructurado | Medio | Bajo | ⭐⭐⭐ |
| 🟡 Media | Factorizar exportación | Medio | Medio | ⭐⭐⭐ |
| 🟢 Baja | Tests automatizados | Bajo | Alto | ⭐⭐ |
| 🟢 Baja | Documentación API | Bajo | Bajo | ⭐⭐ |
| 🟢 Baja | Rate limiting | Bajo | Medio | ⭐⭐ |
| 🟢 Baja | Redis para jobs | Bajo | Alto | ⭐ |

---

## 🚀 Plan de Implementación Sugerido

### Fase 1 (Semana 1): Bugs y Estabilidad
1. Arreglar bug `domain_description` (15 min)
2. Mejorar manejo de errores (3-4 horas)
3. Configuración centralizada (1-2 horas)

### Fase 2 (Semana 2): Refactoring
1. Refactorizar en routers (2-3 horas)
2. Factorizar lógica de exportación (2-3 horas)
3. Logging estructurado (2 horas)

### Fase 3 (Semana 3+): Mejoras Adicionales
1. Tests automatizados
2. Documentación mejorada
3. Rate limiting (si se necesita)

---

## 💡 Notas Finales

- **Mantener optimización unificada**: El diseño actual de `translate_and_classify_unified_batch` es correcto y eficiente
- **Enfoque incremental**: Implementar mejoras de forma gradual, probando cada cambio
- **Priorizar estabilidad**: Arreglar bugs antes de agregar nuevas features