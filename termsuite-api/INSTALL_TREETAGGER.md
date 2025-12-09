# Instalación de TreeTagger

## Paso 1: Descargar TreeTagger

1. Ve a: https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/
2. Descarga los siguientes archivos:

### Para Linux (Docker):
- `tree-tagger-linux-3.2.4.tar.gz` - Binarios de TreeTagger
- `tagger-scripts.tar.gz` - Scripts auxiliares
- `install-tagger.sh` - Script de instalación

### Modelos de idioma (archivos .par):
- `spanish-utf8.par.gz` - Modelo para español
- `english-utf8.par.gz` - Modelo para inglés
- `french-utf8.par.gz` - Modelo para francés (opcional)
- `german-utf8.par.gz` - Modelo para alemán (opcional)

## Paso 2: Colocar archivos en el proyecto

Crea la siguiente estructura en tu proyecto:

```
termsuite-api/
  treetagger/
    tree-tagger-linux-3.2.4.tar.gz
    tagger-scripts.tar.gz
    install-tagger.sh
    models/
      spanish-utf8.par.gz
      english-utf8.par.gz
      french-utf8.par.gz (opcional)
      german-utf8.par.gz (opcional)
```

## Paso 3: Ejecutar script de instalación

```bash
cd termsuite-api
chmod +x install_treetagger.sh
./install_treetagger.sh
```

Este script:
1. Descomprime TreeTagger
2. Descomprime los modelos
3. Renombra los archivos correctamente
4. Configura permisos

## Paso 4: Reconstruir Docker

```bash
docker-compose down
docker-compose build
docker-compose up -d
```

## Paso 5: Verificar instalación

```bash
docker exec termsuite-api ls -la /app/treetagger/
docker exec termsuite-api ls -la /app/treetagger/models/
```

Deberías ver:
```
/app/treetagger/
  bin/
    tree-tagger
  lib/
  models/
    spanish.par
    english.par
    french.par
    german.par
```

## Paso 6: Probar TermSuite

Desde la interfaz web:
1. Sube un TMX con segmentos completos
2. Selecciona idiomas
3. ☑️ Marca "Extraer términos individuales con TermSuite"
4. Click "Aplicar Idiomas"

Debería funcionar correctamente.

## Troubleshooting

### Error: "tree-tagger: command not found"
```bash
docker exec termsuite-api chmod +x /app/treetagger/bin/*
```

### Error: "Model not found"
Verifica que los archivos .par estén en `/app/treetagger/models/` y tengan el nombre correcto:
- `spanish.par` (no `spanish-utf8.par`)
- `english.par` (no `english-utf8.par`)

### Error: "Permission denied"
```bash
docker exec termsuite-api chmod -R 755 /app/treetagger/
```
