#!/bin/bash
# Script para preparar TreeTagger antes de construir Docker

set -e

echo "=========================================="
echo "Preparando TreeTagger para Docker"
echo "=========================================="

# Crear directorio si no existe
mkdir -p treetagger/models

# Verificar que existen los archivos necesarios
echo ""
echo "Verificando archivos..."

if [ ! -f "treetagger/tree-tagger-linux-3.2.4.tar.gz" ]; then
    echo "❌ Falta: treetagger/tree-tagger-linux-3.2.4.tar.gz"
    echo "   Descarga desde: https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tree-tagger-linux-3.2.4.tar.gz"
    exit 1
fi

if [ ! -f "treetagger/tagger-scripts.tar.gz" ]; then
    echo "❌ Falta: treetagger/tagger-scripts.tar.gz"
    echo "   Descarga desde: https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tagger-scripts.tar.gz"
    exit 1
fi

# Verificar modelos
MODELS_FOUND=0

if [ -f "treetagger/models/spanish-utf8.par.gz" ]; then
    echo "✓ Modelo español encontrado"
    MODELS_FOUND=$((MODELS_FOUND + 1))
fi

if [ -f "treetagger/models/english-utf8.par.gz" ]; then
    echo "✓ Modelo inglés encontrado"
    MODELS_FOUND=$((MODELS_FOUND + 1))
fi

if [ -f "treetagger/models/french-utf8.par.gz" ]; then
    echo "✓ Modelo francés encontrado"
    MODELS_FOUND=$((MODELS_FOUND + 1))
fi

if [ -f "treetagger/models/german-utf8.par.gz" ]; then
    echo "✓ Modelo alemán encontrado"
    MODELS_FOUND=$((MODELS_FOUND + 1))
fi

if [ $MODELS_FOUND -eq 0 ]; then
    echo "❌ No se encontraron modelos de idioma (.par.gz)"
    echo "   Descarga al menos uno desde: https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/"
    exit 1
fi

echo ""
echo "✓ Todos los archivos necesarios están presentes"
echo ""
echo "Ahora puedes construir Docker:"
echo "  docker-compose build"
echo ""
