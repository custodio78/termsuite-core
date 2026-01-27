# 📚 Uso de Memorias TMX

## ¿Qué es TMX?

TMX (Translation Memory eXchange) es un formato estándar XML para intercambiar memorias de traducción entre diferentes herramientas CAT (Computer-Assisted Translation).

## Extracción de Términos por Idioma

La API permite extraer términos de un idioma específico de tu memoria TMX.

### Ejemplo de TMX

```xml
<?xml version="1.0" encoding="UTF-8"?>
<tmx version="1.4">
  <body>
    <tu>
      <tuv xml:lang="en-US">
        <seg>machine learning</seg>
      </tuv>
      <tuv xml:lang="es-ES">
        <seg>aprendizaje automático</seg>
      </tuv>
    </tu>
  </body>
</tmx>
```

## Uso de la API

### 1. Subir TMX con Idioma Específico

```bash
# Extraer solo términos en inglés
curl -X POST "http://localhost:7000/api/upload-tmx?language=en" \
  -F "file=@memoria.tmx"

# Extraer solo términos en español
curl -X POST "http://localhost:7000/api/upload-tmx?language=es" \
  -F "file=@memoria.tmx"

# Extraer solo términos en francés
curl -X POST "http://localhost:7000/api/upload-tmx?language=fr" \
  -F "file=@memoria.tmx"
```

### 2. Subir TMX sin Filtro de Idioma

```bash
# Extraer todos los términos (todos los idiomas)
curl -X POST "http://localhost:7000/api/upload-tmx" \
  -F "file=@memoria.tmx"
```

## Códigos de Idioma Soportados

La API reconoce códigos de idioma estándar ISO 639-1:

| Código | Idioma | Variantes Aceptadas |
|--------|--------|---------------------|
| `en` | Inglés | en-US, en-GB, en-CA |
| `es` | Español | es-ES, es-MX, es-AR |
| `fr` | Francés | fr-FR, fr-CA |
| `de` | Alemán | de-DE, de-AT, de-CH |
| `it` | Italiano | it-IT |
| `pt` | Portugués | pt-PT, pt-BR |
| `zh` | Chino | zh-CN, zh-TW |
| `ja` | Japonés | ja-JP |
| `ru` | Ruso | ru-RU |

**Nota:** El parser es flexible y acepta tanto códigos simples (`en`) como variantes regionales (`en-US`).

## Flujo de Trabajo Completo

### Escenario: Traducción Técnica EN → ES

```python
import requests

BASE_URL = "http://localhost:7000"

# 1. Subir TMX extrayendo términos en español
with open('memoria_tecnica.tmx', 'rb') as f:
    response = requests.post(
        f"{BASE_URL}/api/upload-tmx",
        files={'file': f},
        params={'language': 'es'}  # Solo términos en español
    )
tmx_id = response.json()['file_id']
print(f"TMX subido: {tmx_id}")

# 2. Subir corpus en español
with open('corpus_tecnico.txt', 'rb') as f:
    response = requests.post(
        f"{BASE_URL}/api/upload-corpus",
        files={'file': f}
    )
corpus_id = response.json()['file_id']

# 3. Extraer términos del corpus
response = requests.post(
    f"{BASE_URL}/api/extract",
    json={
        'corpus_id': corpus_id,
        'language': 'es',
        'min_frequency': 2,
        'use_tmx': True,
        'tmx_id': tmx_id
    }
)
job_id = response.json()['job_id']

# 4. Esperar y descargar Excel
# El Excel marcará qué términos ya están en tu memoria TMX
```

## Resultado en Excel

El archivo Excel generado incluirá una columna **"En TMX"**:

| Término | Frecuencia | En TMX |
|---------|------------|--------|
| aprendizaje automático | 45 | **Sí** ✅ |
| red neuronal | 32 | No |
| inteligencia artificial | 28 | **Sí** ✅ |
| procesamiento de datos | 15 | No |

Esto te permite identificar rápidamente:
- ✅ Términos que ya tienes traducidos en tu memoria
- ❌ Términos nuevos que necesitas traducir

## Casos de Uso

