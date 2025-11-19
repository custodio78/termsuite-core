# 🚀 Guía de Inicio Rápido

## Paso 1: Preparar el Entorno

### Windows
```cmd
cd termsuite-api
start.bat
```

### Linux/Mac
```bash
cd termsuite-api
chmod +x start.sh
./start.sh
```

## Paso 2: Colocar el JAR de TermSuite

1. Descarga o compila `termsuite-core-3.0.10.jar`
2. Colócalo en la carpeta `termsuite/`

```
termsuite-api/
└── termsuite/
    └── termsuite-core-3.0.10.jar  ← Aquí
```

## Paso 3: Iniciar la API

```bash
docker-compose up -d
```

Verifica que esté funcionando:
```bash
curl http://localhost:8000
```

## Paso 4: Usar la API

### Opción A: Interfaz Web (Swagger)

Abre en tu navegador:
```
http://localhost:8000/docs
```

Desde ahí puedes probar todos los endpoints interactivamente.

### Opción B: Línea de Comandos (curl)

**1. Subir corpus:**
```bash
curl -X POST "http://localhost:8000/api/upload-corpus" \
  -F "file=@mi_corpus.txt"
```

Respuesta:
```json
{
  "file_id": "abc-123-def",
  "filename": "mi_corpus.txt",
  "size": 12345,
  "message": "Corpus subido exitosamente"
}
```

**2. Extraer términos:**
```bash
curl -X POST "http://localhost:8000/api/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "corpus_id": "abc-123-def",
    "language": "en",
    "min_frequency": 2
  }'
```

Respuesta:
```json
{
  "job_id": "xyz-789-uvw",
  "status": "pending",
  "message": "Extracción iniciada"
}
```

**3. Consultar estado:**
```bash
curl "http://localhost:8000/api/status/xyz-789-uvw"
```

**4. Descargar Excel:**
```bash
curl -O "http://localhost:8000/api/export/excel/xyz-789-uvw"
```

### Opción C: Script Python

```bash
python client_example.py
```

O usa el script de prueba:
```bash
python test_api.py mi_corpus.txt
```

## Paso 5: Con Memoria TMX

**1. Subir TMX:**
```bash
curl -X POST "http://localhost:8000/api/upload-tmx" \
  -F "file=@memoria.tmx"
```

**2. Extraer con TMX:**
```bash
curl -X POST "http://localhost:8000/api/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "corpus_id": "abc-123-def",
    "language": "en",
    "min_frequency": 2,
    "use_tmx": true,
    "tmx_id": "tmx-456-ghi"
  }'
```

## 📊 Resultado

El archivo Excel contendrá:

| Término | Patrón | Frecuencia | Frec. Documentos | Especificidad | En TMX |
|---------|--------|------------|------------------|---------------|--------|
| machine learning | N N | 45 | 12 | 0.8523 | Sí |
| neural network | A N | 32 | 8 | 0.7891 | No |
| ... | ... | ... | ... | ... | ... |

## 🛠️ Comandos Útiles

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Reiniciar servicio
docker-compose restart

# Detener servicio
docker-compose down

# Ver estado
docker-compose ps

# Limpiar todo
docker-compose down -v
```

## ❓ Problemas Comunes

### Puerto 8000 ocupado
Edita `docker-compose.yml`:
```yaml
ports:
  - "8080:8000"  # Cambiar a 8080
```

### Sin memoria Java
Edita `docker-compose.yml`:
```yaml
environment:
  - JAVA_OPTS=-Xms2g -Xmx8g  # Aumentar memoria
```

### JAR no encontrado
```bash
# Verificar
ls -la termsuite/termsuite-core-3.0.10.jar

# Si no existe, compilar desde el proyecto original
cd ../
gradle clean jar
cp build/libs/termsuite-core-3.0.10.jar termsuite-api/termsuite/
```

## 🎯 Próximos Pasos

- Lee el [README.md](README.md) completo
- Explora la [documentación interactiva](http://localhost:8000/docs)
- Revisa [client_example.py](client_example.py) para integración Python
- Ejecuta [test_api.py](test_api.py) para pruebas automatizadas
