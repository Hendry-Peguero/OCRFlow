@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo.
echo  ╔═══════════════════════════════════════════════════════════╗
echo  ║           OCRFlow — Instalador de dependencias            ║
echo  ╚═══════════════════════════════════════════════════════════╝
echo.

rem ── 1. Verificar Python ──────────────────────────────────────────────────────
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado en el PATH.
    echo.
    echo  Descarga Python 3.13+ desde:
    echo    https://www.python.org/downloads/
    echo.
    echo  IMPORTANTE: durante la instalacion marca la casilla
    echo  "Add Python to PATH" antes de hacer clic en Install Now.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%V in ('python --version 2^>^&1') do set PY_VER=%%V
echo [OK] %PY_VER% detectado.
echo.

rem ── 2. Crear entorno virtual ──────────────────────────────────────────────────
if exist ".venv\Scripts\python.exe" (
    echo [OK] Entorno virtual ya existe, omitiendo creacion.
) else (
    echo Creando entorno virtual en .venv\ ...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
    echo [OK] Entorno virtual creado.
)
echo.

rem ── 3. Actualizar pip ─────────────────────────────────────────────────────────
echo Actualizando pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip -q
echo.

rem ── 4. Instalar dependencias Python ──────────────────────────────────────────
echo Instalando dependencias Python (requirements.txt)...
echo Esto puede tardar varios minutos la primera vez...
echo.
".venv\Scripts\pip.exe" install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Fallo al instalar dependencias.
    echo Comprueba tu conexion a internet y vuelve a ejecutar este instalador.
    pause
    exit /b 1
)
echo.
echo [OK] Dependencias Python instaladas.
echo.

rem ── 5. Verificar Tesseract OCR ────────────────────────────────────────────────
echo ─────────────────────────────────────────────────────────────
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
    echo  Pasos para instalarlo:
    echo    1. Descarga el instalador Windows 64-bit desde:
    echo       https://github.com/UB-Mannheim/tesseract/releases
    echo       ^(archivo: tesseract-ocr-w64-setup-X.X.X.exe^)
    echo    2. Durante la instalacion activa los idiomas Spanish y English.
    echo    3. Marca la opcion "Add Tesseract to PATH" o reinicia el equipo.
    echo.
)

rem ── 6. Verificar Ghostscript ──────────────────────────────────────────────────
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
    echo  Descarga la version Windows 64-bit desde:
    echo    https://www.ghostscript.com/releases/gsdnld.html
    echo.
)

echo.
echo ═════════════════════════════════════════════════════════════
echo  OCRFlow instalado correctamente.
echo.
echo  Para iniciar la aplicacion haz doble clic en:
echo     ejecutame.bat
echo ═════════════════════════════════════════════════════════════
echo.
pause
