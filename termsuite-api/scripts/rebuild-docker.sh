#!/bin/bash

echo "🚀 Reconstruyendo Docker con nueva funcionalidad de clasificación de ámbito..."
echo "=================================================================="

# Detener contenedor existente si está ejecutándose
echo "📦 Deteniendo contenedor existente..."
docker-compose down

# Limpiar imágenes anteriores (opcional, descomenta si quieres limpiar completamente)
# echo "🧹 Limpiando imágenes anteriores..."
# docker rmi termsuite-api-termsuite-api 2>/dev/null || true

# Reconstruir imagen
echo "🔨 Reconstruyendo imagen Docker..."
docker-compose build --no-cache

# Verificar que la construcción fue exitosa
if [ $? -eq 0 ]; then
    echo "✅ Imagen reconstruida exitosamente"
    
    # Iniciar contenedor
    echo "🚀 Iniciando contenedor..."
    docker-compose up -d
    
    # Esperar un momento para que el servicio se inicie
    echo "⏳ Esperando que el servicio se inicie..."
    sleep 10
    
    # Verificar que el servicio está funcionando
    echo "🔍 Verificando estado del servicio..."
    if curl -s http://localhost:7000/api > /dev/null; then
        echo "✅ Servicio funcionando correctamente en http://localhost:7000"
        echo ""
        echo "🎯 Nuevas funcionalidades disponibles:"
        echo "   - ✅ SOLUCIONADO: Descarga prematura de Excel"
        echo "   - Descarga rápida para archivos pequeños (≤100 términos)"
        echo "   - Descarga asíncrona para archivos grandes (>100 términos)"
        echo "   - Clasificación de términos por ámbito/dominio optimizada"
        echo "   - Nuevas columnas en Excel: Relevancia Ámbito, Confianza Ámbito, Razón Ámbito"
        echo "   - Endpoint: GET /api/tmx/{tmx_id}/export-ready"
        echo "   - Endpoint: POST /api/ollama/classify-domain"
        echo ""
        echo "📖 Para usar la nueva funcionalidad:"
        echo "   1. Abre http://localhost:7000 en tu navegador"
        echo "   2. Sube un archivo TMX"
        echo "   3. En 'Ámbito de Especialización', describe tu dominio (opcional)"
        echo "   4. Activa 'Clasificar términos por relevancia al ámbito' (opcional)"
        echo "   5. Procesa y descarga - el sistema elegirá automáticamente:"
        echo "      • Descarga rápida: ≤100 términos con datos pre-procesados"
        echo "      • Descarga asíncrona: >100 términos o procesamiento pesado"
        echo ""
        echo "🧪 Para probar las mejoras:"
        echo "   python tests/test_download_fix.py"
        echo "   python tests/test_domain_classification.py"
    else
        echo "⚠️  El servicio no responde. Verificando logs..."
        docker-compose logs --tail=20 termsuite-api
    fi
    
    echo ""
    echo "📋 Comandos útiles:"
    echo "   Ver logs:     docker-compose logs -f termsuite-api"
    echo "   Detener:      docker-compose down"
    echo "   Reiniciar:    docker-compose restart"
    echo "   Estado:       docker-compose ps"
    
else
    echo "❌ Error al reconstruir la imagen Docker"
    echo "Revisa los logs arriba para identificar el problema"
    exit 1
fi

echo "=================================================================="
echo "✅ Reconstrucción completada"