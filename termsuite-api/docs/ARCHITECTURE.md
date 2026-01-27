# 🏗️ Arquitectura de TermSuite API

## 📁 Estructura del Proyecto

```
termsuite-api/
├── app/                          # Aplicación FastAPI
│   ├── __init__.py
│   ├── main.py                   # Endpoints y lógica principal
│   ├── models.py                 # Modelos Pydantic
│   ├── services/                 # Servicios de negocio
│   │   ├── termsuite.py         # Wrapper de TermSuite JAR
│   │   ├── tmx_parser.py        # Parser de memorias TMX
│   │   └── excel_export.py      # Exportador a Excel
│   └── utils/                    # Utilidades
│       └── file_handler.py      # Manejo de archivos
├── data/                         # Datos persistentes (volumen)
│   ├── uploads/                 # Archivos subidos
│   │   ├── tmx/                # Memorias TMX
│   │   └── corpus/             # Corpus de texto
│   ├── corpus/                  # Corpus procesados
│   └── outputs/                 # Resultados (JSON, Excel)
├── termsuite/                    # JAR de TermSuite
│   └── termsuite-core-3.0.10.jar
├── examples/                     # Archivos de ejemplo
│   ├── sample_corpus.txt
│   └── sample_memory.tmx
├── Dockerfile                    # Imagen Docker
├── docker-compose.yml           # Orquestación
├── requirements.txt             # Dependencias Python
├── start.sh / start.bat         # Scripts de inicio
├── test_api.py                  # Tests automatizados
├── client_example.py            # Cliente Python de ejemplo
├── README.md                    # Documentación principal
├── QUICKSTART.md               # Guía rápida
└── ARCHITECTURE.md             # Este archivo
```

## 🔄 Flujo de Trabajo

```
┌─────────────┐
│   Cliente   │
│ (Browser/   │
│  Python/    │
│  curl)      │
└──────┬──────┘
       │
       │ HTTP Request
       ▼
┌─────────────────────────────────────────┐
│         FastAPI Application             │
│  ┌───────────────────────────────────┐  │
│  │         main.py (Endpoints)       │  │
│  │  • POST /api/upload-tmx          │  │
│  │  • POST /api/upload-corpus       │  │
│  │  • POST /api/extract             │  │
│  │  • GET  /api/status/{job_id}     │  │
│  │  • GET  /api/export/excel/{id}   │  │
│  └───────────────┬───────────────────┘  │
│                  │                       │
│  ┌───────────────▼───────────────────┐  │
│  │         Services Layer            │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │  TermSuiteService           │  │  │
│  │  │  • Ejecuta JAR              │  │  │
│  │  │  • Procesa corpus           │  │  │
│  │  └─────────────────────────────┘  │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │  TMXParser                  │  │  │
│  │  │  • Parsea archivos TMX      │  │  │
│  │  │  • Extrae términos          │  │  │
│  │  └─────────────────────────────┘  │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │  ExcelExporter              │  │  │
│  │  │  • Genera archivos Excel    │  │  │
│  │  │  • Aplica formato           │  │  │
│  │  └─────────────────────────────┘  │  │
│  └─────────────────────────────────┘  │
│                  │                       │
│  ┌───────────────▼───────────────────┐  │
│  │         Utils Layer               │  │
│  │  • FileHandler (gestión archivos) │  │
│  └───────────────────────────────────┘  │
└──────────────┬──────────────────────────┘
               │
               │ Subprocess call
               ▼
┌─────────────────────────────────────────┐
│         TermSuite JAR (Java)            │
│  • Preprocesamiento NLP                 │
│  • Extracción de términos               │
│  • Cálculo de métricas                  │
│  • Exportación a JSON                   │
└─────────────────────────────────────────┘
```

## 🔌 API Endpoints

### 1. Upload TMX
```
POST /api/upload-tmx
├── Input: Archivo TMX (multipart/form-data)
├── Process:
│   ├── Guardar archivo
│   ├── Parsear XML
│   └── Extraer términos
└── Output: file_id, términos encontrados
```

### 2. Upload Corpus
```
POST /api/upload-corpus
├── Input: Archivo TXT o ZIP (multipart/form-data)
├── Process:
│   ├── Guardar archivo
│   └── Extraer ZIP si aplica
└── Output: corpus_id
```

### 3. Extract Terms
```
POST /api/extract
├── Input: corpus_id, language, min_frequency, tmx_id (JSON)
├── Process (Background Task):
│   ├── Validar corpus y TMX
│   ├── Ejecutar TermSuite JAR
│   ├── Procesar resultados JSON
│   ├── Filtrar con TMX (opcional)
│   └── Generar Excel
└── Output: job_id
```

