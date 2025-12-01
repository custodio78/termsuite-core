# TermSuite API - Extracción con TMX Multiidioma

## ✅ Funcionalidad de Selección de Idiomas

### Flujo de Trabajo

Cuando subes un TMX multiidioma:

1. **📤 Subes el TMX** 
   - La aplicación analiza automáticamente todos los idiomas disponibles
   - Detecta: español (es), inglés (en), francés (fr), etc.

2. **🌍 Selectores dinámicos aparecen**
   - **Idioma origen**: Selecciona el idioma de los términos a extraer
   - **Idioma de traducción**: Selecciona el idioma al que traducir
   - Solo muestra los idiomas que realmente están en tu TMX

3. **🔄 Seleccionas los idiomas**
   - Ejemplo: Origen = Español (es), Traducción = English (en)
   - El sistema valida que sean diferentes
   - **☑️ Opción**: Extraer términos individuales con TermSuite

4. **✅ Aplicas idiomas** 
   - Click en "Aplicar Idiomas"
   - Extrae términos del idioma origen
   - Configura las traducciones al idioma destino
   - Si activaste TermSuite, extrae términos individuales de los segmentos

5. **⚙️ Configuras opciones de filtrado**
   - Frecuencia mínima
   - Número de palabras (min/max)
   - Top N términos
   - Incluir/excluir números
   - **Incluir traducciones** (muestra: es → en)

6. **📊 Extraes términos** 
   - Click en "Extraer Términos del TMX"
   - Descarga Excel con términos y traducciones

### Ejemplo con TMX ULMA (es, en)

```
1. Subes ULMA_MasterTM.tmx
2. Mensaje: "TMX multiidioma detectado: es, en"
3. Selectores muestran:
   - Idioma origen: Español (es) ✓
   - Idioma traducción: English (en) ✓
4. Click "Aplicar Idiomas"
5. Mensaje: "1,272 términos del idioma 'es' extraídos (traducción: en)"
6. Checkbox: "Incluir traducciones (es → en)" ✓
7. Configuras: frecuencia ≥ 2, palabras 1-5
8. Click "Extraer Términos del TMX"
9. Descargas: terminos_tmx_es.xlsx
```

### Columnas en el Excel

| Número | Término | Frecuencia | Longitud | Palabras | Idioma | Traducción | Tipo Match | Variantes |
|--------|---------|------------|----------|----------|--------|------------|------------|-----------|
| 1 | elevador | 45 | 8 | 1 | es | elevator | Exacto | 1 |
| 2 | sistema hidráulico | 32 | 18 | 2 | es | hydraulic system | Exacto | 1 |
| 3 | válvula | 28 | 7 | 1 | es | valve \| tap | Exacto | 2 |

**Nota:** Si un término tiene múltiples traducciones, se muestran separadas por ` | `

### Ventajas

✅ **Detección automática** de idiomas disponibles  
✅ **Selección específica** de idioma origen y destino  
✅ **Validación** de idiomas diferentes  
✅ **Traducciones precisas** del idioma configurado  
✅ **Soporte multiidioma** (es, en, fr, de, it, pt, eu, ca, gl, etc.)  
✅ **Interfaz intuitiva** con selectores dinámicos  
✅ **Herramienta de búsqueda** para verificar términos específicos  
✅ **Limpieza automática** de bullets y marcadores de lista  
✅ **Dos modos de extracción**: Segmentos completos o términos individuales  

### Casos de Uso

**TMX bilingüe (es-en):**
- Origen: Español → Traducción: English
- Extrae términos en español con traducciones al inglés

**TMX trilingüe (es-en-fr):**
- Origen: Español → Traducción: English
- Origen: Español → Traducción: Français
- Origen: English → Traducción: Español

**TMX monolingüe (solo es):**
- Solo aparece selector de idioma origen
- No hay selector de traducción
- Extrae términos sin traducciones

## 🔍 Herramienta de Búsqueda

Si un término no aparece en el Excel, usa la herramienta de búsqueda integrada:

### Cómo usar:

1. Después de subir el TMX
2. En "Configurar Extracción"
3. Escribe el término: `coupling`
4. Presiona Enter o click en "Buscar en TMX"
5. Aparece un panel con resultados detallados

