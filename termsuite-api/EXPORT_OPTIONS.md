# 📊 Opciones de Exportación TMX

Guía completa de todas las opciones disponibles para exportar términos de memorias TMX.

## 🎯 Endpoint

```
GET /api/export/tmx-excel/{tmx_id}
```

## 📋 Parámetros Disponibles

### 1. Filtros de Frecuencia

#### `min_frequency` (integer)
Frecuencia mínima de aparición del término.

```bash
# Solo términos que aparecen 5 o más veces
curl -O "http://localhost:7000/api/export/tmx-excel/TMX_ID?min_frequency=5"
```

#### `top_n` (integer)
Limitar a los N términos más frecuentes.

```bash
# Top 100 términos más frecuentes
curl -O "http://localhost:7000/api/export/tmx-excel/TMX_ID?top_n=100"
```

### 2. Filtros de Palabras

#### `min_words` (integer)
Mínimo número de palabras que debe tener el término.

```bash
# Solo términos con 2 o más palabras
curl -O "http://localhost:7000/api/export/tmx-excel/TMX_ID?min_words=2"
```

#### `max_words` (integer)
Máximo número de palabras que puede tener el término.

```bash
# Solo términos con máximo 3 palabras
curl -O "http://localhost:7000/api/export/tmx-excel/TMX_ID?max_words=3"
```

**Combinación:**
```bash
# Términos de 2 a 4 palabras
curl -O "http://localhost:7000/api/export/tmx-excel/TMX_ID?min_words=2&max_words=4"
```

### 3. Ordenamiento

#### `sort_by` (string)
Campo por el cual ordenar. Opciones:
- `frequency` (por defecto)
- `alphabetical`
- `length`
- `words`

#### `sort_order` (string)
Orden de clasificación:
- `desc` (descendente, por defecto)
- `asc` (ascendente)

```bash
# Ordenar alfabéticamente A-Z
curl -O "http://localhost:7000/api/export/tmx-excel/TMX_ID?sort_by=alphabetical&sort_order=asc"

# Ordenar por longitud (más largos primero)
curl -O "http://localhost:7000/api/export/tmx-excel/TMX_ID?sort_by=length&sort_order=desc"

# Ordenar por número de palabras
curl -O "http://localhost:7000/api/export/tmx-excel/TMX_ID?sort_by=words&sort_order=asc"
```

### 4. Formato de Salida

#### `format` (string)
Formato del archivo de salida:
- `excel` (por defecto) - Archivo .xlsx
- `csv` - Archivo CSV
- `json` - Archivo JSON

```bash
# Exportar a CSV
curl -O "http://localhost:7000/api/export/tmx-excel/TMX_ID?format=csv"

# Exportar a JSON
curl -O "http://localhost:7000/api/export/tmx-excel/TMX_ID?format=json"
```

### 5. Selección de Columnas

#### `columns` (string)
Columnas a incluir (separadas por coma).

Columnas disponibles:
- `number` - Número de orden
- `term` - Término
- `frequency` - Frecuencia
- `length` - Longitud en caracteres
- `words` - Número de palabras
- `language` - Idioma
- `translation` - Traducción (si está disponible)

```bash
# Solo término y frecuencia
curl -O "http://localhost:7000/api/export/tmx-excel/TMX_ID?columns=term,frequency"

# Término, frecuencia y traducción
curl -O "http://localhost:7000/api/export/tmx-excel/TMX_ID?columns=term,frequency,translation&include_translation=true"
```

### 6. Filtros de Contenido

#### `exclude_numbers` (boolean)
Excluir términos que contengan números.

```bash
# Excluir términos con números
curl -O "http://localhost:7000/api/export/tmx-excel/TMX_ID?exclude_numbers=true"
```

#### `contains` (string)
Filtrar solo términos que contengan este texto.

```bash
# Solo términos que contengan "máquina"
curl -O "http://localhost:7000/api/export/tmx-excel/TMX_ID?contains=máquina"

# Solo términos que contengan "sistema"
curl -O "http://localhost:7000/api/export/tmx-excel/TMX_ID?contains=sistema"
```

### 7. Traducción

#### `include_translation` (boolean)
Incluir columna de traducción (si el TMX tiene pares bilingües).

```bash
# Incluir traducción
curl -O "http://localhost:7000/api/export/tmx-excel/TMX_ID?include_translation=true"
```

## 🎨 Ejemplos de Uso Combinado

### Ejemplo 1: Términos Técnicos Frecuentes
```bash
# Top 50 términos con 2+ palabras, sin números, ordenados por frecuencia
curl -O "http://localhost:7000/api/export/tmx-excel/TMX_ID?\
top_n=50&\
min_words=2&\
exclude_numbers=true&\
sort_by=frequency&\
sort_order=desc"
```

