# Guía de Pruebas

## Requisitos Previos

1. **Docker corriendo:**
   ```bash
   docker ps
   # Debe mostrar el contenedor termsuite-api
   ```

2. **Servidor accesible:**
   ```bash
   curl http://localhost:8000/api
   # Debe responder con JSON
   ```

3. **Python con requests:**
   ```bash
   pip install requests pandas openpyxl
   ```

## Pruebas Rápidas

### 1. Verificar Servidor

```bash
python test_server.py
```

**Resultado esperado:**
```
✓ Servidor funcionando correctamente
  Versión: 1.0.0
  Endpoints disponibles:
    - upload_tmx: /api/upload-tmx
    - upload_corpus: /api/upload-corpus
    ...
```

### 2. Prueba Completa de TMX

```bash
python test_tmx_extraction.py
```

**Resultado esperado:**
```
1. Subiendo TMX...
✓ TMX subido: abc123...

2. Obteniendo idiomas disponibles...
✓ Idiomas detectados: es, en

3. Extrayendo términos (modo directo)...
✓ 15 términos del idioma 'es' extraídos

4. Buscando término 'válvula'...
✓ ES: Encontrado (frecuencia: 4)
✗ EN: No encontrado

5. Exportando a Excel...
✓ Excel exportado: test_output_abc123.xlsx

6. Verificando contenido del Excel...
✓ Excel leído correctamente
  Filas: 15
  Columnas: Número, Término, Frecuencia, Longitud, Palabras, Idioma, Traducción, Tipo Match, Variantes

  Primeros 5 términos:
    1. válvula (4x) → valve | tap | faucet [3 variantes]
    2. elevador (4x) → elevator | lift [2 variantes]
    ...

✓ PRUEBA COMPLETADA EXITOSAMENTE
```

## Pruebas Manuales en la Interfaz Web

### Prueba 1: TMX de Glosario (Recomendado)

1. Abre http://localhost:8000
2. Click en "Seleccionar Archivo"
3. Elige: `examples/test_terms_glossary.tmx`
4. Click "Subir TMX"
5. Verás: "TMX multiidioma detectado: es, en"
6. Selecciona:
   - Idioma origen: Español (es)
   - Idioma traducción: English (en)
7. Click "Aplicar Idiomas"
8. Verás: "15 términos del idioma 'es' extraídos (traducción: en)"
9. Configura:
   - Frecuencia mínima: 1
   - ☑ Incluir traducciones
10. Click "Extraer Términos del TMX"
11. Descarga el Excel

**Verificar en Excel:**
- Columna "Traducción" con múltiples valores separados por ` | `
- Columna "Variantes" indicando número de traducciones
- Términos como "válvula" con 3 variantes: valve | tap | faucet

### Prueba 2: TMX con Segmentos + TermSuite

1. Abre http://localhost:8000
2. Sube: `examples/test_multiple_translations.tmx`
3. Selecciona idiomas: es → en
4. ☑ Marca "Extraer términos individuales con TermSuite"
5. Click "Aplicar Idiomas" (tardará unos segundos)
6. Verás términos individuales extraídos de las frases
7. Exporta a Excel

**Verificar:**
- Términos individuales como "válvula", "elevador", "bomba"
- No frases completas
- Frecuencias calculadas correctamente

### Prueba 3: Herramienta de Búsqueda

1. Después de subir un TMX
2. En el campo "Buscar término específico..."
3. Escribe: `válvula`
4. Presiona Enter o click "Buscar en TMX"
5. Aparece panel con resultados:
   - ✓ ES: Encontrado (frecuencia: 4)
   - ✗ EN: No encontrado

**Probar también:**
- Buscar "valve" → Encontrado en EN
- Buscar "xyz" → No encontrado en ningún idioma
- Buscar "bomba" → Ver coincidencias parciales

## Solución de Problemas

### Error: "No se puede conectar al servidor"

```bash
# Verificar que Docker está corriendo
docker ps

# Si no está corriendo, iniciar
docker-compose up -d

# Ver logs
docker logs termsuite-api -f
```

### Error: "TMX no encontrado"

- Verifica que el archivo existe en `examples/`
- Usa rutas relativas desde el directorio `termsuite-api/`

### Error: "TermSuite failed"

```bash
# Verificar que Java está disponible en el contenedor
docker exec termsuite-api java -version

# Verificar que el JAR existe
docker exec termsuite-api ls -la /app/termsuite/
```

### Excel vacío o sin traducciones

1. Verifica que marcaste ☑ "Incluir traducciones"
2. Verifica que aplicaste los idiomas con "Aplicar Idiomas"
3. Verifica que el TMX tiene ambos idiomas

## Pruebas Automatizadas

### Ejecutar todas las pruebas

```bash
# Prueba básica
python test_server.py

# Prueba completa
python test_tmx_extraction.py

# Responder 's' cuando pregunte por TermSuite
```

### Verificar archivos generados

```bash
# Listar archivos de prueba
ls -lh test_*.xlsx

# Ver contenido con pandas
python -c "import pandas as pd; df = pd.read_excel('test_output_*.xlsx'); print(df.head())"
```

## Limpieza

```bash
# Eliminar archivos de prueba
rm test_*.xlsx

# Limpiar uploads del servidor
docker exec termsuite-api rm -rf /app/uploads/*
```

## Casos de Prueba Específicos

### Caso 1: Término con 3 traducciones

**Buscar:** válvula  
**Esperado:** valve | tap | faucet  
**Variantes:** 3

### Caso 2: Término con variante regional

**Buscar:** elevador  
**Esperado:** elevator | lift  
**Variantes:** 2

### Caso 3: Término único

**Buscar:** plataforma  
**Esperado:** platform  
**Variantes:** 1

### Caso 4: Término con bullets

**Buscar:** depósito  
**Esperado:** "depósito" (sin "a)")  
**Limpieza:** ✓ Bullets eliminados

## Métricas de Éxito

✅ Servidor responde en < 1 segundo  
✅ TMX se sube correctamente  
✅ Idiomas se detectan automáticamente  
✅ Términos se extraen sin errores  
✅ Múltiples traducciones se muestran separadas por ` | `  
✅ Búsqueda encuentra términos correctamente  
✅ Excel se genera con todas las columnas  
✅ TermSuite extrae términos individuales (si está activado)  
✅ Limpieza de bullets funciona correctamente
