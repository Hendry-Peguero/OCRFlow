"""Diagnóstico del PDF de entrada: decide qué tratamiento necesita.

La detección de capa de texto está portada de `validar_ocr_pdfs.py` (el validador
de OCR verificado sobre ~9199 PDFs): extracción por página con pypdf (respaldo
pdfplumber), medición de DENSIDAD de caracteres por página, detección de fuentes
e imágenes, y muestreo en documentos largos. Esa densidad es la clave: un escaneo
con números de página o marcas de agua tiene "algo de texto" en cada página pero
una densidad ridícula — la medida ingenua anterior lo marcaba como accesible.

Sobre esa base se elige el modo de conversión y, de forma conservadora, si el
documento ya es legible por un lector de pantalla.
"""

import io
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from pypdf import PdfReader

from core.config import (
    COBERTURA_TEXTO_ALTA, DENSIDAD_MIN_CHARS, MAX_PAGINAS_ANALISIS,
    MIN_OCR_CHARS, MIN_OCR_QUALITY, OCR_GARBAGE_RATIO, OCR_SAMPLE_CHARS,
    PAGE_TEXT_MIN_CHARS, SCORE_OCR_MINIMO,
)

# Caracteres "legibles": letras (cualquier idioma vía isalpha), dígitos, espacios
# y signos de puntuación/tipografía comunes.
_PUNCT = set(' .,;:!?¿¡()[]{}-–—/\\@#%&*+=<>"\'«»“”‘’|°ºª…\n\t\r')


class Modo(str, Enum):
    OCR_COMPLETO = 'ocr_completo'   # sin texto: OCR de todo el documento
    OCR_PARCIAL = 'ocr_parcial'     # mixto: OCR solo de las páginas sin texto
    REHACER_OCR = 'rehacer_ocr'     # texto basura o de baja calidad: rehacer el OCR
    SIN_OCR = 'sin_ocr'             # texto bueno en todas las páginas: solo metadatos/tags


@dataclass
class Diagnostico:
    ruta: str
    paginas: int = 0
    paginas_analizadas: int = 0
    paginas_con_texto: int = 0
    paginas_solo_imagen: int = 0
    caracteres: int = 0
    chars_por_pagina: float = 0.0
    ratio_legible: float = 0.0
    ratio_basura: float = 0.0
    score_ocr: int = 0
    tiene_ocr: bool = False          # legible por lector de pantalla (criterio validado)
    tiene_fuentes: bool = False
    tiene_imagenes: bool = False
    tiene_tags: bool = False
    muestreado: bool = False
    encriptado: bool = False
    error: str | None = None
    razones: list[str] = field(default_factory=list)
    modo: Modo = Modo.OCR_COMPLETO

    @property
    def cobertura(self) -> float:
        return self.paginas_con_texto / self.paginas if self.paginas else 0.0

    @property
    def ya_es_accesible(self) -> bool:
        # Conservador a propósito: solo si el texto cubre casi todas las páginas
        # con densidad suficiente Y el documento está etiquetado.
        return self.modo == Modo.SIN_OCR and self.tiene_tags

    def resumen(self) -> str:
        if self.error:
            return f'ERROR: {self.error}'
        if self.encriptado:
            return 'PDF protegido con contraseña; no se puede procesar'
        base = {
            Modo.OCR_COMPLETO: 'Sin capa de texto (imagen/escaneado): requiere OCR completo',
            Modo.OCR_PARCIAL: (
                f'Documento mixto: {self.paginas_con_texto}/{self.paginas} páginas con '
                f'texto, {self.paginas_solo_imagen} solo imagen: OCR de las escaneadas'
            ),
            Modo.REHACER_OCR: (
                f'Capa de texto de mala calidad (legible {self.ratio_legible:.0%}, '
                f'basura {self.ratio_basura:.0%}): se rehará el OCR'
            ),
            Modo.SIN_OCR: (
                f'Texto correcto en las {self.paginas} páginas '
                f'({self.chars_por_pagina:.0f} chars/página)'
            ),
        }[self.modo]
        tags = 'con tags' if self.tiene_tags else 'sin tags'
        muestra = ' [muestreado]' if self.muestreado else ''
        return f'{base} | {tags}{muestra}'


