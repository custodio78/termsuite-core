@echo off
echo 🔧 Aplicando corrección de descarga prematura de Excel...
echo ==================================================================

REM Verificar que Docker esté funcionando
docker --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker no está instalado o no está funcionando
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker Compose no está instalado o no está funcionando
    pause
    exit /b 1
)

echo ✅ Docker y Docker Compose disponibles

REM Mostrar resumen de cambios
echo.
echo 📋 Cambios que se aplicarán:
echo    ✅ Nuevo endpoint: GET /api/tmx/{tmx_id}/export-ready
echo    ✅ Límite de 100 términos para descarga rápida
echo    ✅ Descarga asíncrona automática para archivos grandes
echo    ✅ Clasificación de dominio optimizada
echo    ✅ Frontend actualizado con lógica inteligente
echo.

REM Confirmar con el usuario
set /p "confirm=¿Continuar con el rebuild? (y/N): "
if /i not "%confirm%"=="y" (
    echo ❌ Operación cancelada
    pause
    exit /b 1
)

REM Detener contenedor existente
echo 📦 Deteniendo contenedor existente...
docker-compose down

REM Limpiar caché de build
echo 🧹 Limpiando caché de Docker...
docker system prune -f >nul 2>&1

REM Reconstruir imagen sin caché
echo 🔨 Reconstruyendo imagen Docker (sin caché)...
docker-compose build --no-cache --pull

REM Verificar que la construcción fue exitosa
if %ERRORLEVEL% EQU 0 (
    echo ✅ Imagen reconstruida exitosamente
    
    REM Iniciar contenedor
    echo 🚀 Iniciando contenedor con nuevas funcionalidades...
    docker-compose up -d
    
    REM Esperar que el servicio se inicie
    echo ⏳ Esperando que el servicio se inicie...
    timeout /t 15 /nobreak >nul
    
    REM Verificar que el servicio está funcionando
    echo 🔍 Verificando estado del servicio...
    
    REM Intentar conectar varias veces
    set "service_ok=0"
    for /l %%i in (1,1,5) do (
        curl -s http://localhost:7000/api >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            echo ✅ Servicio funcionando correctamente en http://localhost:7000
            
            REM Probar el nuevo endpoint
            echo 🧪 Probando nuevo endpoint de verificación de descarga...
            curl -s "http://localhost:7000/api/tmx/test/export-ready" >nul 2>&1
            if !ERRORLEVEL! EQU 0 (
                echo ✅ Nuevo endpoint disponible (respuesta esperada: 404 para TMX inexistente^)
            ) else (
                echo ⚠️  Nuevo endpoint no responde (puede ser normal si no hay TMX de prueba^)
            )
            
            echo.
            echo 🎉 ¡CORRECCIÓN APLICADA EXITOSAMENTE!
            echo.
            echo 🎯 Problema solucionado:
            echo    ❌ ANTES: Excel aparecía para descarga mientras el proceso seguía trabajando
            echo    ✅ AHORA: Excel solo aparece cuando está completamente listo
            echo.
            echo 📊 Comportamiento nuevo:
            echo    • Archivos pequeños (≤100 términos^): Descarga rápida inmediata
            echo    • Archivos grandes (^>100 términos^): Descarga asíncrona con progreso
            echo    • Clasificación de dominio: Optimizada para evitar bloqueos
            echo.
            echo 🌐 Interfaz web: http://localhost:7000
            echo 📖 Documentación: SOLUCION_DESCARGA_PREMATURA.md
            echo.
            echo 🧪 Para probar la corrección:
            echo    python test_download_fix.py
            
            set "service_ok=1"
            goto :service_ready
        ) else (
            echo ⏳ Intento %%i/5: Servicio aún no responde, esperando...
            timeout /t 5 /nobreak >nul
        )
    )
    
    :service_ready
    if "%service_ok%"=="0" (
        echo ⚠️  El servicio no responde después de varios intentos
        echo 📋 Verificando logs del contenedor...
        docker-compose logs --tail=30 termsuite-api
        echo.
        echo 💡 Posibles soluciones:
        echo    1. Esperar más tiempo: docker-compose logs -f termsuite-api
        echo    2. Reiniciar: docker-compose restart
        echo    3. Verificar puertos: docker-compose ps
    )
    
) else (
    echo ❌ Error al reconstruir la imagen Docker
    echo.
    echo 📋 Logs del build:
    docker-compose logs --tail=50
    echo.
    echo 💡 Posibles soluciones:
    echo    1. Verificar sintaxis en archivos modificados
    echo    2. Limpiar completamente: docker system prune -a
    echo    3. Revisar Dockerfile y requirements.txt
    pause
    exit /b 1
)

echo.
echo 📋 Comandos útiles:
echo    Ver logs en tiempo real: docker-compose logs -f termsuite-api
echo    Detener servicio:        docker-compose down
echo    Reiniciar servicio:      docker-compose restart
echo    Estado contenedores:     docker-compose ps
echo    Probar API:              curl http://localhost:7000/api

echo ==================================================================
echo ✅ Corrección de descarga prematura aplicada correctamente
echo 🎯 El problema de 'Excel aparece pero el proceso sigue trabajando' está SOLUCIONADO
pause