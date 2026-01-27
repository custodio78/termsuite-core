# Solución: Descarga Prematura de Excel

## Problema Identificado

El usuario reportó que "aparece para descargar el excel pero estoy viendo en el log del docker que todavía está trabajando". Esto indica que:

1. **El archivo Excel aparece para descarga antes de estar completamente procesado**
2. **El proceso sigue ejecutándose en segundo plano** (visible en logs de Docker)
3. **El archivo descargado puede estar incompleto o corrupto**

## Causa Raíz

El problema estaba en el endpoint síncrono `/api/export/tmx-excel/{tmx_id}` que:

- Procesaba clasificaciones de dominio con Ollama de forma síncrona
- Podía tardar mucho tiempo con archivos grandes
- El navegador recibía la respuesta de descarga antes de que el procesamiento terminara
- No había límites en el número de términos para descarga "rápida"

## Solución Implementada

### 1. Nuevo Endpoint de Verificación

```python
@app.get("/api/tmx/{tmx_id}/export-ready")
async def check_tmx_export_ready(tmx_id: str):
```

**Funcionalidad:**
- Verifica si un TMX está listo para descarga rápida
- Considera datos pre-procesados y número de términos
- Retorna recomendación: `fast`, `async`, o `basic`

### 2. Límite de Términos para Descarga Rápida

**Backend (`main.py`):**
```python
# LÍMITE: Solo procesar si hay 100 términos o menos
if (domain_description and domain_description.strip() and ollama_translator.is_available() 
    and len(terms_for_excel) <= 100):
```

**Frontend (`app_v2.js`):**
```javascript
if (readyData.ready_for_fast_download && state.config.includeTranslations) {
    // FLUJO RÁPIDO: ≤100 términos
} else {
    // FLUJO ASÍNCRONO: >100 términos
}
```

### 3. Lógica de Decisión Mejorada

| Condición | Flujo | Razón |
|-----------|-------|-------|
| ≤100 términos + datos pre-procesados | **Rápido** | Descarga inmediata |
| >100 términos | **Asíncrono** | Evita bloqueos |
| Clasificación de dominio + >100 términos | **Asíncrono** | Procesamiento pesado |
| Sin datos pre-procesados | **Asíncrono** | Requiere procesamiento |

### 4. Mensajes de Estado Informativos

```javascript
const reason = readyData.total_terms > 100 ? 
    `Procesando ${readyData.total_terms} términos (>100)` : 
    readyData.needs_domain_processing ? 
    'Clasificando términos por ámbito' :
    'Preparando traducciones';
```

## Archivos Modificados

### Backend
- **`app/main.py`**:
  - Nuevo endpoint `/api/tmx/{tmx_id}/export-ready`
  - Límite de 100 términos para clasificación de dominio síncrona
  - Mensajes informativos mejorados

### Frontend
- **`app/static/js/app_v2.js`**:
  - Lógica de decisión basada en número de términos
  - Uso del nuevo endpoint de verificación
  - Mensajes de progreso más informativos

### Testing
- **`test_download_fix.py`**: Script de prueba para verificar la solución

## Beneficios de la Solución

### ✅ Problema Resuelto
- **No más descargas prematuras**: El Excel solo aparece cuando está completamente listo
- **Progreso visible**: El usuario ve el progreso real del procesamiento
- **Archivos completos**: No más archivos corruptos o incompletos

### ✅ Rendimiento Optimizado
- **Descarga rápida para archivos pequeños** (≤100 términos)
- **Procesamiento asíncrono para archivos grandes** (>100 términos)
- **Clasificación de dominio optimizada**

### ✅ Experiencia de Usuario Mejorada
- **Mensajes informativos**: El usuario sabe qué está pasando
- **Tiempo estimado**: Progreso visible en tiempo real
- **Decisión automática**: El sistema elige el mejor flujo

## Cómo Probar la Solución

1. **Ejecutar el script de prueba:**
   ```bash
   cd termsuite-api
   python test_download_fix.py
   ```

2. **Probar con archivo pequeño (≤100 términos):**
   - Debería usar descarga rápida
   - Excel aparece inmediatamente cuando está listo

3. **Probar con archivo grande (>100 términos):**
   - Debería usar descarga asíncrona
   - Muestra progreso en tiempo real
   - Excel aparece solo cuando está completamente procesado

## Monitoreo

Para verificar que la solución funciona:

1. **Logs de Docker**: Ya no deberían mostrar procesamiento después de iniciar descarga
2. **Interfaz web**: Muestra progreso real y mensajes informativos
3. **Archivos descargados**: Siempre completos y correctos

## Configuración Recomendada

- **Archivos pequeños**: Usar descarga rápida (automático)
- **Archivos grandes**: Usar descarga asíncrona (automático)
- **Con clasificación de dominio**: Preferir descarga asíncrona
- **Sin Ollama**: Descarga básica sin traducciones

---

**Estado**: ✅ **SOLUCIONADO**  
**Fecha**: 2026-01-04  
**Impacto**: Alto - Mejora significativa en experiencia de usuario