@echo off
cd /d "%~dp0"
echo Iniciando diagnostico...
echo.

".venv\Scripts\python.exe" -c "
import sys, traceback
sys.path.insert(0, '.')
try:
    from gui.app import main
    main()
except Exception:
    with open('crash_log.txt', 'w', encoding='utf-8') as f:
        traceback.print_exc(file=f)
    print('ERROR guardado en crash_log.txt')
    import traceback
    traceback.print_exc()
" 2>&1

echo.
echo Proceso terminado con codigo: %errorlevel%
pause
