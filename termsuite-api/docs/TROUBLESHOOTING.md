# Troubleshooting - Solución de Problemas

## Problema: Términos no aparecen en el Excel

Si términos como "coupling" o "mechanical adjustments" no aparecen en el Excel exportado, sigue estos pasos:

### 1. Verificar con la herramienta de búsqueda

Después de subir tu TMX:

1. En la sección "Configurar Extracción"
2. Escribe el término en el campo "Buscar término específico..."
3. Click en "Buscar en TMX"
4. Verás un mensaje indicando:
   - ✓ Si el término fue encontrado y su frecuencia
   - ~ Si hay coincidencias parciales
   - ✗ Si no fue encontrado

### 2. Verificar idioma seleccionado

**Problema común:** Seleccionaste español pero los términos están en inglés

**Solución:**
- Si buscas "coupling" → Selecciona idioma: **English (en)**
- Si buscas "acoplamiento" → Selecciona idioma: **Español (es)**

### 3. Verificar filtros aplicados

Los términos pueden estar siendo filtrados por:

#### Frecuencia mínima
- Si configuraste "Frecuencia mínima: 5"
- Y "coupling" aparece solo 3 veces
- **No aparecerá en el Excel**
- **Solución:** Reduce la frecuencia mínima a 1

#### Número de palabras
- Si configuraste "Palabras mínimas: 2"
- Y buscas "coupling" (1 palabra)
- **No aparecerá en el Excel**
- **Solución:** Configura "Palabras mínimas: 1"

#### Top N términos
- Si configuraste "Top N términos: 100"
- Y "coupling" está en la posición 150
- **No aparecerá en el Excel**
- **Solución:** Aumenta el Top N o déjalo vacío

### 4. Usar el script de diagnóstico

Desde la línea de comandos:

```bash
cd termsuite-api
python debug_tmx.py uploads/tmx/TU_TMX_ID.tmx coupling "mechanical adjustments"
```

Esto te mostrará:
- Idiomas disponibles
- Total de términos por idioma
- Si los términos buscados existen
- Frecuencia de cada término
- Top 10 términos más frecuentes

### 5. Verificar limpieza de bullets

Si tu TMX tiene términos con bullets:
- `a) coupling` → Se limpia a `coupling` ✓
- `1. mechanical adjustments` → Se limpia a `mechanical adjustments` ✓

**Nota:** La limpieza solo elimina bullets si hay espacio después:
- `a) term` → `term` (se limpia)
- `a)term` → `a)term` (NO se limpia, se considera parte del término)

### 6. Ejemplo de configuración correcta

Para extraer TODOS los términos sin filtros:

```
Idioma origen: English (en)
Idioma traducción: Español (es)
Frecuencia mínima: 1
Top N términos: [vacío]
Palabras mínimas: 1
Palabras máximas: 10
☑ Incluir traducciones
☐ Excluir números
```

### 7. Verificar el archivo JSON generado

Después de "Aplicar Idiomas", se genera un archivo:
```
uploads/tmx/TU_TMX_ID_terms.json
```

Puedes abrirlo para ver:
- Todos los términos extraídos
- Frecuencias
- Idioma configurado

### 8. Casos especiales

#### TMX con variantes de idioma
- Tu TMX puede tener `en-US`, `en-GB`
- El sistema detecta ambos como `en`
- Selecciona simplemente `English (en)`

#### Términos con caracteres especiales
- Los términos se limpian de bullets pero mantienen:
  - Guiones: `c-clamp`, `a-frame`
  - Paréntesis internos: `valve (hydraulic)`
  - Números: `ISO 9001`

#### Términos muy largos
- Si un término tiene más de 50 caracteres
- Puede estar truncado en la vista previa
- Pero aparece completo en el Excel

#### Múltiples traducciones
- Si un término tiene 2 o más traducciones diferentes
- **Todas se incluyen** en el Excel
- Separadas por ` | ` (pipe)
- Ejemplo: `valve | tap | faucet`
- La columna "Variantes" indica cuántas traducciones hay

## Contacto

Si después de seguir estos pasos el problema persiste, revisa:
1. Los logs del servidor
2. El archivo TMX original (puede estar corrupto)
3. La codificación del archivo (debe ser UTF-8)
