@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo  =============================================================
echo       OCRFlow -- Instalador de dependencias
echo  =============================================================
echo.

rem -- 1. Verificar Python 3.11+ -----------------------------------------
echo [1/5] Verificando Python...
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado en el PATH.
    echo.
    echo  Descarga Python desde:
    echo    https://www.python.org/downloads/
    echo  Marca "Add Python to PATH" durante la instalacion.
    echo.
    pause
    exit /b 1
)
python -c "import sys; exit(0 if sys.version_info>=(3,11) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Se requiere Python 3.11 o superior.
    for /f "tokens=*" %%V in ('python --version 2^>^&1') do echo  Detectado: %%V
    echo  Descarga: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%V in ('python --version 2^>^&1') do echo [OK] %%V detectado.
echo.

rem -- 2. Entorno virtual ------------------------------------------------
echo [2/5] Configurando entorno virtual...
if exist ".venv\Scripts\python.exe" (
    echo [OK] Entorno virtual existente.
) else (
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
    echo [OK] Entorno virtual creado.
)
echo.

rem -- 3. Dependencias Python --------------------------------------------
echo [3/5] Instalando dependencias Python...
echo  Actualizando pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip -q
echo  Instalando paquetes (puede tardar varios minutos)...
".venv\Scripts\pip.exe" install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Fallo al instalar dependencias Python.
    echo  Verifica la conexion a internet o elimina .venv y reintenta.
    echo.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -c "import PySide6" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PySide6 no se instalo. Elimina .venv y reintenta.
    pause
    exit /b 1
)
echo [OK] Dependencias Python listas.
echo.

rem -- 4. Verificar Tesseract OCR ----------------------------------------
echo [4/5] Verificando Tesseract OCR...
call :check_tesseract
if "%TESS_OK%"=="1" (
    echo [OK] Tesseract OCR detectado.
) else (
    echo [AVISO] Tesseract OCR no encontrado.
    echo  Instala el archivo:
    echo    installer\tesseract-ocr-w64-setup-*.exe
    echo  Activa "Additional language data" y selecciona Spanish.
    echo  Marca "Add to PATH" y reinicia esta ventana tras instalar.
)
echo.

rem -- 5. Verificar Ghostscript ------------------------------------------
echo [5/5] Verificando Ghostscript...
call :check_ghostscript
if "%GS_OK%"=="1" (
    echo [OK] Ghostscript detectado.
) else (
    echo [AVISO] Ghostscript no encontrado.
    echo  Instala el archivo gs*w64.exe de la carpeta installer\
    echo  (necesitas el instalador .exe, no el .zip de GhostPCL).
)
echo.

rem -- Resumen -----------------------------------------------------------
echo  =============================================================
echo   Estado final:
echo.
call :check_tesseract
call :check_ghostscript
if "%TESS_OK%"=="1" (
    echo   [OK] Tesseract OCR
) else (
    echo   [!!] Tesseract OCR -- instalar manualmente
)
if "%GS_OK%"=="1" (
    echo   [OK] Ghostscript
) else (
    echo   [!!] Ghostscript -- instalar manualmente
)
echo.
echo   Para abrir OCRFlow: doble clic en OCRFlow.vbs o ejecutame.bat
echo  =============================================================
echo.
pause
exit /b 0


rem ======================================================================
rem  SUBRUTINAS
rem ======================================================================

:check_tesseract
set TESS_OK=0
where tesseract >nul 2>&1
if not errorlevel 1 ( set TESS_OK=1 & goto :eof )
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe"        set TESS_OK=1 & goto :eof
if exist "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"  set TESS_OK=1
goto :eof

:check_ghostscript
set GS_OK=0
where gswin64c >nul 2>&1
if not errorlevel 1 ( set GS_OK=1 & goto :eof )
where gswin32c >nul 2>&1
if not errorlevel 1 ( set GS_OK=1 & goto :eof )
where gs >nul 2>&1
if not errorlevel 1 ( set GS_OK=1 & goto :eof )
if exist "C:\Program Files\gs" (
    for /d %%D in ("C:\Program Files\gs\*") do (
        if exist "%%D\bin\gswin64c.exe" ( set GS_OK=1 & goto :eof )
        if exist "%%D\bin\gswin32c.exe" ( set GS_OK=1 & goto :eof )
    )
)
goto :eof
