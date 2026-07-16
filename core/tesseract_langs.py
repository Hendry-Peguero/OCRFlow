"""Detección e instalación automática de paquetes de idioma de Tesseract OCR.

Los archivos .traineddata se descargan del repositorio oficial de Tesseract en GitHub.
Si el directorio tessdata del sistema no tiene permisos de escritura, se intenta
elevar privilegios con UAC (solo Windows).
"""

import ctypes
import ctypes.wintypes as _wt
import os
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

_TESSDATA_URL = (
    'https://github.com/tesseract-ocr/tessdata/raw/main/{lang}.traineddata'
)

_CREATE_NO_WINDOW = 0x08000000  # flag de Windows para no abrir ventana CMD


# ── Inicialización ──────────────────────────────────────────────────────────────

def inicializar() -> None:
    """Corrige el entorno para que Tesseract funcione aunque no esté en PATH.

    Debe llamarse una vez al arrancar la app, antes de cualquier llamada a OCR.
    Resuelve dos problemas comunes en instalaciones silenciosas:
    1. TESSDATA_PREFIX malo → tesseract devuelve exit-code 1 en deskew.
    2. Tesseract instalado pero no en PATH → ocrmypdf no encuentra el ejecutable.
    """
    # ── Fix 1: TESSDATA_PREFIX inválido ──────────────────────────────────────
    prefix = os.environ.get('TESSDATA_PREFIX', '')
    if prefix and not Path(prefix).is_dir():
        del os.environ['TESSDATA_PREFIX']

    # ── Fix 2: Tesseract instalado pero no en PATH ───────────────────────────
    # ocrmypdf llama a 'tesseract' por nombre como subproceso; si no está en
    # PATH la conversión falla aunque el exe exista en disco.
    if not shutil.which('tesseract'):
        tess = encontrar_tesseract()
        if tess:
            os.environ['PATH'] = str(tess.parent) + os.pathsep + os.environ.get('PATH', '')


# ── Localización ────────────────────────────────────────────────────────────────

def encontrar_tesseract() -> Path | None:
    """Devuelve la ruta al ejecutable tesseract, o None si no está instalado."""
    tess = shutil.which('tesseract')
    if tess:
        return Path(tess)
    pf = os.environ.get('ProgramFiles', r'C:\Program Files')
    candidate = Path(pf, 'Tesseract-OCR', 'tesseract.exe')
    return candidate if candidate.exists() else None


def encontrar_tessdata() -> Path | None:
    """Devuelve el directorio tessdata activo, o None si no se encuentra."""
    # TESSDATA_PREFIX puede apuntar al padre de tessdata/ o a tessdata/ directamente
    prefix = os.environ.get('TESSDATA_PREFIX')
    if prefix:
        p = Path(prefix)
        if (p / 'tessdata').is_dir():
            return p / 'tessdata'
        if p.is_dir():
            return p

    tess = encontrar_tesseract()
    if tess:
        tessdata = tess.parent / 'tessdata'
        if tessdata.is_dir():
            return tessdata
    return None


# ── Consulta ────────────────────────────────────────────────────────────────────

