@echo off
cd /d "%~dp0"

rem ── Verificar que el entorno virtual esta instalado ───────────────────────────
if not exist ".venv\Scripts\pythonw.exe" (
    echo [ERROR] El entorno virtual no esta instalado.
    echo.
    echo  Ejecuta primero el instalador haciendo doble clic en:
    echo     instalador.bat
    echo.
    pause
    exit /b 1
)

rem ── Lanzar la aplicacion sin ventana de consola ───────────────────────────────
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0gui\app.py"
