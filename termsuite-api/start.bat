@echo off
REM Script de inicio para TermSuite API (Windows)

echo ==========================================
echo   TermSuite API - Inicio
echo ==========================================
echo.

REM Verificar Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker no esta instalado
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Compose no esta instalado
    pause
    exit /b 1
)

REM Verificar JAR
if not exist "termsuite\termsuite-core-3.0.10.jar" (
    echo ADVERTENCIA: JAR de TermSuite no encontrado
    echo Por favor, coloca termsuite-core-3.0.10.jar en la carpeta termsuite\
    echo.
    pause
)

REM Crear directorios
echo Creando directorios...
if not exist "data\uploads" mkdir data\uploads
if not exist "data\corpus" mkdir data\corpus
if not exist "data\outputs" mkdir data\outputs
if not exist "termsuite" mkdir termsuite

REM Construir y ejecutar
echo Construyendo contenedor Docker...
docker-compose build

echo Iniciando servicios...
docker-compose up -d

echo.
echo TermSuite API iniciada
echo.
echo Endpoints disponibles:
echo    - API: http://localhost:7000
echo    - Docs: http://localhost:7000/docs
echo.
echo Comandos utiles:
echo    - Ver logs: docker-compose logs -f
echo    - Detener: docker-compose down
echo    - Reiniciar: docker-compose restart
echo.
pause
