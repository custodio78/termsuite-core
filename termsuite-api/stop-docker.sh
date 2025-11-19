#!/bin/bash
# Script para detener el contenedor

CONTAINER_NAME="termsuite-api"

echo "🛑 Deteniendo TermSuite API..."
docker stop $CONTAINER_NAME

echo "🗑️  Eliminando contenedor..."
docker rm $CONTAINER_NAME

echo "✅ Contenedor detenido y eliminado"
