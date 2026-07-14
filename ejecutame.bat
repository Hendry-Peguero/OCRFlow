@echo off
cd /d "%~dp0"

rem -- 1. Verificar entorno virtual --------------------------------------
if not exist ".venv\Scripts\pythonw.exe" (
    echo.
    echo [ERROR] Entorno virtual no encontrado.
    echo.
    echo  Ejecuta primero el instalador:
    echo     instalador.bat
    echo.
    pause
    exit /b 1
)

rem -- 2. Verificar que PySide6 esta disponible --------------------------
".venv\Scripts\python.exe" -c "import PySide6" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Las dependencias no estan completas.
    echo.
    echo  PySide6 no se pudo importar. Posibles causas:
    echo    - La instalacion fallo o quedo incompleta.
    echo    - La version de Python no es compatible (se requiere 3.11 o superior).
    echo.
    echo  Solucion: elimina la carpeta .venv y ejecuta instalador.bat de nuevo.
    echo.
    pause
    exit /b 1
)

rem -- 3. Lanzar la aplicacion -------------------------------------------
start "OCRFlow" /NORMAL "%~dp0.venv\Scripts\pythonw.exe" "%~dp0gui\app.py"
