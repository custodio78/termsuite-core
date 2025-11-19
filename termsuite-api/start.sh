#!/bin/bash
# Script de inicio para TermSuite API

echo "=========================================="
echo "  TermSuite API - Inicio"
echo "=========================================="

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose no está instalado"
    exit 1
fi

# Verificar JAR
if [ ! -f "termsuite/termsuite-core-3.0.10.jar" ]; then
    echo "⚠️  Advertencia: JAR de TermSuite no encontrado"
    echo "   Por favor, coloca termsuite-core-3.0.10.jar en la carpeta termsuite/"
    echo ""
    read -p "¿Continuar de todos modos? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Crear directorios
echo "📁 Creando directorios..."
mkdir -p data/uploads data/corpus data/outputs termsuite

# Construir y ejecutar
echo "🐳 Construyendo contenedor Docker..."
docker-compose build

echo "🚀 Iniciando servicios..."
docker-compose up -d

echo ""
echo "✅ TermSuite API iniciada"
echo ""
echo "📡 Endpoints disponibles:"
echo "   - API: http://localhost:7000"
echo "   - Docs: http://localhost:7000/docs"
echo ""
echo "📋 Comandos útiles:"
echo "   - Ver logs: docker-compose logs -f"
echo "   - Detener: docker-compose down"
echo "   - Reiniciar: docker-compose restart"
echo ""
