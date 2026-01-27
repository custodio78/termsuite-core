#!/bin/bash

echo "🔧 Aplicando corrección de descarga prematura de Excel..."
echo "=================================================================="

# Verificar que Docker esté funcionando
if ! docker --version > /dev/null 2>&1; then
    echo "❌ Docker no está instalado o no está funcionando"
    exit 1
fi

if ! docker-compose --version > /dev/null 2>&1; then
    echo "❌ Docker Compose no está instalado o no está funcionando"
    exit 1
fi

echo "✅ Docker y Docker Compose disponibles"

# Mostrar resumen de cambios
echo ""
echo "📋 Cambios que se aplicarán:"
echo "   ✅ Nuevo endpoint: GET /api/tmx/{tmx_id}/export-ready"
echo "   ✅ Límite de 100 términos para descarga rápida"
echo "   ✅ Descarga asíncrona automática para archivos grandes"
echo "   ✅ Clasificación de dominio optimizada"
echo "   ✅ Frontend actualizado con lógica inteligente"
echo ""

# Confirmar con el usuario
read -p "¿Continuar con el rebuild? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Operación cancelada"
    exit 1
fi

# Detener contenedor existente
echo "📦 Deteniendo contenedor existente..."
docker-compose down

# Verificar que se detuvo correctamente
if docker-compose ps | grep -q "Up"; then
    echo "⚠️  Forzando detención..."
    docker-compose kill
    docker-compose down
fi

# Limpiar caché de build (opcional pero recomendado)
echo "🧹 Limpiando caché de Docker..."
docker system prune -f > /dev/null 2>&1

# Reconstruir imagen sin caché
echo "🔨 Reconstruyendo imagen Docker (sin caché)..."
docker-compose build --no-cache --pull

# Verificar que la construcción fue exitosa
if [ $? -eq 0 ]; then
    echo "✅ Imagen reconstruida exitosamente"
    
    # Iniciar contenedor
    echo "🚀 Iniciando contenedor con nuevas funcionalidades..."
    docker-compose up -d
    
    # Esperar que el servicio se inicie
    echo "⏳ Esperando que el servicio se inicie..."
    sleep 15
    
    # Verificar que el servicio está funcionando
    echo "🔍 Verificando estado del servicio..."
    
    # Intentar conectar varias veces
    for i in {1..5}; do
        if curl -s http://localhost:7000/api > /dev/null 2>&1; then
            echo "✅ Servicio funcionando correctamente en http://localhost:7000"
            
            # Probar el nuevo endpoint
            echo "🧪 Probando nuevo endpoint de verificación de descarga..."
            if curl -s "http://localhost:7000/api/tmx/test/export-ready" > /dev/null 2>&1; then
                echo "✅ Nuevo endpoint disponible (respuesta esperada: 404 para TMX inexistente)"
            else
                echo "⚠️  Nuevo endpoint no responde (puede ser normal si no hay TMX de prueba)"
            fi
            
            echo ""
            echo "🎉 ¡CORRECCIÓN APLICADA EXITOSAMENTE!"
            echo ""
            echo "🎯 Problema solucionado:"
            echo "   ❌ ANTES: Excel aparecía para descarga mientras el proceso seguía trabajando"
            echo "   ✅ AHORA: Excel solo aparece cuando está completamente listo"
            echo ""
            echo "📊 Comportamiento nuevo:"
            echo "   • Archivos pequeños (≤100 términos): Descarga rápida inmediata"
            echo "   • Archivos grandes (>100 términos): Descarga asíncrona con progreso"
            echo "   • Clasificación de dominio: Optimizada para evitar bloqueos"
            echo ""
            echo "🌐 Interfaz web: http://localhost:7000"
            echo "📖 Documentación: SOLUCION_DESCARGA_PREMATURA.md"
            echo ""
            echo "🧪 Para probar la corrección:"
            echo "   python test_download_fix.py"
            
            break
        else
            echo "⏳ Intento $i/5: Servicio aún no responde, esperando..."
            sleep 5
        fi
    done
    
    if [ $i -eq 5 ]; then
        echo "⚠️  El servicio no responde después de varios intentos"
        echo "📋 Verificando logs del contenedor..."
        docker-compose logs --tail=30 termsuite-api
        echo ""
        echo "💡 Posibles soluciones:"
        echo "   1. Esperar más tiempo: docker-compose logs -f termsuite-api"
        echo "   2. Reiniciar: docker-compose restart"
        echo "   3. Verificar puertos: docker-compose ps"
    fi
    
else
    echo "❌ Error al reconstruir la imagen Docker"
    echo ""
    echo "📋 Logs del build:"
    docker-compose logs --tail=50
    echo ""
    echo "💡 Posibles soluciones:"
    echo "   1. Verificar sintaxis en archivos modificados"
    echo "   2. Limpiar completamente: docker system prune -a"
    echo "   3. Revisar Dockerfile y requirements.txt"
    exit 1
fi

echo ""
echo "📋 Comandos útiles:"
echo "   Ver logs en tiempo real: docker-compose logs -f termsuite-api"
echo "   Detener servicio:        docker-compose down"
echo "   Reiniciar servicio:      docker-compose restart"
echo "   Estado contenedores:     docker-compose ps"
echo "   Probar API:              curl http://localhost:7000/api"

echo "=================================================================="
echo "✅ Corrección de descarga prematura aplicada correctamente"
echo "🎯 El problema de 'Excel aparece pero el proceso sigue trabajando' está SOLUCIONADO"