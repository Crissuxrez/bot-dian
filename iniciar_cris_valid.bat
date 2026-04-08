@echo off
title Cris Valid - Agente de Soporte Técnico

:: Código de escape ANSI (carácter 27)
for /F "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do set "ESC=%%b"

:: Colores
set "AZUL=%ESC%[94m"
set "RESET=%ESC%[0m"

echo %AZUL%==============================================%RESET%
echo %AZUL%    Cris Valid - Validador Fiscal%RESET%
echo %AZUL%==============================================%RESET%
echo.

:: Verificar si existe el entorno virtual
if not exist "venv\Scripts\activate.bat" (
    echo %AZUL%[ERROR] No se encuentra el entorno virtual.%RESET%
    echo Ejecute primero: python -m venv venv
    pause
    exit /b 1
)

:: Activar el entorno virtual
call venv\Scripts\activate.bat

:: Verificar que Streamlit esté instalado
streamlit --version >nul 2>nul
if %errorlevel% neq 0 (
    echo %AZUL%[ERROR] Streamlit no instalado.%RESET%
    echo Ejecute: pip install streamlit
    pause
    exit /b 1
)

:: Lanzar la aplicación
echo %AZUL%Iniciando Cris Valid...%RESET%
echo.
streamlit run app.py

:: Al cerrar Streamlit, desactivar el entorno (opcional)
call deactivate
pause