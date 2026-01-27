#!/bin/bash
# Script alternativo para ejecutar sin docker-compose

echo "=========================================="
echo "  TermSuite API - Inicio con Docker"
echo "=========================================="

# Variables
IMAGE_NAME="termsuite-api"
CONTAINER_NAME="termsuite-api"
PORT=7000

# Detener contenedor existente
echo "🛑 Deteniendo contenedor existente..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# Construir imagen
echo "🔨 Construyendo imagen Docker..."
docker build -t $IMAGE_NAME .

if [ $? -ne 0 ]; then
    echo "❌ Error al construir la imagen"
    exit 1
fi

# Crear directorios
echo "📁 Creando directorios..."
mkdir -p data/uploads data/corpus data/outputs termsuite

# Ejecutar contenedor
echo "🚀 Iniciando contenedor..."
docker run -d \
    --name $CONTAINER_NAME \
    -p $PORT:8000 \
    -v "$(pwd)/data:/app/data" \
    -v "$(pwd)/termsuite:/app/termsuite" \
    -e TERMSUITE_JAR=/app/termsuite/termsuite-core-3.0.10.jar \
    -e DATA_DIR=/app/data \
    -e JAVA_OPTS="-Xms1g -Xmx4g" \
    --restart unless-stopped \
    $IMAGE_NAME

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ TermSuite API iniciada exitosamente"
    echo ""
    echo "📡 Endpoints disponibles:"
    echo "   - API: http://localhost:$PORT"
    echo "   - Docs: http://localhost:$PORT/docs"
    echo ""
    echo "📋 Comandos útiles:"
    echo "   - Ver logs: docker logs -f $CONTAINER_NAME"
    echo "   - Detener: docker stop $CONTAINER_NAME"
    echo "   - Reiniciar: docker restart $CONTAINER_NAME"
    echo ""
else
    echo "❌ Error al iniciar el contenedor"
    exit 1
fi
