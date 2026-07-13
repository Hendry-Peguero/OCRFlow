"""Validación del resultado: mide el PDF de salida con los mismos criterios
que el auditor NORTIC (texto extraíble, calidad de OCR, tags, /Lang, título)."""

import io
from dataclasses import dataclass
from pathlib import Path

import pdfplumber
from pypdf import PdfReader

from core.analyzer import metricas_ocr, tiene_tags_accesibilidad
from core.config import MAX_PAGINAS_ANALISIS, MIN_OCR_CHARS, MIN_OCR_QUALITY


@dataclass
class Resultado:
    caracteres: int = 0
    ratio_legible: float = 0.0
    ratio_basura: float = 0.0
    tiene_tags: bool = False
    idioma: str | None = None
    titulo: str | None = None

    @property
    def legible_por_lector(self) -> bool:
        """El mínimo indispensable: hay texto y es de calidad razonable."""
        return self.caracteres >= MIN_OCR_CHARS and self.ratio_legible >= MIN_OCR_QUALITY


def validar(ruta: str | Path) -> Resultado:
    datos = Path(ruta).read_bytes()
    res = Resultado()

    reader = PdfReader(io.BytesIO(datos))
    res.tiene_tags = tiene_tags_accesibilidad(reader)
    catalogo = reader.trailer.get('/Root', {})
    lang = catalogo.get('/Lang')
    res.idioma = str(lang) if lang else None
    if reader.metadata and reader.metadata.title:
        res.titulo = str(reader.metadata.title)

    with pdfplumber.open(io.BytesIO(datos)) as pdf:
        texto = '\n'.join(
            (p.extract_text() or '') for p in pdf.pages[:MAX_PAGINAS_ANALISIS]
        )
    res.caracteres = len(texto.strip())
    res.ratio_legible, res.ratio_basura = metricas_ocr(texto)
    return res
