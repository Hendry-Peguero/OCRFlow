"""Verifica la clasificación de modo del analyzer, en especial el bug que hacía
marcar escaneos como 'ya accesibles'.

No descarga ni hace OCR: construye diagnósticos sintéticos y comprueba el modo.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from core.analyzer import Diagnostico, Modo, _elegir_modo


def diag(paginas, pag_con_texto, caracteres, ratio_legible=1.0, ratio_basura=0.0,
         tiene_tags=False):
    d = Diagnostico(ruta='x.pdf')
    d.paginas = paginas
    d.paginas_analizadas = paginas
    d.paginas_con_texto = pag_con_texto
    d.paginas_solo_imagen = max(0, paginas - pag_con_texto)
    d.caracteres = caracteres
    d.chars_por_pagina = caracteres / max(1, paginas)
    d.ratio_legible = ratio_legible
    d.ratio_basura = ratio_basura
    d.tiene_tags = tiene_tags
    # tiene_ocr con el criterio validado
    d.tiene_ocr = (d.cobertura >= 0.5 and d.chars_por_pagina >= 50) or False
    d.modo = _elegir_modo(d)
    return d


CASOS = [
    # (descripción, diag, modo esperado, ya_accesible esperado)
    ('Escaneo puro sin texto',
     diag(paginas=10, pag_con_texto=0, caracteres=0),
     Modo.OCR_COMPLETO, False),

    ('Escaneo con números de página (texto disperso) — EL BUG',
     diag(paginas=100, pag_con_texto=100, caracteres=100 * 25),  # 25 chars/pág
     Modo.OCR_PARCIAL, False),

    ('Documento mixto: 60 con texto, 40 escaneadas',
     diag(paginas=100, pag_con_texto=60, caracteres=60 * 800),
     Modo.OCR_PARCIAL, False),

    ('Texto corrupto (mojibake)',
     diag(paginas=10, pag_con_texto=10, caracteres=10 * 500,
          ratio_legible=0.30, ratio_basura=0.35),
     Modo.REHACER_OCR, False),

    ('Documento nativo con texto bueno, sin tags',
     diag(paginas=10, pag_con_texto=10, caracteres=10 * 500, tiene_tags=False),
     Modo.SIN_OCR, False),

    ('Documento nativo con texto bueno Y tags',
     diag(paginas=10, pag_con_texto=10, caracteres=10 * 500, tiene_tags=True),
     Modo.SIN_OCR, True),
]


def main() -> int:
    fallos = 0
    for desc, d, modo_esp, acc_esp in CASOS:
        ok_modo = d.modo == modo_esp
        ok_acc = d.ya_es_accesible == acc_esp
        estado = 'OK ' if (ok_modo and ok_acc) else 'FALLA'
        if not (ok_modo and ok_acc):
            fallos += 1
        print(f'[{estado}] {desc}')
        print(f'        modo={d.modo.value} (esperado {modo_esp.value}), '
              f'ya_accesible={d.ya_es_accesible} (esperado {acc_esp})')
    print()
    if fallos:
        print(f'{fallos} caso(s) fallaron.')
        return 1
    print('Todos los casos pasaron: los escaneos ya NO se marcan como accesibles.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
