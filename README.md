# OCRFlow

Aplicación de escritorio para Windows que convierte PDFs escaneados o ilegibles en **documentos accesibles para lectores de pantalla** (Narrador de Windows, NVDA, JAWS) mediante una capa invisible de texto OCR y metadatos de accesibilidad.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-Qt6-41CD52?logo=qt&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Características

- Cola de PDFs con arrastrar y soltar — procesamiento en lote
- Diagnóstico automático: detecta PDFs escaneados, con OCR corrupto o ya accesibles
- Capa de texto OCR invisible vía Tesseract 5
- **31 idiomas de OCR disponibles**: español, inglés, francés, portugués, alemán, árabe, chino, japonés, coreano, hindi y más
- **Auto-instalación de idiomas faltantes**: si el idioma seleccionado no está instalado en Tesseract, la app lo descarga e instala automáticamente antes de convertir (solicita permisos de administrador si es necesario)
- Salida PDF/A para archivado a largo plazo
- Etiquetado de idioma y metadatos del documento (`/Lang`, título, `DisplayDocTitle`)
- Seguimiento de progreso por página con conversiones cancelables
- Interfaz completamente navegable por teclado y compatible con lectores de pantalla
- Sin ventanas CMD visibles durante la conversión

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| GUI | PySide6 (Qt 6) |
| Motor OCR | OCRmyPDF + Tesseract 5 |
| Manipulación PDF | pikepdf · pypdf · pdfplumber |
| Lenguaje | Python 3.11+ |

---

## Requisitos previos

Instala estas dependencias **antes** de ejecutar `instalador.bat`. Los instaladores están incluidos en la carpeta `installer/`.

