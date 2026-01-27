# Limitación: Extracción con TermSuite

## Estado Actual

✅ **Funcionalidad Principal: FUNCIONANDO**
- Extracción directa de términos del TMX
- Múltiples traducciones
- Búsqueda de términos
- Exportación a Excel

❌ **Funcionalidad Avanzada: NO DISPONIBLE**
- Extracción con TermSuite para analizar segmentos largos

## Razón

TermSuite requiere **TreeTagger** o **Mate** como dependencia obligatoria para el análisis morfológico y POS tagging. TreeTagger:

1. **No se puede redistribuir** por razones de licencia
2. **Requiere instalación manual** compleja
3. **Necesita modelos de idioma** específicos (archivos `.par`)
4. **Debe configurarse** con rutas específicas

## Impacto

### Sin TermSuite (Estado Actual)

**Funciona para:**
- ✅ TMX de glosarios (términos individuales)
- ✅ Extracción directa de segmentos
- ✅ Búsqueda y filtrado
- ✅ Múltiples traducciones
- ✅ Exportación a Excel

**NO funciona para:**
- ❌ Analizar segmentos largos y extraer términos individuales automáticamente
- ❌ Identificar términos compuestos en frases completas
- ❌ Análisis morfológico avanzado

### Con TermSuite (Requiere TreeTagger)

**Funcionalidad adicional:**
- ✅ Analizar frases completas: "La válvula de seguridad debe ser inspeccionada"
- ✅ Extraer términos: "válvula", "válvula de seguridad", "seguridad"
- ✅ Identificar términos compuestos automáticamente
- ✅ Análisis morfológico y lematización

## Soluciones

### Opción 1: Usar TMX de Glosarios (Recomendado)

En lugar de TMX con frases completas, usa TMX con términos individuales:

```xml
<!-- En lugar de esto: -->
<seg>La válvula de seguridad debe ser inspeccionada regularmente.</seg>

<!-- Usa esto: -->
<seg>válvula</seg>
<seg>válvula de seguridad</seg>
```

**Ventajas:**
- ✅ Funciona inmediatamente
- ✅ No requiere configuración adicional
- ✅ Resultados más precisos
- ✅ Más rápido

**Cómo obtener un TMX de glosarios:**
- Exportar desde SDL Trados como "Glossary"
- Exportar desde memoQ como "Term Base"
- Exportar desde Memsource como "Term Base"
- Convertir manualmente tu TMX

### Opción 2: Instalar TreeTagger (Avanzado)

Si necesitas analizar segmentos largos, puedes instalar TreeTagger manualmente:

#### Pasos:

1. **Descargar TreeTagger:**
   ```bash
   wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tree-tagger-linux-3.2.4.tar.gz
   ```

2. **Descargar modelos de idioma:**
   ```bash
   # Para español
   wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/spanish-utf8.par.gz
   gunzip spanish-utf8.par.gz
   mv spanish-utf8.par spanish.par
   
   # Para inglés
   wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/english-utf8.par.gz
   gunzip english-utf8.par.gz
   mv english-utf8.par english.par
   ```

3. **Modificar Dockerfile:**
   ```dockerfile
   # Agregar después de instalar Java
   RUN apt-get update && apt-get install -y \
       wget \
       && rm -rf /var/lib/apt/lists/*
   
   # Instalar TreeTagger
   WORKDIR /app/treetagger
   RUN wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tree-tagger-linux-3.2.4.tar.gz \
       && tar -xzf tree-tagger-linux-3.2.4.tar.gz \
       && rm tree-tagger-linux-3.2.4.tar.gz
   
   # Descargar modelos
   RUN mkdir -p models && cd models \
       && wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/spanish-utf8.par.gz \
       && gunzip spanish-utf8.par.gz \
       && mv spanish-utf8.par spanish.par \
       && wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/english-utf8.par.gz \
       && gunzip english-utf8.par.gz \
       && mv english-utf8.par english.par
   
   WORKDIR /app
   ```

4. **Actualizar termsuite.py:**
   ```python
   self.treetagger_home = os.getenv('TREETAGGER_HOME', '/app/treetagger')
   
   cmd = [
       'java',
       *shlex.split(self.java_opts),
       '-jar', self.jar_path,
       '-t', self.treetagger_home,  # <-- Agregar esto
       '--from-text-corpus', str(corpus_path),
       # ... resto de parámetros
   ]
   ```

5. **Reconstruir imagen:**
   ```bash
   docker-compose down
   docker-compose build
   docker-compose up -d
   ```

### Opción 3: Usar TermSuite Docker Oficial

El proyecto TermSuite tiene su propia imagen Docker con TreeTagger incluido:

```bash
git clone https://github.com/termsuite/termsuite-docker.git
cd termsuite-docker
bin/build
bin/termsuite extract -c ./corpus/ -l es --tsv output.tsv
```

Luego integrar los resultados con tu aplicación.

## Recomendación

Para la mayoría de casos de uso, **Opción 1 (TMX de Glosarios)** es suficiente y más eficiente:

1. ✅ No requiere TreeTagger
2. ✅ Más rápido
3. ✅ Más preciso
4. ✅ Más fácil de mantener
5. ✅ Funciona inmediatamente

Solo considera instalar TreeTagger si:
- Tienes TMX con frases muy largas
- No puedes convertir tu TMX a formato de glosario
- Necesitas análisis morfológico avanzado
- Tienes experiencia con configuración de sistemas complejos

## Conclusión

La aplicación **funciona perfectamente** para su propósito principal: extraer términos de TMX con múltiples traducciones. La funcionalidad de TermSuite es opcional y solo necesaria para casos de uso muy específicos.

**Recomendación:** Usa TMX de glosarios y disfruta de la funcionalidad completa sin complicaciones.
