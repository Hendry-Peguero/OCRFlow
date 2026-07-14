@echo off
rem ---------------------------------------------------------------------------
rem  Build de PDF Accesible — PyInstaller + Inno Setup
rem
rem  Requisitos previos:
rem    • Python con el venv en .venv\ (pip install pyinstaller si hace falta)
rem    • Inno Setup 6  https://jrsoftware.org/isdl.php
rem    • installer\deps\tesseract-setup.exe  (UB-Mannheim, versión w64)
rem    • installer\deps\gs-setup.exe         (Ghostscript para Windows 64-bit)
rem
rem  Uso: doble clic en este archivo (o ejecútalo desde la raíz del proyecto)
rem ---------------------------------------------------------------------------

cd /d "%~dp0.."

echo.
echo --------------------------------------------------------
echo   Paso 1 de 2: empaquetando con PyInstaller
echo --------------------------------------------------------
echo.

rem Instala PyInstaller si no está disponible
.venv\Scripts\python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Instalando PyInstaller en el venv...
    .venv\Scripts\pip install pyinstaller
    if errorlevel 1 goto error
)

.venv\Scripts\pyinstaller installer\pdf_accesible.spec --noconfirm
if errorlevel 1 goto error

echo.
echo --------------------------------------------------------
echo   Paso 2 de 2: compilando instalador con Inno Setup
echo --------------------------------------------------------
echo.

rem Busca Inno Setup en las rutas de instalación habituales
set ISCC=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe"       set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"

if "%ISCC%"=="" (
    echo ERROR: No se encontró Inno Setup 6.
    echo Descárgalo de https://jrsoftware.org/isdl.php e instálalo.
    goto error
)

%ISCC% installer\setup.iss
if errorlevel 1 goto error

echo.
echo --------------------------------------------------------
echo   Listo.
echo   Instalador: installer\Output\PDF_Accesible_Instalador_v1.0.0.exe
echo --------------------------------------------------------
goto fin

:error
echo.
echo ERROR: el proceso falló con código %errorlevel%.
echo Revisa los mensajes anteriores para más detalles.
pause
exit /b 1

:fin
pause