def metricas_ocr(texto: str) -> tuple[float, float]:
    """Devuelve (ratio_legible, ratio_basura) sobre una muestra del texto.

    Detecta mojibake / OCR defectuoso (carácter de reemplazo, controles, área de
    uso privado Unicode). Complementa a la densidad: la densidad ve "cuánto texto",
    esto ve "qué tan legible es ese texto".
    """
    if not texto:
        return 0.0, 1.0
    muestra = texto[:OCR_SAMPLE_CHARS]
    legibles = 0
    basura = 0
    for c in muestra:
        if c == '�' or (ord(c) < 32 and c not in '\n\t\r') or (0xE000 <= ord(c) <= 0xF8FF):
            basura += 1
        elif c.isalnum() or c in _PUNCT:
            legibles += 1
    n = len(muestra)
    return legibles / n, basura / n


def tiene_tags_accesibilidad(reader: PdfReader) -> bool:
    """True si el PDF declara estructura etiquetada (/MarkInfo + /StructTreeRoot)."""
    try:
        catalogo = reader.trailer.get('/Root', {})
        mark_info = catalogo.get('/MarkInfo', None)
        struct_tree = catalogo.get('/StructTreeRoot', None)
        marcado = bool(mark_info.get('/Marked', False)) if mark_info else False
        return marcado and struct_tree is not None
    except Exception:
        return False


def _indices_muestra(total: int) -> tuple[list[int], bool]:
    """Índices de página a analizar; muestrea uniformemente si el doc es largo."""
    if total > MAX_PAGINAS_ANALISIS:
        paso = total / MAX_PAGINAS_ANALISIS
        return sorted({int(i * paso) for i in range(MAX_PAGINAS_ANALISIS)}), True
    return list(range(total)), False


def _pagina_tiene_recursos(page) -> tuple[bool, bool]:
    """(tiene_fuentes, tiene_imagenes) para una página, tolerante a errores."""
    fuentes = imagenes = False
    try:
        recursos = page.get('/Resources')
        if recursos is not None:
            if recursos.get('/Font'):
                fuentes = True
            xobj = recursos.get('/XObject')
            if xobj:
                try:
                    xobj = xobj.get_object()
                    for k in xobj:
                        if xobj[k].get_object().get('/Subtype') == '/Image':
                            imagenes = True
                            break
                except Exception:
                    pass
    except Exception:
        pass
    return fuentes, imagenes


def _score_ocr(paginas: int, pag_con_texto: int, chars_total: int, fuentes: bool) -> tuple[int, list[str]]:
    """Score 0-100 de legibilidad por lector de pantalla (idéntico al validador)."""
    if paginas <= 0:
        return 0, ['Sin páginas legibles']
    ratio = pag_con_texto / paginas
    cpp = chars_total / paginas
    s = 40 * ratio
    razones = [f'{int(ratio * 100)}% páginas con texto']
    if cpp >= 800:
        s += 35
    elif cpp >= 300:
        s += 28
    elif cpp >= 100:
        s += 20
    elif cpp >= 30:
        s += 10
    razones.append(f'densidad {int(cpp)} chars/pág')
    if fuentes:
        s += 15
        razones.append('fuentes embebidas')
    else:
        razones.append('sin fuentes embebidas')
    if chars_total >= 1000:
        s += 10
    elif chars_total >= 200:
        s += 5
    razones.append(f'{chars_total} chars totales')
    return int(round(min(100, s))), razones


