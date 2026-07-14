@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo  =============================================================
echo       OCRFlow -- Instalador de dependencias
echo  =============================================================
echo.

rem -- 1. Verificar Python 3.11+ -----------------------------------------
echo [1/6] Verificando Python...
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
echo [2/6] Configurando entorno virtual...
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
echo [3/6] Instalando dependencias Python...
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

rem -- 4. Tesseract OCR --------------------------------------------------
echo [4/6] Verificando Tesseract OCR...
call :check_tesseract
if "%TESS_OK%"=="1" (
    echo [OK] Tesseract OCR ya esta instalado.
) else (
    echo  Instalando Tesseract OCR automaticamente...
    echo.
    call :install_tesseract
    call :check_tesseract
    if "!TESS_OK!"=="1" (
        echo [OK] Tesseract OCR instalado.
    ) else (
        echo.
        echo [AVISO] Instalacion automatica no disponible.
        echo  Instala manualmente:
        echo    https://github.com/UB-Mannheim/tesseract/releases
        echo    Archivo: tesseract-ocr-w64-setup-*.exe
        echo    Activa "Additional language data" y selecciona Spanish.
        echo    Marca "Add to PATH".
        echo.
    )
)
call :check_tesseract
if "%TESS_OK%"=="1" call :instalar_espanol
echo.

rem -- 5. Ghostscript ----------------------------------------------------
echo [5/6] Verificando Ghostscript...
call :check_ghostscript
if "%GS_OK%"=="1" (
    echo [OK] Ghostscript ya esta instalado.
) else (
    echo  Instalando Ghostscript automaticamente...
    echo.
    call :install_ghostscript
    call :check_ghostscript
    if "!GS_OK!"=="1" (
        echo [OK] Ghostscript instalado.
    ) else (
        echo.
        echo [AVISO] Instalacion automatica no disponible.
        echo  Instala manualmente:
        echo    https://github.com/ArtifexSoftware/ghostpdl-downloads/releases
        echo    Archivo: gs*w64.exe
        echo.
    )
)
echo.

rem -- 6. Resumen --------------------------------------------------------
echo  =============================================================
echo   Instalacion completada.
echo.
call :check_tesseract
call :check_ghostscript
if "%TESS_OK%"=="1" (
    echo   [OK] Tesseract OCR
) else (
    echo   [!!] Tesseract OCR -- ver instrucciones arriba
)
if "%GS_OK%"=="1" (
    echo   [OK] Ghostscript
) else (
    echo   [!!] Ghostscript -- ver instrucciones arriba
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

:install_tesseract
where winget >nul 2>&1
if not errorlevel 1 (
    echo  [winget] Instalando UB-Mannheim.TesseractOCR...
    winget install --id UB-Mannheim.TesseractOCR --silent --accept-source-agreements --accept-package-agreements
    goto :eof
)
echo  [PS] Buscando ultima version en GitHub...
set _PS=%temp%\inst_tess.ps1
(
    echo [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
    echo try {
    echo   $r = Invoke-RestMethod 'https://api.github.com/repos/UB-Mannheim/tesseract/releases/latest'
    echo   $a = $r.assets ^| Where-Object {$_.name -match 'w64-setup.*\.exe'} ^| Select-Object -First 1
    echo   if ($a) {
    echo     Write-Host "Descargando $($a.name)..."
    echo     Invoke-WebRequest $a.browser_download_url -OutFile "$env:TEMP\tess_setup.exe" -UseBasicParsing
    echo     Start-Process "$env:TEMP\tess_setup.exe" -ArgumentList '/S' -Verb RunAs -Wait
    echo   } else { Write-Warning "No se encontro el instalador." }
    echo } catch { Write-Error $_ }
) > "%_PS%"
powershell -ExecutionPolicy Bypass -File "%_PS%"
del "%_PS%" >nul 2>&1
goto :eof

:instalar_espanol
set _TESSDATA=
if exist "C:\Program Files\Tesseract-OCR\tessdata"        set _TESSDATA=C:\Program Files\Tesseract-OCR\tessdata
if exist "C:\Program Files (x86)\Tesseract-OCR\tessdata"  set _TESSDATA=C:\Program Files (x86)\Tesseract-OCR\tessdata
if "%_TESSDATA%"=="" goto :eof
if exist "%_TESSDATA%\spa.traineddata" (
    echo  [OK] Idioma espanol ya disponible.
    goto :eof
)
echo  Descargando spa.traineddata (idioma espanol)...
set _PS=%temp%\dl_spa.ps1
(
    echo [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
    echo $dest = $env:_TESSDATA + '\spa.traineddata'
    echo try {
    echo   Invoke-WebRequest 'https://github.com/tesseract-ocr/tessdata/raw/main/spa.traineddata' -OutFile $dest -UseBasicParsing
    echo   Write-Host "spa.traineddata descargado."
    echo } catch { Write-Error $_ }
) > "%_PS%"
powershell -ExecutionPolicy Bypass -File "%_PS%"
del "%_PS%" >nul 2>&1
if exist "%_TESSDATA%\spa.traineddata" (
    echo  [OK] Idioma espanol instalado.
) else (
    echo  [AVISO] No se pudo descargar spa.traineddata.
)
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

:install_ghostscript
where winget >nul 2>&1
if not errorlevel 1 (
    echo  [winget] Instalando ArtifexSoftware.GhostScript...
    winget install --id ArtifexSoftware.GhostScript --silent --accept-source-agreements --accept-package-agreements
    goto :eof
)
echo  [PS] Buscando ultima version en GitHub...
set _PS=%temp%\inst_gs.ps1
(
    echo [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
    echo try {
    echo   $r = Invoke-RestMethod 'https://api.github.com/repos/ArtifexSoftware/ghostpdl-downloads/releases/latest'
    echo   $a = $r.assets ^| Where-Object {$_.name -match 'gs\d+w64.*\.exe'} ^| Select-Object -First 1
    echo   if ($a) {
    echo     Write-Host "Descargando $($a.name)..."
    echo     Invoke-WebRequest $a.browser_download_url -OutFile "$env:TEMP\gs_setup.exe" -UseBasicParsing
    echo     Start-Process "$env:TEMP\gs_setup.exe" -ArgumentList '/S' -Verb RunAs -Wait
    echo   } else { Write-Warning "No se encontro el instalador." }
    echo } catch { Write-Error $_ }
) > "%_PS%"
powershell -ExecutionPolicy Bypass -File "%_PS%"
del "%_PS%" >nul 2>&1
goto :eof
