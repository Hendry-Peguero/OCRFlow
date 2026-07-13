"""Genera un PDF de solo imagen (simula un escaneo) para probar el pipeline.

El PDF resultante no tiene capa de texto: un lector de pantalla no puede leerlo.
Tras pasar por cli.py debe tener texto extraíble en español.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

TEXTO = (
    "REPÚBLICA DOMINICANA",
    "Informe de Prueba de Accesibilidad",
    "",
    "Este documento simula un PDF escaneado sin capa de texto.",
    "Los lectores de pantalla como el Narrador de Windows, NVDA",
    "o JAWS no pueden leer este contenido hasta que se le aplique",
    "reconocimiento óptico de caracteres (OCR).",
    "",
    "El conversor debe producir una copia accesible donde todo",
    "este texto sea seleccionable, buscable y legible en voz alta.",
    "",
    "Fecha del documento: 9 de julio de 2026.",
)


def main() -> None:
    # A4 a 200 dpi
    img = Image.new('RGB', (1654, 2339), 'white')
    draw = ImageDraw.Draw(img)
    fuente = ImageFont.truetype('arial.ttf', 44)

    y = 200
    for linea in TEXTO:
        draw.text((160, y), linea, fill='black', font=fuente)
        y += 80

    destino = Path(__file__).parent / 'prueba_escaneada.pdf'
    img.save(destino, 'PDF', resolution=200)
    print(f'Creado: {destino}')


if __name__ == '__main__':
    main()