def analizar(ruta: str | Path) -> Diagnostico:
    ruta = Path(ruta)
    diag = Diagnostico(ruta=str(ruta))
    datos = ruta.read_bytes()

    if b'%PDF' not in datos[:1024]:
        diag.error = 'El archivo no es un PDF válido'
        return diag

    try:
        reader = PdfReader(io.BytesIO(datos), strict=False)
        if reader.is_encrypted:
            try:
                if reader.decrypt('') == 0:  # ninguna contraseña vacía funcionó
                    diag.encriptado = True
                    return diag
            except Exception:
                diag.encriptado = True
                return diag
        diag.tiene_tags = tiene_tags_accesibilidad(reader)
        paginas = reader.pages
        diag.paginas = len(paginas)
    except Exception as e:
        diag.error = f'No se pudo abrir el PDF: {str(e)[:120]}'
        return diag

    if diag.paginas == 0:
        diag.error = 'El PDF no tiene páginas'
        return diag

    indices, diag.muestreado = _indices_muestra(diag.paginas)
    diag.paginas_analizadas = len(indices)

    chars_muestra = 0
    pag_con_texto = 0
    fuentes = imagenes = False
    trozos_texto: list[str] = []

    for i in indices:
        page = paginas[i]
        f, im = _pagina_tiene_recursos(page)
        fuentes = fuentes or f
        imagenes = imagenes or im
        try:
            txt = page.extract_text() or ''
        except Exception:
            txt = ''
        n = len(txt.strip())
        chars_muestra += n
        if n >= PAGE_TEXT_MIN_CHARS:
            pag_con_texto += 1
        if txt and len('\n'.join(trozos_texto)) < OCR_SAMPLE_CHARS:
            trozos_texto.append(txt)

    # Respaldo con pdfplumber si pypdf casi no extrajo texto pero hay fuentes
    # (pypdf falla en algunos PDFs con fuentes embebidas que pdfplumber sí lee).
    if chars_muestra < 20 and fuentes:
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(datos)) as pdf:
                pl_chars = 0
                pl_pags = 0
                for i in indices[:min(len(indices), 30)]:
                    try:
                        t = pdf.pages[i].extract_text() or ''
                    except Exception:
                        t = ''
                    c = len(t.strip())
                    pl_chars += c
                    if c >= PAGE_TEXT_MIN_CHARS:
                        pl_pags += 1
                    if t and len('\n'.join(trozos_texto)) < OCR_SAMPLE_CHARS:
                        trozos_texto.append(t)
                if pl_chars > chars_muestra:
                    chars_muestra = pl_chars
                    pag_con_texto = max(pag_con_texto, pl_pags)
        except Exception:
            pass

    diag.tiene_fuentes = fuentes
    diag.tiene_imagenes = imagenes

    # Extrapola al total si se muestreó.
    factor = diag.paginas / max(1, diag.paginas_analizadas)
    if diag.muestreado:
        diag.paginas_con_texto = round(pag_con_texto * factor)
        diag.caracteres = round(chars_muestra * factor)
    else:
        diag.paginas_con_texto = pag_con_texto
        diag.caracteres = chars_muestra
    diag.paginas_solo_imagen = max(0, diag.paginas - diag.paginas_con_texto)
    diag.chars_por_pagina = diag.caracteres / max(1, diag.paginas)

    diag.ratio_legible, diag.ratio_basura = metricas_ocr('\n'.join(trozos_texto))

    diag.score_ocr, diag.razones = _score_ocr(
        diag.paginas, diag.paginas_con_texto, diag.caracteres, fuentes)
    # Criterio validado de "legible por lector de pantalla".
    diag.tiene_ocr = (
        (diag.cobertura >= 0.5 and diag.chars_por_pagina >= DENSIDAD_MIN_CHARS)
        or diag.score_ocr >= SCORE_OCR_MINIMO
    )

    diag.modo = _elegir_modo(diag)
    return diag


def _elegir_modo(diag: Diagnostico) -> Modo:
    # 1. Prácticamente sin texto en todo el documento -> OCR completo.
    if diag.caracteres < MIN_OCR_CHARS or diag.cobertura < 0.05:
        return Modo.OCR_COMPLETO
    # 2. Hay texto, pero está corrupto (mojibake) -> rehacer el OCR.
    if diag.ratio_basura >= OCR_GARBAGE_RATIO or diag.ratio_legible < MIN_OCR_QUALITY:
        return Modo.REHACER_OCR
    # 3. Texto de calidad, pero no cubre casi todas las páginas o densidad baja
    #    -> OCR solo de las páginas escaneadas (conserva las que ya tienen texto).
    if (diag.cobertura < COBERTURA_TEXTO_ALTA
            or diag.chars_por_pagina < DENSIDAD_MIN_CHARS
            or not diag.tiene_ocr):
        return Modo.OCR_PARCIAL
    # 4. Texto bueno en (casi) todas las páginas -> no requiere OCR.
    return Modo.SIN_OCR
