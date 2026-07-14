# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec para PDF Accesible.

Uso:
    .venv\Scripts\pyinstaller installer\pdf_accesible.spec --noconfirm
"""
from pathlib import Path

ROOT = Path(SPECPATH)

a = Analysis(
    [str(ROOT / 'gui' / 'app.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=[
        # Plugin de progreso: ocrmypdf lo carga por nombre de módulo
        'core.progreso',
        # ocrmypdf usa pluggy para descubrir plugins
        'ocrmypdf._plugin_manager',
        'ocrmypdf.builtin_plugins',
        'ocrmypdf.builtin_plugins.tesseract_ocr',
        'ocrmypdf.builtin_plugins.ghostscript',
        'ocrmypdf.builtin_plugins.optimize',
        'ocrmypdf.builtin_plugins.output_type',
        'ocrmypdf.builtin_plugins.pdfa',
        'ocrmypdf.builtin_plugins.pdfinfo',
        'ocrmypdf.builtin_plugins.validate',
        # PIL backends
        'PIL._imaging',
        'PIL.Image',
        # pdfminer (usado por pdfplumber)
        'pdfminer',
        'pdfminer.high_level',
        'pdfminer.layout',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PDF Accesible',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # sin ventana de consola
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Descomenta si tienes un icono .ico:
    # icon=str(ROOT / 'gui' / 'icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PDF Accesible',
)