### 1. Identificar Términos Faltantes
```bash
# Extraer términos del idioma origen
curl -X POST "http://localhost:7000/api/upload-tmx?language=en" \
  -F "file=@memoria.tmx"

# Extraer términos del corpus
# Los términos NO marcados en TMX son los que faltan traducir
```

### 2. Validar Consistencia Terminológica
```bash
# Extraer términos del idioma destino
curl -X POST "http://localhost:7000/api/upload-tmx?language=es" \
  -F "file=@memoria.tmx"

# Comparar con términos extraídos del corpus
# Identificar variaciones o inconsistencias
```

### 3. Análisis Multilingüe
```bash
# Subir TMX para idioma A
curl -X POST "http://localhost:7000/api/upload-tmx?language=en" \
  -F "file=@memoria.tmx"

# Subir TMX para idioma B (mismo archivo, diferente idioma)
curl -X POST "http://localhost:7000/api/upload-tmx?language=es" \
  -F "file=@memoria.tmx"

# Comparar cobertura terminológica en ambos idiomas
```

## Formato TMX Soportado

### Versiones
- TMX 1.4 (recomendado)
- TMX 1.1, 1.2, 1.3 (compatibles)

### Estructura Mínima
```xml
<?xml version="1.0" encoding="UTF-8"?>
<tmx version="1.4">
  <header 
    creationtool="Tool" 
    srclang="en-US" 
    datatype="plaintext"/>
  <body>
    <tu>
      <tuv xml:lang="en-US">
        <seg>source term</seg>
      </tuv>
      <tuv xml:lang="es-ES">
        <seg>término destino</seg>
      </tuv>
    </tu>
  </body>
</tmx>
```

### Atributos de Idioma Reconocidos
- `xml:lang="en-US"` (estándar XML)
- `lang="en-US"` (alternativo)

## Solución de Problemas

### Error: "No se encontraron términos"
**Causa:** El idioma especificado no existe en el TMX.

**Solución:**
```bash
# Verificar qué idiomas tiene tu TMX
# Subir sin filtro de idioma primero
curl -X POST "http://localhost:7000/api/upload-tmx" \
  -F "file=@memoria.tmx"
```

### Error: "Error al parsear TMX"
**Causa:** Archivo TMX corrupto o formato inválido.

**Solución:**
1. Validar XML: https://www.xmlvalidation.com/
2. Verificar encoding UTF-8
3. Revisar estructura TMX

### Términos Duplicados
**Comportamiento:** La API elimina duplicados automáticamente.

**Ejemplo:**
```
Input TMX:  ["machine learning", "machine learning", "AI"]
Output:     ["AI", "machine learning"]  # Ordenado y sin duplicados
```

## Mejores Prácticas

1. **Especifica siempre el idioma** cuando trabajes con TMX multilingües
2. **Usa códigos ISO estándar** (en, es, fr, etc.)
3. **Valida tu TMX** antes de subirlo
4. **Mantén encoding UTF-8** para caracteres especiales
5. **Documenta el idioma** usado en cada extracción

## Integración con Herramientas CAT

### SDL Trados
```bash
# Exportar TMX desde Trados
# File → Export → Translation Memory → TMX

# Subir a la API
curl -X POST "http://localhost:7000/api/upload-tmx?language=es" \
  -F "file=@trados_export.tmx"
```

### memoQ
```bash
# Exportar TMX desde memoQ
# Translation Memories → Export → TMX 1.4

# Subir a la API
curl -X POST "http://localhost:7000/api/upload-tmx?language=fr" \
  -F "file=@memoq_export.tmx"
```

### OmegaT
```bash
# TMX se genera automáticamente en /omegat/project_save.tmx

# Subir a la API
curl -X POST "http://localhost:7000/api/upload-tmx?language=de" \
  -F "file=@project_save.tmx"
```

## API Reference

### Endpoint
```
POST /api/upload-tmx
```

### Parámetros
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `file` | File | Sí | Archivo TMX |
| `language` | String | No | Código de idioma (en, es, fr, etc.) |

### Respuesta
```json
{
  "file_id": "uuid",
  "filename": "memoria.tmx",
  "size": 12345,
  "message": "TMX subido exitosamente. 150 términos del idioma 'es' encontrados."
}
```

### Códigos de Estado
- `200`: Éxito
- `400`: Error en el archivo o formato
- `500`: Error del servidor