### Ejemplo 2: Glosario Alfabético
```bash
# Todos los términos ordenados alfabéticamente en CSV
curl -O "http://localhost:7000/api/export/tmx-excel/TMX_ID?\
format=csv&\
sort_by=alphabetical&\
sort_order=asc"
```

### Ejemplo 3: Términos Compuestos
```bash
# Términos de 3-5 palabras, frecuentes, con traducción
curl -O "http://localhost:7000/api/export/tmx-excel/TMX_ID?\
min_words=3&\
max_words=5&\
min_frequency=3&\
include_translation=true&\
sort_by=frequency"
```

### Ejemplo 4: Análisis Específico
```bash
# Términos que contengan "sistema", top 20, con traducción
curl -O "http://localhost:7000/api/export/tmx-excel/TMX_ID?\
contains=sistema&\
top_n=20&\
include_translation=true&\
format=excel"
```

### Ejemplo 5: Exportación Mínima
```bash
# Solo término y frecuencia en JSON
curl -O "http://localhost:7000/api/export/tmx-excel/TMX_ID?\
columns=term,frequency&\
format=json&\
min_frequency=2"
```

## 📊 Casos de Uso

### 1. Crear Glosario de Términos Frecuentes
```bash
curl -O "http://localhost:7000/api/export/tmx-excel/TMX_ID?\
min_frequency=10&\
min_words=2&\
sort_by=alphabetical&\
include_translation=true"
```

### 2. Identificar Términos Compuestos
```bash
curl -O "http://localhost:7000/api/export/tmx-excel/TMX_ID?\
min_words=3&\
top_n=100&\
sort_by=frequency"
```

### 3. Análisis de Términos Técnicos
```bash
curl -O "http://localhost:7000/api/export/tmx-excel/TMX_ID?\
exclude_numbers=false&\
min_frequency=5&\
format=csv"
```

### 4. Exportación para Revisión
```bash
curl -O "http://localhost:7000/api/export/tmx-excel/TMX_ID?\
top_n=200&\
include_translation=true&\
sort_by=frequency&\
columns=term,frequency,translation"
```

## 🐍 Uso desde Python

```python
import requests

BASE_URL = "http://localhost:7000"
TMX_ID = "tu-tmx-id-aqui"

# Configurar parámetros
params = {
    'min_frequency': 5,
    'top_n': 100,
    'min_words': 2,
    'sort_by': 'frequency',
    'sort_order': 'desc',
    'format': 'excel',
    'include_translation': True
}

# Descargar
response = requests.get(
    f"{BASE_URL}/api/export/tmx-excel/{TMX_ID}",
    params=params
)

# Guardar archivo
with open('terminos_filtrados.xlsx', 'wb') as f:
    f.write(response.content)

print("Archivo descargado exitosamente")
```

## 📝 Valores por Defecto

Si no especificas parámetros, se usan estos valores:

```python
{
    'min_frequency': None,      # Sin filtro
    'top_n': None,              # Todos los términos
    'min_words': None,          # Sin filtro
    'max_words': None,          # Sin filtro
    'sort_by': 'frequency',     # Ordenar por frecuencia
    'sort_order': 'desc',       # Descendente
    'format': 'excel',          # Formato Excel
    'columns': None,            # Todas las columnas
    'exclude_numbers': False,   # Incluir números
    'contains': None,           # Sin filtro
    'include_translation': False # Sin traducción
}
```

## ⚠️ Notas Importantes

1. **Orden de aplicación de filtros:**
   - Primero se aplican filtros de contenido (min_frequency, min_words, etc.)
   - Luego se ordena (sort_by, sort_order)
   - Finalmente se aplica top_n

2. **Traducción:**
   - Solo funciona si el TMX tiene pares bilingües
   - Requiere `include_translation=true`

3. **Columnas personalizadas:**
   - Si especificas `columns`, solo se incluirán esas columnas
   - Los nombres pueden estar en inglés o español

4. **Formatos:**
   - Excel: Incluye formato y estilos
   - CSV: Compatible con Excel y otras herramientas
   - JSON: Para procesamiento programático

## 🔍 Troubleshooting

### Error: "No se encontraron términos con los filtros aplicados"
**Causa:** Los filtros son demasiado restrictivos.

**Solución:** Relaja los filtros o verifica los valores.

### Traducción vacía
**Causa:** El TMX no tiene pares bilingües o el idioma no coincide.

**Solución:** Verifica que el TMX tenga traducciones y que el idioma sea correcto.

### Columnas no aparecen
**Causa:** Nombre de columna incorrecto o columna no disponible.

**Solución:** Usa nombres válidos: term, frequency, length, words, language, translation.
