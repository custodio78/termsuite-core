# Cómo Funciona la Extracción de TMX

## Concepto Importante

Un archivo TMX (Translation Memory eXchange) almacena **segmentos de traducción completos**, no términos individuales.

### Ejemplo de TMX:

```xml
<tu>
  <tuv xml:lang="es">
    <seg>La válvula de seguridad debe ser inspeccionada regularmente.</seg>
  </tuv>
  <tuv xml:lang="en">
    <seg>The safety valve must be inspected regularly.</seg>
  </tuv>
</tu>
```

## Qué Extrae la Aplicación

### Extracción Directa (sin filtros)

La aplicación extrae **segmentos completos**:

```
Término: "La válvula de seguridad debe ser inspeccionada regularmente."
Traducción: "The safety valve must be inspected regularly."
```

### Búsqueda de Términos

Cuando buscas "válvula":
- **Coincidencia parcial**: Encuentra todos los segmentos que contienen "válvula"
- Muestra: "La válvula de seguridad...", "Cierre la válvula principal...", etc.

## Dos Tipos de TMX

### 1. TMX de Segmentos (lo que tenemos)

**Contenido:**
```xml
<seg>La válvula de seguridad debe ser inspeccionada regularmente.</seg>
```

**Extracción:**
- Segmentos completos
- Útil para traducción de frases
- Búsqueda parcial de términos

### 2. TMX de Términos (lo que esperabas)

**Contenido:**
```xml
<seg>válvula</seg>
```

**Extracción:**
- Términos individuales
- Útil para glosarios
- Búsqueda exacta

## Solución: Crear TMX de Términos

Si quieres extraer términos individuales, necesitas un TMX con términos únicos:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE tmx SYSTEM "tmx14.dtd">
<tmx version="1.4">
  <header creationtool="TermSuite" creationtoolversion="1.0" datatype="plaintext" segtype="phrase" adminlang="en-US" srclang="es" o-tmf="unknown"/>
  <body>
    
    <tu>
      <tuv xml:lang="es"><seg>válvula</seg></tuv>
      <tuv xml:lang="en"><seg>valve</seg></tuv>
    </tu>
    
    <tu>
      <tuv xml:lang="es"><seg>válvula</seg></tuv>
      <tuv xml:lang="en"><seg>tap</seg></tuv>
    </tu>
    
    <tu>
      <tuv xml:lang="es"><seg>válvula</seg></tuv>
      <tuv xml:lang="en"><seg>faucet</seg></tuv>
    </tu>
    
    <tu>
      <tuv xml:lang="es"><seg>elevador</seg></tuv>
      <tuv xml:lang="en"><seg>elevator</seg></tuv>
    </tu>
    
    <tu>
      <tuv xml:lang="es"><seg>elevador</seg></tuv>
      <tuv xml:lang="en"><seg>lift</seg></tuv>
    </tu>
    
  </body>
</tmx>
```

## Filtrado de Términos

Para extraer solo términos específicos de segmentos largos, puedes:

### Opción 1: Filtrar por número de palabras

```
Palabras mínimas: 1
Palabras máximas: 3
```

Esto filtrará segmentos largos y dejará solo términos cortos.

### Opción 2: Usar la búsqueda

1. Busca el término: "válvula"
2. Ve las coincidencias parciales
3. Identifica en qué segmentos aparece

### Opción 3: Exportar y filtrar en Excel

1. Exporta todos los segmentos
2. En Excel, filtra por longitud o palabras
3. Busca términos específicos con Ctrl+F

## Recomendación

Para tu caso de uso (extraer términos con múltiples traducciones), te recomiendo:

1. **Crear un TMX de términos** (no de segmentos)
2. **Usar un glosario** en formato TMX
3. **Exportar desde tu CAT tool** solo términos, no segmentos completos

### Herramientas para convertir:

- **SDL Trados**: Exportar como "Glossary" en formato TMX
- **memoQ**: Exportar "Term Base" como TMX
- **Memsource**: Exportar "Term Base"

## Ejemplo Práctico

### TMX Actual (segmentos):
```
Total términos: 28 segmentos completos
Búsqueda "válvula": 4 coincidencias parciales
```

### TMX Ideal (términos):
```
Total términos: 9 términos únicos
Búsqueda "válvula": 1 coincidencia exacta (con 3 traducciones)
```

## Conclusión

La aplicación funciona correctamente. El "problema" es que el TMX de prueba contiene segmentos completos, no términos individuales. Esto es el comportamiento estándar de las memorias de traducción.

Para probar la funcionalidad de múltiples traducciones, necesitas un TMX con términos individuales repetidos con diferentes traducciones.
