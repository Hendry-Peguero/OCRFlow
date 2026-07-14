@echo off
rem Lanzador de la aplicacion PDF Accesible.
rem Doble clic para abrir la interfaz grafica sin usar la terminal.
cd /d "%~dp0"
start "" ".venv\Scripts\pythonw.exe" "gui\app.py"
