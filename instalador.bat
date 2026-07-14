@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo  =============================================================
echo       OCRFlow -- Instalador de dependencias
echo  =============================================================
echo.

rem -- 1. Verificar que Python existe ------------------------------------
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado en el PATH.
    echo.
    echo  Descarga Python desde:
    echo    https://www.python.org/downloads/
    echo.
    echo  IMPORTANTE: marca "Add Python to PATH" durante la instalacion.
    echo.
    pause
    exit /b 1
)

rem -- 2. Verificar version minima (3.11+) ------------------------------
set USE_PY=python

python -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Se requiere Python 3.11 o superior.
    echo.
    echo  Descarga la ultima version desde:
    echo    https://www.python.org/downloads/
    echo  Marca "Add Python to PATH" durante la instalacion.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%V in ('python --version 2^>^&1') do echo [OK] %%V detectado.
echo.

rem -- 3. Crear entorno virtual ------------------------------------------
if exist ".venv\Scripts\python.exe" (
    echo [OK] Entorno virtual ya existe, omitiendo creacion.
    echo      Si hay problemas, elimina la carpeta .venv y ejecuta de nuevo.
) else (
    echo Creando entorno virtual en .venv\ ...
    %USE_PY% -m venv .venv
    if errorlevel 1 (
        echo.
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
    echo [OK] Entorno virtual creado.
)
echo.

rem -- 4. Actualizar pip -------------------------------------------------
echo Actualizando pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip -q
echo.

rem -- 5. Instalar dependencias ------------------------------------------
echo Instalando dependencias Python (requirements.txt)...
echo Esto puede tardar varios minutos la primera vez...
echo.
".venv\Scripts\pip.exe" install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Fallo al instalar dependencias.
    echo.
    echo  Posibles causas:
    echo    - Sin conexion a internet.
    echo    - Version de Python incompatible con PySide6.
    echo.
    echo  Solucion: elimina la carpeta .venv, instala la ultima version de
    echo  Python desde https://www.python.org/downloads/
    echo  y ejecuta este instalador de nuevo.
    echo.
    pause
    exit /b 1
)

rem -- 6. Confirmar que PySide6 importa correctamente --------------------
".venv\Scripts\python.exe" -c "import PySide6" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] PySide6 no se instalo correctamente.
    echo.
    echo  La version de Python instalada puede no ser compatible.
    echo  Instala Python 3.13 desde:
    echo    https://www.python.org/downloads/release/python-3130/
    echo  Luego elimina la carpeta .venv y ejecuta este instalador de nuevo.
    echo.
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas y verificadas.
echo.

rem -- 7. Verificar Tesseract OCR ----------------------------------------
echo -------------------------------------------------------------
echo Verificando dependencias externas del sistema...
echo.

set TESS_OK=0
where tesseract >nul 2>&1
if not errorlevel 1 set TESS_OK=1
if "%TESS_OK%"=="0" (
    if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" set TESS_OK=1
)
if "%TESS_OK%"=="0" (
    if exist "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" set TESS_OK=1
)

if "%TESS_OK%"=="1" (
    echo [OK] Tesseract OCR detectado.
) else (
    echo [AVISO] Tesseract OCR no encontrado.
    echo.
    echo  La conversion OCR no funcionara sin Tesseract.
    echo    1. Descarga Windows 64-bit desde:
    echo       https://github.com/UB-Mannheim/tesseract/releases
    echo    2. Activa los idiomas Spanish y English durante la instalacion.
    echo    3. Marca "Add Tesseract to PATH" o reinicia tras instalar.
    echo.
)

rem -- 8. Verificar Ghostscript ------------------------------------------
set GS_OK=0
where gswin64c >nul 2>&1
if not errorlevel 1 set GS_OK=1
where gswin32c >nul 2>&1
if not errorlevel 1 set GS_OK=1

if exist "C:\Program Files\gs" (
    for /f "delims=" %%D in ('dir /b /ad "C:\Program Files\gs" 2^>nul') do (
        if exist "C:\Program Files\gs\%%D\bin\gswin64c.exe" set GS_OK=1
    )
)

if "%GS_OK%"=="1" (
    echo [OK] Ghostscript detectado.
) else (
    echo [AVISO] Ghostscript no encontrado.
    echo.
    echo  La generacion de PDF/A no funcionara sin Ghostscript.
    echo  Descarga Windows 64-bit desde:
    echo    https://www.ghostscript.com/releases/gsdnld.html
    echo.
)

echo.
echo  =============================================================
echo   OCRFlow instalado correctamente.
echo.
echo   Para iniciar la aplicacion haz doble clic en:
echo      ejecutame.bat
echo  =============================================================
echo.
pause
