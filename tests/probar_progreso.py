"""Prueba manual del callback de progreso y de la conversión completa.

Convierte tests/prueba_escaneada.pdf reportando cada avance del OCR y
verifica que el resultado sea legible. No requiere GUI.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from core.analyzer import analizar
from core.converter import convertir
from core.validator import validar

AQUI = Path(__file__).parent


def main() -> int:
    entrada = AQUI / 'prueba_escaneada.pdf'
    if not entrada.exists():
        import crear_pdf_prueba
        crear_pdf_prueba.main()

    salida = AQUI / 'salida' / 'prueba_progreso.pdf'
    eventos: list[tuple[str, float | None]] = []

    def al_progresar(desc: str, fraccion: float | None):
        eventos.append((desc, fraccion))
        pct = f'{fraccion:.0%}' if fraccion is not None else '…'
        print(f'  progreso: {desc or "(sin etapa)"} {pct}')

    diag = analizar(entrada)
    print(f'Diagnóstico: {diag.resumen()}')
    convertir(entrada, salida, diag, progreso=al_progresar)

    res = validar(salida)
    print(f'Resultado: {res.caracteres} caracteres, legible {res.ratio_legible:.0%}')

    assert eventos, 'El callback de progreso nunca fue llamado'
    assert res.legible_por_lector, 'La salida no es legible'
    print(f'OK: {len(eventos)} eventos de progreso recibidos.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
