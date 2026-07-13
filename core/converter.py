"""Conversión del PDF: OCR + metadatos de accesibilidad.

Usa ocrmypdf con --force-ocr --deskew --output-type pdfa: rasteriza cada página
y aplica OCR siempre, nunca deja páginas sin capa de texto, y produce PDF/A.

El único caso en que NO se fuerza OCR es un PDF que ya tiene texto nativo bueno
en todas sus páginas (modo SIN_OCR): forzarlo rasterizaría texto vectorial nítido
y lo empeoraría. Ese se copia y solo se le corrigen los metadatos. Con `forzar`
se puede rehacer el OCR también en ese caso.

Tras el OCR se ajustan con pikepdf los metadatos que anuncian los lectores de
pantalla: /Lang, título XMP y ViewerPreferences/DisplayDocTitle.
"""

import os
import shutil
from pathlib import Path

import ocrmypdf
import pikepdf

from core import progreso as _progreso
from core.analyzer import Diagnostico, Modo
from core.config import IDIOMA_DOCUMENTO, IDIOMA_OCR


class ErrorConversion(Exception):
    pass


class ConversionCancelada(Exception):
    pass


def convertir(
    entrada: str | Path,
    salida: str | Path,
    diag: Diagnostico,
    idioma_ocr: str = IDIOMA_OCR,
    idioma_documento: str = IDIOMA_DOCUMENTO,
    titulo: str | None = None,
    pdfa: bool = True,
    forzar: bool = False,
    progreso=None,
    cancelar=None,
) -> None:
    """Genera en `salida` la versión accesible de `entrada`. Nunca toca el original.

    pdfa: salida en PDF/A (por defecto, como los pipelines de referencia).
    forzar: rehace el OCR incluso si el PDF ya tiene texto nativo bueno.
    progreso: callable(descripcion, fraccion|None) con el avance del OCR.
    cancelar: callable() -> bool; si devuelve True se aborta (ConversionCancelada).
    """
    entrada = Path(entrada)
    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)

    if diag.encriptado:
        raise ErrorConversion('El PDF está protegido con contraseña')
    if diag.error:
        raise ErrorConversion(diag.error)

    if diag.modo == Modo.SIN_OCR and not forzar:
        # Texto nativo bueno en todas las páginas: forzar OCR lo empeoraría.
        # Solo se copia y se corrigen metadatos.
        shutil.copyfile(entrada, salida)
    else:
        try:
            _ejecutar_ocr(entrada, salida, idioma_ocr, titulo, pdfa, progreso, cancelar)
        except ConversionCancelada:
            # Eliminar el archivo parcial para no dejar un PDF corrupto en disco.
            if salida.exists():
                try:
                    salida.unlink()
                except OSError:
                    pass
            raise
        if not salida.exists():
            raise ErrorConversion('El OCR no produjo el archivo de salida')

    _ajustar_metadatos(salida, idioma_documento, titulo or entrada.stem)


def _ejecutar_ocr(entrada, salida, idioma_ocr, titulo, pdfa, progreso, cancelar):
    # Misma receta que procesar_sin_ocr.py / ftp_ocr_pipeline.py.
    opciones: dict = dict(
        language=idioma_ocr,
        output_type='pdfa' if pdfa else 'pdf',
        force_ocr=True,      # rasteriza y OCR de todo, siempre
        deskew=True,         # endereza escaneos torcidos
        jobs=max(1, (os.cpu_count() or 2) - 1),
        progress_bar=False,
        invalidate_digital_signatures=True,
    )
    if titulo:
        opciones['title'] = titulo
    if progreso is not None or cancelar is not None:
        opciones['progress_bar'] = True  # sin esto ocrmypdf no instancia la barra
        opciones['plugins'] = ['core.progreso']
        _progreso.registrar(progreso, cancelar)

    try:
        ocrmypdf.ocr(str(entrada), str(salida), **opciones)
    except _progreso.CancelacionSolicitada as e:
        raise ConversionCancelada() from e
    except ocrmypdf.exceptions.EncryptedPdfError as e:
        raise ErrorConversion('El PDF está protegido con contraseña') from e
    except Exception as e:
        if _fue_cancelacion(e):
            raise ConversionCancelada() from e
        raise ErrorConversion(f'Fallo del OCR: {str(e)[:200]}') from e
    finally:
        _progreso.limpiar()


def _fue_cancelacion(exc: BaseException) -> bool:
    """True si la cancelación viene envuelta en otra excepción del pipeline."""
    visto = set()
    e: BaseException | None = exc
    while e is not None and id(e) not in visto:
        if isinstance(e, _progreso.CancelacionSolicitada):
            return True
        if 'CancelacionSolicitada' in str(e):
            return True
        visto.add(id(e))
        e = e.__cause__ or e.__context__
    return False


def _ajustar_metadatos(ruta: Path, idioma_documento: str, titulo: str) -> None:
    """Fija /Lang, título XMP y DisplayDocTitle — lo que anuncia el lector de pantalla."""
    with pikepdf.open(ruta, allow_overwriting_input=True) as pdf:
        pdf.Root.Lang = pikepdf.String(idioma_documento)

        if '/ViewerPreferences' not in pdf.Root:
            pdf.Root.ViewerPreferences = pikepdf.Dictionary()
        pdf.Root.ViewerPreferences.DisplayDocTitle = True

        with pdf.open_metadata() as meta:
            if not meta.get('dc:title'):
                meta['dc:title'] = titulo

        pdf.save(ruta)