def listar_instalados() -> list[str]:
    """Lista los códigos de idioma instalados en Tesseract."""
    tess = encontrar_tesseract()
    if not tess:
        return []
    try:
        r = subprocess.run(
            [str(tess), '--list-langs'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=10,
            creationflags=_CREATE_NO_WINDOW,
        )
        # Distintas versiones de Tesseract mandan la lista a stdout o stderr
        salida = (r.stdout or '') + (r.stderr or '')
        return [
            line.strip()
            for line in salida.splitlines()
            if line.strip()
            and not line.lower().startswith('list')
            and not line.lower().startswith('warning')
            and not line.lower().startswith('error')
        ]
    except Exception:
        return []


def idiomas_faltantes(idioma_ocr: str) -> list[str]:
    """Dado un string como 'spa+eng+fra', devuelve los códigos no instalados."""
    codigos = [c.strip() for c in idioma_ocr.split('+') if c.strip()]
    instalados = set(listar_instalados())
    return [c for c in codigos if c not in instalados]


# ── Instalación ─────────────────────────────────────────────────────────────────

def instalar_idioma(codigo: str, progreso=None) -> None:
    """Descarga e instala el traineddata para `codigo`.

    progreso: callable(descripcion: str, fraccion: float | None)

    Raises:
        ValueError      — tessdata no encontrado
        IOError         — fallo de descarga
        PermissionError — sin permisos y UAC rechazado
    """
    tessdata = encontrar_tessdata()
    if tessdata is None:
        raise ValueError(
            'No se encontró el directorio tessdata de Tesseract.\n'
            'Verifica que Tesseract esté instalado correctamente.'
        )

    destino = tessdata / f'{codigo}.traineddata'
    url = _TESSDATA_URL.format(lang=codigo)

    # Descarga a fichero temporal para no dejar basura si algo falla
    tmp_fd, tmp_str = tempfile.mkstemp(suffix='.traineddata', prefix=f'tess_{codigo}_')
    os.close(tmp_fd)
    tmp = Path(tmp_str)

    try:
        def _reporthook(count, block_size, total_size):
            if progreso and total_size > 0:
                bajados = min(count * block_size, total_size)
                progreso(
                    f'Descargando "{codigo}"… '
                    f'{bajados // 1024} KB / {total_size // 1024} KB',
                    bajados / total_size,
                )

        if progreso:
            progreso(f'Conectando para descargar "{codigo}"…', None)
        try:
            urllib.request.urlretrieve(url, tmp, reporthook=_reporthook)
        except Exception as e:
            raise IOError(
                f'No se pudo descargar el paquete de idioma "{codigo}".\n'
                f'Verifica la conexión a Internet.\n\nDetalle: {e}'
            ) from e

        if progreso:
            progreso(f'Instalando "{codigo}"…', None)

        # Intento directo
        try:
            shutil.copy2(str(tmp), str(destino))
            return
        except PermissionError:
            pass

        # Elevación UAC (Windows)
        _copiar_con_uac(tmp, destino)

    finally:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass


def _copiar_con_uac(origen: Path, destino: Path) -> None:
    """Copia un archivo usando ShellExecuteExW con verbo 'runas' (UAC, solo Windows)."""

    class _SHELLEXECUTEINFOW(ctypes.Structure):
        _fields_ = [
            ('cbSize',         _wt.DWORD),
            ('fMask',          _wt.ULONG),
            ('hwnd',           _wt.HWND),
            ('lpVerb',         _wt.LPCWSTR),
            ('lpFile',         _wt.LPCWSTR),
            ('lpParameters',   _wt.LPCWSTR),
            ('lpDirectory',    _wt.LPCWSTR),
            ('nShow',          ctypes.c_int),
            ('hInstApp',       _wt.HINSTANCE),
            ('lpIDList',       ctypes.c_void_p),
            ('lpClass',        _wt.LPCWSTR),
            ('hkeyClass',      _wt.HKEY),
            ('dwHotKey',       _wt.DWORD),
            ('hIconOrMonitor', _wt.HANDLE),
            ('hProcess',       _wt.HANDLE),
        ]

    SEE_MASK_NOCLOSEPROCESS = 0x40

    origen_str  = str(origen).replace("'", '"')
    destino_str = str(destino).replace("'", '"')
    ps_params = (
        f'-NoProfile -NonInteractive -Command '
        f'"Copy-Item -LiteralPath \'{origen_str}\' -Destination \'{destino_str}\' -Force"'
    )

    sei = _SHELLEXECUTEINFOW()
    sei.cbSize   = ctypes.sizeof(sei)
    sei.fMask    = SEE_MASK_NOCLOSEPROCESS
    sei.lpVerb   = 'runas'
    sei.lpFile   = 'powershell.exe'
    sei.lpParameters = ps_params
    sei.nShow    = 0  # SW_HIDE

    shell32 = ctypes.windll.shell32
    kernel32 = ctypes.windll.kernel32

    if not shell32.ShellExecuteExW(ctypes.byref(sei)):
        err = ctypes.GetLastError()
        raise PermissionError(
            f'El usuario canceló la elevación de permisos (código {err}).\n'
            'Para instalar el idioma, ejecuta la aplicación como administrador.'
        )

    try:
        kernel32.WaitForSingleObject(sei.hProcess, 30_000)  # máx 30 s
        exit_code = _wt.DWORD()
        kernel32.GetExitCodeProcess(sei.hProcess, ctypes.byref(exit_code))
        if exit_code.value != 0:
            raise PermissionError(
                f'La copia con permisos de administrador falló (código {exit_code.value}).\n'
                'Ejecuta la aplicación como administrador.'
            )
    finally:
        kernel32.CloseHandle(sei.hProcess)

    if not destino.exists():
        raise PermissionError(
            'La instalación no se completó correctamente.\n'
            'Ejecuta la aplicación como administrador.'
        )
