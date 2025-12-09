# Instalación de TreeTagger para TermSuite

## ¿Qué es TreeTagger?

TreeTagger es un POS tagger (etiquetador morfosintáctico) necesario para que TermSuite pueda analizar segmentos de texto y extraer términos individuales.

## ¿Cuándo lo necesitas?

**NO lo necesitas si:**
- ✅ Usas TMX de glosarios (términos individuales)
- ✅ Solo quieres extraer segmentos completos
- ✅ La funcionalidad básica te es suficiente

**SÍ lo necesitas si:**
- Tienes TMX con frases completas
- Quieres extraer términos individuales automáticamente
- Necesitas análisis morfológico avanzado

## Instalación Rápida

### Paso 1: Descargar archivos

Ve a: https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/

Descarga:
1. **tree-tagger-linux-3.2.4.tar.gz**
2. **tagger-scripts.tar.gz**
3. **spanish-utf8.par.gz** (modelo español)
4. **english-utf8.par.gz** (modelo inglés)

### Paso 2: Organizar archivos

Crea esta estructura en tu proyecto:

```
termsuite-api/
  treetagger/
    tree-tagger-linux-3.2.4.tar.gz
    tagger-scripts.tar.gz
    models/
      spanish-utf8.par.gz
      english-utf8.par.gz
```

### Paso 3: Reconstruir Docker

```bash
cd termsuite-api
docker-compose down
docker-compose build
docker-compose up -d
```

Durante el build verás:
```
========================================
Instalando TreeTagger...
========================================
Instalando modelo: spanish-utf8.par.gz
Instalando modelo: english-utf8.par.gz
✓ TreeTagger instalado correctamente
```

### Paso 4: Verificar instalación

```bash
docker exec termsuite-api ls -la /app/treetagger/models/
```

Deberías ver:
```
spanish.par
english.par
```

### Paso 5: Probar

1. Abre http://localhost:7000
2. Sube un TMX con segmentos completos
3. Selecciona idiomas
4. ☑️ Marca "Extraer términos individuales con TermSuite"
5. Click "Aplicar Idiomas"

## Modelos Disponibles

Puedes descargar modelos para más idiomas:

| Idioma | Archivo | URL |
|--------|---------|-----|
| Español | spanish-utf8.par.gz | https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/spanish-utf8.par.gz |
| Inglés | english-utf8.par.gz | https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/english-utf8.par.gz |
| Francés | french-utf8.par.gz | https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/french-utf8.par.gz |
| Alemán | german-utf8.par.gz | https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/german-utf8.par.gz |
| Italiano | italian-utf8.par.gz | https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/italian-utf8.par.gz |
| Portugués | portuguese-utf8.par.gz | https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/portuguese-utf8.par.gz |

## Troubleshooting

### Error: "TreeTagger no encontrado"

Verifica que los archivos estén en `termsuite-api/treetagger/` ANTES de hacer `docker-compose build`.

### Error: "Model not found"

Verifica que descargaste los modelos `.par.gz` y los colocaste en `termsuite-api/treetagger/models/`.

### Build sin TreeTagger

Si haces build sin los archivos de TreeTagger, verás:
```
⚠ TreeTagger no disponible
La extracción con TermSuite no funcionará
Ver INSTALL_TREETAGGER.md para instrucciones
```

Esto es normal. La aplicación funcionará pero sin la funcionalidad de TermSuite.

## Licencia

TreeTagger es software gratuito para investigación y educación. Para uso comercial, contacta al autor.

Más información: https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/

## Alternativa

Si no quieres instalar TreeTagger, simplemente usa TMX de glosarios (términos individuales) en lugar de memorias de traducción con frases completas. La funcionalidad principal funciona perfectamente sin TreeTagger.
