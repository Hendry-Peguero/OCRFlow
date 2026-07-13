"""CLI del conversor PDF -> PDF accesible (Etapa 0: prototipo del motor).

Uso:
    python cli.py documento.pdf
    python cli.py doc1.pdf doc2.pdf carpeta_con_pdfs -o salida/
    python cli.py documento.pdf --diagnostico          # solo analiza, no convierte
    python cli.py documento.pdf --pdfa --titulo "Memoria anual 2025"
"""

import argparse
import sys
import time
from pathlib import Path

# La consola de Windows suele usar cp1252; evita que los acentos salgan rotos.
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from core.analyzer import analizar
from core.config import IDIOMA_DOCUMENTO, IDIOMA_OCR, SUFIJO_SALIDA
from core.converter import ErrorConversion, convertir
from core.validator import validar


def recolectar_pdfs(rutas: list[str]) -> list[Path]:
    pdfs: list[Path] = []
    for r in rutas:
        p = Path(r)
        if p.is_dir():
            pdfs.extend(sorted(p.glob('*.pdf')))
        elif p.suffix.lower() == '.pdf' and p.exists():
            pdfs.append(p)
        else:
            print(f'AVISO: se ignora "{r}" (no existe o no es PDF)', file=sys.stderr)
    return pdfs


def ruta_salida(entrada: Path, outdir: str | None) -> Path:
    nombre = entrada.stem + SUFIJO_SALIDA + '.pdf'
    return (Path(outdir) if outdir else entrada.parent) / nombre


def marca(ok: bool) -> str:
    return 'OK' if ok else 'FALTA'


def procesar(entrada: Path, args) -> bool:
    print(f'\n=== {entrada} ===')
    diag = analizar(entrada)
    print(f'Diagnóstico: {diag.resumen()}')

    if args.diagnostico:
        return True
    if diag.error or diag.encriptado:
        return False
    if diag.ya_es_accesible and not args.forzar:
        print('Ya es accesible (texto en todas las páginas + tags). '
              'Usa --forzar para rehacer el OCR de todos modos.')
        return True

    salida = ruta_salida(entrada, args.salida)
    print(f'Convirtiendo -> {salida}')
    t0 = time.monotonic()
    try:
        convertir(
            entrada, salida, diag,
            idioma_ocr=args.lang,
            idioma_documento=args.lang_doc,
            titulo=args.titulo,
            pdfa=args.pdfa,
            forzar=args.forzar,
        )
    except ErrorConversion as e:
        print(f'ERROR: {e}', file=sys.stderr)
        return False

    res = validar(salida)
    print(f'Terminado en {time.monotonic() - t0:.1f} s')
    print(f'  Antes : {diag.caracteres} caracteres, legible {diag.ratio_legible:.0%}, '
          f'tags: {marca(diag.tiene_tags)}')
    print(f'  Ahora : {res.caracteres} caracteres, legible {res.ratio_legible:.0%}, '
          f'tags: {marca(res.tiene_tags)} (fase 2), idioma: {res.idioma or "FALTA"}, '
          f'título: {res.titulo or "FALTA"}')
    if not res.legible_por_lector:
        print('  ADVERTENCIA: la calidad del texto sigue baja; revisar el escaneo original.',
              file=sys.stderr)
    return res.legible_por_lector


def main() -> int:
    ap = argparse.ArgumentParser(
        description='Convierte PDFs escaneados o defectuosos en PDFs legibles por lectores de pantalla.')
    ap.add_argument('entradas', nargs='+', help='PDF(s) o carpeta(s) con PDFs')
    ap.add_argument('-o', '--salida', help='carpeta de salida (por defecto, junto al original)')
    ap.add_argument('--lang', default=IDIOMA_OCR, help=f'idiomas de OCR (defecto: {IDIOMA_OCR})')
    ap.add_argument('--lang-doc', default=IDIOMA_DOCUMENTO,
                    help=f'idioma /Lang del documento (defecto: {IDIOMA_DOCUMENTO})')
    ap.add_argument('--titulo', help='título del documento (metadatos)')
    ap.add_argument('--pdfa', dest='pdfa', action='store_true', default=True,
                    help='generar salida en formato PDF/A (por defecto)')
    ap.add_argument('--sin-pdfa', dest='pdfa', action='store_false',
                    help='generar PDF normal en vez de PDF/A')
    ap.add_argument('--forzar', action='store_true',
                    help='rehacer el OCR aunque el diagnóstico diga que ya es legible')
    ap.add_argument('--diagnostico', action='store_true', help='solo analizar, sin convertir')
    args = ap.parse_args()

    pdfs = recolectar_pdfs(args.entradas)
    if not pdfs:
        print('No se encontró ningún PDF que procesar.', file=sys.stderr)
        return 2

    fallos = sum(0 if procesar(p, args) else 1 for p in pdfs)
    print(f'\n{len(pdfs) - fallos}/{len(pdfs)} procesados correctamente.')
    return 1 if fallos else 0


if __name__ == '__main__':
    sys.exit(main())
