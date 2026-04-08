@echo off
title Agente de Soporte DIAN
echo ========================================
echo    AGENTE DE SOPORTE TECNICO DIAN
echo ========================================
echo.

:: Activar entorno virtual si existe
if exist venv\Scripts\activate (
    call venv\Scripts\activate
)

:: Verificar Python
python --version
if errorlevel 1 (
    echo ERROR: Python no encontrado. Instala Python 3.10 o superior.
    pause
    exit /b 1
)

:: Instalar dependencias si es necesario
if not exist venv\Scripts\activate (
    echo.
    echo Creando entorno virtual...
    python -m venv venv
    call venv\Scripts\activate
    echo Instalando dependencias...
    pip install -r requirements.txt
)

echo.
echo ========================================
echo    SELECCIONA UNA OPCION:
echo ========================================
echo.
echo 1. Iniciar interfaz web (Streamlit)
echo 2. Modo línea de comandos
echo 3. Cargar manuales desde carpeta data/manuales
echo 4. Salir
echo.

set /p opcion="Opcion: "

if "%opcion%"=="1" (
    echo.
    echo Iniciando interfaz web...
    streamlit run app.py
) else if "%opcion%"=="2" (
    echo.
    echo Modo línea de comandos...
    python cli.py
) else if "%opcion%"=="3" (
    echo.
    echo Cargando manuales...
    python cli.py --load-manuals
    pause
) else (
    echo.
    echo Saliendo...
    exit
)