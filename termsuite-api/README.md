# TermSuite API

API REST para extracción terminológica usando TermSuite con soporte para memorias TMX y exportación a Excel.

## 🚀 Inicio Rápido

### Prerequisitos

- Docker y Docker Compose instalados
- Archivo JAR de TermSuite (`termsuite-core-3.0.10.jar`)

### Instalación

1. **Clonar o copiar el proyecto**

2. **Colocar el JAR de TermSuite**
   ```bash
   mkdir -p termsuite
   # Copiar termsuite-core-3.0.10.jar a la carpeta termsuite/
   ```

3. **Construir y ejecutar**
   ```bash
   docker-compose up --build
   ```

4. **Acceder a la API**
   - API: http://localhost:8000
   - Documentación interactiva: http://localhost:8000/docs
   - Documentación alternativa: http://localhost:8000/redoc

## 📡 Endpoints

### 1. Subir Memoria TMX
```bash
POST /api/upload-tmx
Content-Type: multipart/form-data

# Extraer términos de un idioma específico
curl -X POST "http://localhost:7000/api/upload-tmx?language=en" \
  -F "file=@memoria.tmx"

# O extraer todos los términos (sin filtro de idioma)
curl -X POST "http://localhost:7000/api/upload-tmx" \
  -F "file=@memoria.tmx"
```

**Parámetros:**
- `file`: Archivo TMX (requerido)
- `language`: Código de idioma (opcional: en, es, fr, de, it, pt, etc.)

**Respuesta:**
```json
{
  "file_id": "uuid-del-archivo",
  "filename": "memoria.tmx",
  "size": 12345,
  "message": "TMX subido exitosamente. 150 términos del idioma 'en' encontrados."
}
```

### 2. Subir Corpus
```bash
POST /api/upload-corpus
Content-Type: multipart/form-data

curl -X POST "http://localhost:8000/api/upload-corpus" \
  -F "file=@corpus.txt"
# o
curl -X POST "http://localhost:8000/api/upload-corpus" \
  -F "file=@corpus.zip"
```

**Respuesta:**
```json
{
  "file_id": "uuid-del-corpus",
  "filename": "corpus.txt",
  "size": 54321,
  "message": "Corpus subido exitosamente"
}
```

### 3. Extraer Términos
```bash
POST /api/extract
Content-Type: application/json

curl -X POST "http://localhost:8000/api/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "corpus_id": "uuid-del-corpus",
    "language": "en",
    "min_frequency": 2,
    "use_tmx": true,
    "tmx_id": "uuid-del-tmx"
  }'
```

**Respuesta:**
```json
{
  "job_id": "uuid-del-trabajo",
  "status": "pending",
  "message": "Extracción iniciada"
}
```

### 4. Consultar Estado
```bash
GET /api/status/{job_id}

curl "http://localhost:8000/api/status/uuid-del-trabajo"
```

**Respuesta:**
```json
{
  "job_id": "uuid-del-trabajo",
  "status": "completed",
  "progress": 100,
  "message": "Extracción completada",
  "result_file": "uuid-del-trabajo.xlsx"
}
```

### 5. Descargar Excel
```bash
GET /api/export/excel/{job_id}

curl -O "http://localhost:8000/api/export/excel/uuid-del-trabajo"
```

## 🔧 Configuración

### Variables de Entorno

Editar `docker-compose.yml`:

```yaml
environment:
  - TERMSUITE_JAR=/app/termsuite/termsuite-core-3.0.10.jar
  - DATA_DIR=/app/data
  - JAVA_OPTS=-Xms1g -Xmx4g
```

### Volúmenes

```yaml
volumes:
  - ./data:/app/data              # Datos persistentes
  - ./termsuite:/app/termsuite    # JAR de TermSuite
```

## 📊 Formato de Salida Excel

El archivo Excel generado contiene:

| Columna | Descripción |
|---------|-------------|
| Término | Término extraído |
| Patrón | Patrón sintáctico |
| Frecuencia | Número de ocurrencias |
| Frec. Documentos | Documentos donde aparece |
| Especificidad | Medida de especificidad |
| En TMX | Si está en la memoria TMX |
| Palabras | Palabras que componen el término |

## 🐛 Troubleshooting

### Error: JAR no encontrado
```bash
# Verificar que el JAR existe
ls -la termsuite/termsuite-core-3.0.10.jar
```

### Error: Sin memoria Java
```bash
# Aumentar memoria en docker-compose.yml
JAVA_OPTS=-Xms2g -Xmx8g
```

### Ver logs
```bash
docker-compose logs -f
```

## 📝 Ejemplo Completo

```python
import requests

# 1. Subir TMX
with open('memoria.tmx', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/upload-tmx',
        files={'file': f}
    )
    tmx_id = response.json()['file_id']

# 2. Subir Corpus
with open('corpus.txt', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/upload-corpus',
        files={'file': f}
    )
    corpus_id = response.json()['file_id']

# 3. Extraer términos
response = requests.post(
    'http://localhost:8000/api/extract',
    json={
        'corpus_id': corpus_id,
        'language': 'en',
        'min_frequency': 2,
        'use_tmx': True,
        'tmx_id': tmx_id
    }
)
job_id = response.json()['job_id']

# 4. Esperar y descargar
import time
while True:
    status = requests.get(f'http://localhost:8000/api/status/{job_id}').json()
    if status['status'] == 'completed':
        break
    time.sleep(5)

# 5. Descargar Excel
response = requests.get(f'http://localhost:8000/api/export/excel/{job_id}')
with open('resultados.xlsx', 'wb') as f:
    f.write(response.content)
```

## 📄 Licencia

Apache 2.0