| Requisito | Instalador incluido | Notas |
|---|---|---|
| Python 3.11+ | [python.org](https://www.python.org/downloads/) | Marca **"Add Python to PATH"** durante la instalación |
| Tesseract OCR 5.x | `installer\tesseract-ocr-w64-setup-*.exe` | Activa el idioma **Spanish** · marca **"Add to PATH"** |
| Ghostscript 10.x | `installer\gs10071w64.exe` | Instalar con las opciones por defecto |

> Tras instalar Tesseract y Ghostscript, **reinicia cualquier ventana de comandos abierta** para que el PATH se actualice.

---

## Instalación

```bash
git clone https://github.com/Hendry-Peguero/OCRFlow.git
cd OCRFlow
```

**Paso 1 — Instalar dependencias del sistema (una sola vez):**

1. Ejecutar `installer\tesseract-ocr-w64-setup-*.exe`
   - En la pantalla de componentes, expandir **"Additional language data"** y marcar **Spanish**
   - Marcar **"Add to PATH"**
2. Ejecutar `installer\gs10071w64.exe` — aceptar las opciones por defecto

**Paso 2 — Instalar dependencias Python:**

Doble clic en **`instalador.bat`**. Se encargará de:
- Crear un entorno virtual Python (`.venv/`)
- Instalar todos los paquetes de `requirements.txt`
- Confirmar que Tesseract y Ghostscript están detectados en PATH

---

## Ejecutar la aplicación

Doble clic en **`PDF Accesible.bat`** — abre la GUI sin ventana de consola.

Alternativamente, doble clic en **`OCRFlow.vbs`** o **`ejecutame.bat`**.

> Si falta el entorno virtual, el lanzador pedirá ejecutar `instalador.bat` primero.

---

## Uso

### Interfaz gráfica

1. Arrastrar PDFs a la ventana o usar **+ Agregar PDFs** (`Ctrl+O`)
2. Seleccionar idioma OCR en el combo — si el idioma no está instalado, la app lo descargará automáticamente
3. Elegir carpeta de salida (por defecto: junto al archivo original)
4. Clic en **Convertir F5**

### CLI

```bash
# Convertir un archivo
.venv\Scripts\python cli.py documento.pdf

# Convertir una carpeta completa
.venv\Scripts\python cli.py carpeta\ -o salida\

# Solo analizar, sin convertir
.venv\Scripts\python cli.py documento.pdf --diagnostico

# Forzar OCR aunque el PDF ya tenga texto
.venv\Scripts\python cli.py documento.pdf --forzar

# Especificar idioma OCR
.venv\Scripts\python cli.py documento.pdf --idioma fra+eng

# Sin formato PDF/A
.venv\Scripts\python cli.py documento.pdf --sin-pdfa
```

---

## Cómo funciona

1. **Análisis** (`core/analyzer.py`) — clasifica el PDF: sin texto (escaneado), texto basura (OCR corrupto), mixto o ya accesible. La detección se basa en densidad de caracteres por página, no simplemente en si "la página tiene algo de texto".

2. **Verificación de idiomas** (`core/tesseract_langs.py`) — antes de convertir, comprueba si los idiomas seleccionados están instalados en Tesseract. Si faltan, los descarga del repositorio oficial (`.traineddata`) e instala automáticamente. Si el directorio de Tesseract requiere permisos de administrador, solicita elevación UAC.

3. **Conversión** (`core/converter.py`) — ejecuta `ocrmypdf --force-ocr --deskew --output-type pdfa`. Los PDFs con texto nativo bueno se procesan solo con corrección de metadatos — volver a hacer OCR en texto limpio degradaría la calidad. Usar **Forzar OCR** para anular esto.

4. **Metadatos** — establece `/Lang`, título del documento y `DisplayDocTitle` — lo que el lector de pantalla anuncia al abrir el documento.

5. **Validación** (`core/validator.py`) — mide el resultado con los mismos criterios de densidad de caracteres que el paso 1 y reporta una comparación antes/después.

> El archivo original **nunca se modifica**.

---

## Estructura del proyecto

```
OCRFlow/
├── gui/
│   └── app.py                    # GUI PySide6 — ventana principal, workers QThread
├── core/
│   ├── analyzer.py               # Diagnóstico y clasificación del PDF
│   ├── converter.py              # Pipeline de conversión OCR + PDF/A
│   ├── validator.py              # Medición de calidad del resultado
│   ├── tesseract_langs.py        # Gestión de idiomas Tesseract: detección,
│   │                             #   descarga e instalación automática
│   ├── progreso.py               # Plugin de progreso para OCRmyPDF
│   └── config.py                 # Constantes compartidas
├── installer/
│   ├── tesseract-ocr-w64-setup-*.exe   # Instalador Tesseract 5 (Windows 64-bit)
│   └── gs10071w64.exe            # Instalador Ghostscript 10.07.1 (Windows 64-bit)
├── tests/
│   ├── crear_pdf_prueba.py       # Genera un PDF de prueba escaneado
│   ├── probar_diagnostico.py     # Prueba el analizador
│   └── probar_progreso.py        # Prueba el reporte de progreso
├── cli.py                        # Interfaz de línea de comandos
├── PDF Accesible.bat             # Lanzador principal (sin consola)
├── OCRFlow.vbs                   # Lanzador alternativo (sin consola)
├── ejecutame.bat                 # Lanzador con verificación de dependencias
├── instalador.bat                # Instalador de dependencias Python
└── debug_launch.bat              # Lanzador de diagnóstico — mantiene consola abierta
```

---

## Resolución de problemas

Si la aplicación no abre, ejecutar **`debug_launch.bat`** — mantiene la consola abierta y escribe errores en `crash_log.txt`.

| Síntoma | Solución |
|---|---|
| `Tesseract not found` | Instalar desde `installer\tesseract-ocr-w64-setup-*.exe`, reiniciar cmd |
| `Ghostscript not found` | Instalar desde `installer\gs10071w64.exe`, reiniciar cmd |
| `ModuleNotFoundError: PySide6` | Eliminar `.venv\` y volver a ejecutar `instalador.bat` |
| Idioma OCR no instalado | La app lo descarga automáticamente al convertir. Si falla, ejecutar como administrador |
| `Fallo del OCR` en el log | Verificar que Tesseract y Ghostscript estén en PATH; ejecutar `debug_launch.bat` |
| Ventana no aparece | Revisar la barra de tareas — puede estar minimizada o detrás de otras ventanas |

---

## Prueba rápida

```bash
# Generar un PDF falso escaneado sin capa de texto
.venv\Scripts\python tests\crear_pdf_prueba.py

# Convertirlo
.venv\Scripts\python cli.py tests\prueba_escaneada.pdf -o tests\salida
```

---

## Licencia

MIT — ver [LICENSE](LICENSE)

---

*Desarrollado por [Hendry Peguero](https://github.com/Hendry-Peguero)*
