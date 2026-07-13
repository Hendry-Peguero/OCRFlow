"""Plugin de OCRmyPDF que reenvía el progreso del OCR a quien lo registre.

OCRmyPDF no expone un callback de progreso en su API; su mecanismo oficial es
un plugin que sustituye la clase de barra de progreso. Este módulo implementa
esa clase y un registro global (una conversión a la vez) para que la GUI o el
CLI reciban (descripción, fracción) por cada avance, y puedan cancelar el
proceso a mitad de un archivo.
"""

from ocrmypdf import hookimpl

_callback = None    # callable(desc: str, fraccion: float | None)
_cancelar = None    # callable() -> bool


class CancelacionSolicitada(Exception):
    """Lanzada dentro del pipeline de OCRmyPDF para abortar la conversión."""


def registrar(callback=None, cancelar=None) -> None:
    global _callback, _cancelar
    _callback = callback
    _cancelar = cancelar


def limpiar() -> None:
    registrar(None, None)


class _Barra:
    """Cumple el protocolo ProgressBar de ocrmypdf (context manager + update)."""

    def __init__(self, *args, total=None, desc=None, unit=None, disable=False, **kwargs):
        self.total = total
        self.desc = desc or ''
        self.avance = 0.0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def update(self, n=1, *, completed=None):
        if _cancelar is not None and _cancelar():
            raise CancelacionSolicitada()
        if completed is not None:
            self.avance = completed
        else:
            self.avance += n if n is not None else 1
        if _callback is not None:
            fraccion = min(self.avance / self.total, 1.0) if self.total else None
            _callback(self.desc, fraccion)


@hookimpl
def get_progressbar_class():
    return _Barra