### 4. Get Status
```
GET /api/status/{job_id}
├── Input: job_id (path parameter)
├── Process:
│   └── Consultar estado en memoria
└── Output: status, progress, message, result_file
```

### 5. Export Excel
```
GET /api/export/excel/{job_id}
├── Input: job_id (path parameter)
├── Process:
│   └── Leer archivo Excel del disco
└── Output: Archivo Excel (download)
```

## 🗄️ Almacenamiento de Estado

### En Memoria (jobs dict)
```python
jobs = {
    "job-uuid-123": {
        "status": "completed",
        "progress": 100,
        "message": "Extracción completada",
        "result_file": "job-uuid-123.xlsx",
        "request": {...}
    }
}
```

**Nota:** En producción, usar Redis o base de datos.

### En Disco (volumen Docker)
```
data/
├── uploads/
│   ├── tmx/
│   │   ├── tmx-uuid-1.tmx
│   │   └── tmx-uuid-1_terms.json
│   └── corpus/
│       ├── corpus-uuid-1.txt
│       └── corpus-uuid-2.zip
├── corpus/
│   └── corpus-uuid-1/
│       ├── doc1.txt
│       └── doc2.txt
└── outputs/
    ├── job-uuid-1.json
    └── job-uuid-1.xlsx
```

## 🐳 Docker

### Imagen Base
- `python:3.9-slim`
- OpenJDK 11 (para ejecutar TermSuite JAR)

### Volúmenes
- `./data:/app/data` - Datos persistentes
- `./termsuite:/app/termsuite` - JAR de TermSuite

### Variables de Entorno
- `TERMSUITE_JAR` - Ruta al JAR
- `DATA_DIR` - Directorio de datos
- `JAVA_OPTS` - Opciones de JVM

## 🔐 Seguridad

### Consideraciones Actuales
- ✅ Validación de tipos de archivo
- ✅ Límites de tamaño implícitos
- ⚠️ Sin autenticación (desarrollo)
- ⚠️ Sin rate limiting

### Para Producción
- [ ] Agregar autenticación (JWT/OAuth)
- [ ] Implementar rate limiting
- [ ] Validar y sanitizar inputs
- [ ] Usar HTTPS
- [ ] Agregar logging de auditoría
- [ ] Implementar timeouts
- [ ] Limitar tamaño de archivos explícitamente

## 📊 Escalabilidad

### Limitaciones Actuales
- Estado en memoria (no distribuido)
- Procesamiento síncrono por job
- Sin cola de trabajos

### Mejoras Futuras
- Redis para estado compartido
- Celery para cola de trabajos
- Múltiples workers
- Load balancer
- Almacenamiento en S3/MinIO

## 🧪 Testing

### Test Manual
```bash
python test_api.py corpus.txt memoria.tmx
```

### Test Automatizado
```bash
pytest tests/
```

### Test de Carga
```bash
locust -f locustfile.py
```

## 📝 Logging

### Niveles
- INFO: Operaciones normales
- WARNING: Situaciones inusuales
- ERROR: Errores recuperables
- CRITICAL: Errores fatales

### Ubicación
- Stdout/Stderr (capturado por Docker)
- `docker-compose logs -f`

## 🔄 Ciclo de Vida de un Job

```
1. Cliente sube corpus
   └─> corpus_id generado

2. Cliente inicia extracción
   └─> job_id generado
   └─> Estado: PENDING

3. Background task inicia
   └─> Estado: PROCESSING (10%)
   └─> Ejecuta TermSuite JAR
   └─> Estado: PROCESSING (70%)
   └─> Genera Excel
   └─> Estado: PROCESSING (90%)
   └─> Estado: COMPLETED (100%)

4. Cliente descarga Excel
   └─> Archivo servido desde disco
```

## 🛠️ Mantenimiento

### Limpieza de Archivos
```python
# Implementado en FileHandler
file_handler.cleanup_old_files(days=7)
```

### Monitoreo
- Logs de Docker
- Métricas de uso de disco
- Tiempo de procesamiento por job

## 📚 Dependencias Principales

| Librería | Versión | Propósito |
|----------|---------|-----------|
| FastAPI | 0.104.1 | Framework web |
| Uvicorn | 0.24.0 | Servidor ASGI |
| Pydantic | 2.5.0 | Validación de datos |
| openpyxl | 3.1.2 | Generación de Excel |
| pandas | 2.1.3 | Manipulación de datos |
| lxml | 4.9.3 | Parsing XML/TMX |
