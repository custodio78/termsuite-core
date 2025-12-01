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

4. **✅ Aplicas idiomas** 
   - Click en "Aplicar Idiomas"
   - Extrae términos del idioma origen
   - Configura las traducciones al idioma destino

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

| Número | Término | Frecuencia | Longitud | Palabras | Idioma | Traducción | Tipo Match |
|--------|---------|------------|----------|----------|--------|------------|------------|
| 1 | elevador | 45 | 8 | 1 | es | elevator | Exacto |
| 2 | sistema hidráulico | 32 | 18 | 2 | es | hydraulic system | Exacto |
| 3 | plataforma | 28 | 10 | 1 | es | platform | Exacto |

### Ventajas

✅ **Detección automática** de idiomas disponibles  
✅ **Selección específica** de idioma origen y destino  
✅ **Validación** de idiomas diferentes  
✅ **Traducciones precisas** del idioma configurado  
✅ **Soporte multiidioma** (es, en, fr, de, it, pt, eu, ca, gl, etc.)  
✅ **Interfaz intuitiva** con selectores dinámicos  

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