### Panel de Resultados:

El panel muestra para cada idioma:

**✓ Encontrado (verde)**
- Término encontrado exactamente
- Muestra la frecuencia (ej: 123x)

**~ Coincidencias parciales (amarillo)**
- Términos similares encontrados
- Lista hasta 5 coincidencias con frecuencias
- Útil para encontrar variantes

**✗ No encontrado (rojo)**
- El término no existe en ese idioma
- Verifica que seleccionaste el idioma correcto

### Ejemplo visual:

```
Resultados: "coupling"

✓ English (en): Encontrado                    [123x]

✗ Español (es): No encontrado

Estadísticas del TMX:
English: 1,234 términos únicos, 5,678 ocurrencias
Español: 1,189 términos únicos, 5,432 ocurrencias
```

**Solución:** Selecciona idioma origen = English (en)

## 🔧 Dos Modos de Extracción

### Modo 1: Extracción Directa (por defecto)

**Extrae segmentos completos del TMX**

```
TMX contiene:
"La válvula de seguridad debe ser inspeccionada regularmente."

Extrae:
"La válvula de seguridad debe ser inspeccionada regularmente."
```

**Cuándo usar:**
- TMX es un glosario con términos individuales
- Quieres ver el contexto completo
- Necesitas frases de ejemplo

### Modo 2: Extracción con TermSuite ☑️

**Analiza los segmentos y extrae términos técnicos individuales**

```
TMX contiene:
"La válvula de seguridad debe ser inspeccionada regularmente."

Analiza con TermSuite y extrae:
- válvula
- válvula de seguridad
- seguridad
```

**Cuándo usar:**
- TMX contiene frases completas (memoria de traducción)
- Quieres extraer solo los términos técnicos
- Necesitas un glosario a partir de segmentos largos

**Cómo activar:**
1. Después de subir el TMX
2. Marca ☑️ "Extraer términos individuales con TermSuite"
3. Click en "Aplicar Idiomas"

### Comparación

| Característica | Modo Directo | Modo TermSuite |
|----------------|--------------|----------------|
| Velocidad | ⚡ Rápido | 🐢 Más lento |
| Resultado | Segmentos completos | Términos individuales |
| Mejor para | Glosarios | Memorias de traducción |
| Requiere | - | Java + TermSuite |

## 🧹 Limpieza de Bullets

La aplicación limpia automáticamente bullets y marcadores:

| Original | Limpiado |
|----------|----------|
| `a) elevador` | `elevador` |
| `1. plataforma` | `plataforma` |
| `- cilindro` | `cilindro` |
| `• pistón` | `pistón` |
| `coupling` | `coupling` (sin cambios) |

**Nota:** Solo se eliminan bullets con espacio después, preservando términos válidos como "c-clamp".

## 🔄 Múltiples Traducciones

Si un término tiene varias traducciones en el TMX, **todas se incluyen** en el Excel:

### Ejemplo:

En tu TMX:
```xml
<tu>
  <tuv xml:lang="es"><seg>válvula</seg></tuv>
  <tuv xml:lang="en"><seg>valve</seg></tuv>
</tu>
<tu>
  <tuv xml:lang="es"><seg>válvula</seg></tuv>
  <tuv xml:lang="en"><seg>tap</seg></tuv>
</tu>
```

En el Excel:
```
Término: válvula
Traducción: valve | tap
Variantes: 2
```

### Ventajas:
- ✅ **No pierdes información** de traducciones alternativas
- ✅ **Fácil de identificar** términos con múltiples significados
- ✅ **Columna "Variantes"** indica cuántas traducciones hay
- ✅ **Separador claro** (` | `) para distinguir cada traducción

### Casos de uso:

**Polisemia (múltiples significados):**
- `válvula` → `valve | tap | faucet` (3 variantes)
- Útil para identificar términos ambiguos

**Variantes regionales:**
- `ordenador` → `computer | PC` (2 variantes)
- Útil para localización

**Sinónimos aceptados:**
- `elevador` → `elevator | lift` (2 variantes)
- Útil para terminología flexible
