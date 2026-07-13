"""Constantes de configuración del conversor.

Los umbrales de calidad de OCR provienen del NORTIC B2 checker (checks/pdfs.py),
de modo que este conversor y aquel auditor midan con la misma vara.
"""

# --- Análisis del PDF de entrada ---
# La metodología de detección de capa de texto está portada de validar_ocr_pdfs.py,
# el validador de OCR verificado sobre ~9199 PDFs. Lo importante es medir la
# DENSIDAD de texto por página, no solo si la página "tiene algo de texto":
# un escaneo con números de página o marcas de agua engaña a esa medida ingenua.
MAX_PAGINAS_ANALISIS = 60    # tope de páginas analizadas; si excede, se muestrea
PAGE_TEXT_MIN_CHARS = 10     # una página "tiene texto" si supera estos caracteres
DENSIDAD_MIN_CHARS = 50      # chars/página promedio mínimo para dar por buena la capa de texto
COBERTURA_TEXTO_ALTA = 0.98  # fracción de páginas con texto para tratar el doc como 100% textual
SCORE_OCR_MINIMO = 55        # score de legibilidad (0-100) a partir del cual "tiene OCR"

MIN_OCR_CHARS = 100          # < esto en todo el doc = prácticamente sin texto (imagen/escaneo)
MIN_OCR_QUALITY = 0.45       # ratio de caracteres legibles bajo el cual se sospecha OCR malo
OCR_GARBAGE_RATIO = 0.20     # proporción de caracteres de reemplazo/control que confirma basura
OCR_SAMPLE_CHARS = 4000      # muestra de texto usada para evaluar la calidad (mojibake)

# --- Conversión ---
IDIOMA_OCR = 'spa+eng'       # idiomas por defecto para Tesseract
IDIOMA_DOCUMENTO = 'es-DO'   # valor de /Lang que anuncian los lectores de pantalla
SUFIJO_SALIDA = '_accesible' # prueba.pdf -> prueba_accesible.pdf
