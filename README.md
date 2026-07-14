# OCRFlow

Windows desktop application that converts scanned or unreadable PDFs into **screen-reader accessible documents** (Windows Narrator, NVDA, JAWS) using an invisible OCR text layer and accessibility metadata.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-Qt6-41CD52?logo=qt&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Features

- Drag-and-drop PDF queue with batch processing
- Automatic diagnosis — detects scanned, defective, or already-accessible PDFs
- Invisible OCR text layer via Tesseract 5
- PDF/A output for long-term archiving
- Document language and metadata tagging (`/Lang`, title, `DisplayDocTitle`)
- Per-page progress tracking with cancelable conversions
- Full keyboard navigation and screen-reader compatible UI

---

## Tech Stack

| Layer | Technology |
|---|---|
| GUI | PySide6 (Qt 6) |
| OCR Engine | OCRmyPDF + Tesseract 5 |
| PDF Manipulation | pikepdf · pypdf · pdfplumber |
| Language | Python 3.11+ |

---

## Prerequisites

Install these **before** running `instalador.bat`. Bundled installers are included in the `installer/` folder.

| Requirement | Bundled Installer | Notes |
|---|---|---|
| Python 3.11+ | [python.org](https://www.python.org/downloads/) | Check **"Add Python to PATH"** during setup |
| Tesseract OCR 5.x | `installer\tesseract-ocr-w64-setup-*.exe` | Enable **Spanish** language pack · check **"Add to PATH"** |
| Ghostscript 10.x | `installer\gs10071w64.exe` | Install with default options |

> After installing Tesseract and Ghostscript, **restart any open command windows** so the PATH is refreshed.

---

## Installation

```bash
git clone https://github.com/Hendry-Peguero/OCRFlow.git
cd OCRFlow
```

**Step 1 — Install system dependencies (once):**

1. Run `installer\tesseract-ocr-w64-setup-*.exe`
   - On the components screen, expand **"Additional language data"** and check **Spanish**
   - Check **"Add to PATH"**
2. Run `installer\gs10071w64.exe` — accept defaults

**Step 2 — Install Python dependencies:**

Double-click **`instalador.bat`**. It will:
- Create a Python virtual environment (`.venv/`)
- Install all packages from `requirements.txt`
- Confirm that Tesseract and Ghostscript are detected in PATH

---

## Running the App

Double-click **`OCRFlow.vbs`** — opens the GUI with no console window.

Alternatively, double-click **`ejecutame.bat`** — same result, also checks dependencies before launching.

> If the virtual environment is missing, the launcher will prompt you to run `instalador.bat` first.

---

## Troubleshooting

If the app does not open, run **`debug_launch.bat`** — it keeps the console open and writes errors to `crash_log.txt`.

Common issues:

| Symptom | Fix |
|---|---|
| `Tesseract not found` | Install from `installer\tesseract-ocr-w64-setup-*.exe`, restart cmd |
| `Ghostscript not found` | Install from `installer\gs10071w64.exe`, restart cmd |
| `ModuleNotFoundError: PySide6` | Delete `.venv\` and re-run `instalador.bat` |
| App launches but window doesn't appear | Check taskbar — it may be minimized or behind other windows |

---

## CLI Usage

```bash
# Convert a single file
.venv\Scripts\python cli.py document.pdf

# Batch convert a folder
.venv\Scripts\python cli.py folder\ -o output\

# Analyze only — no conversion
.venv\Scripts\python cli.py document.pdf --diagnostico

# Force OCR even if the PDF already has text
.venv\Scripts\python cli.py document.pdf --forzar

# Set output format and document title
.venv\Scripts\python cli.py document.pdf --pdfa --titulo "Annual Report 2025"

# Disable PDF/A output
.venv\Scripts\python cli.py document.pdf --sin-pdfa
```

---

## How It Works

1. **Analysis** (`core/analyzer.py`) — classifies the PDF: no text (scanned), garbage text (corrupted OCR), mixed, or already accessible. Detection is based on character density per page, not just whether "the page has some text."

2. **Conversion** (`core/converter.py`) — runs `ocrmypdf --force-ocr --deskew --output-type pdfa`. PDFs with good native text are passed through with metadata only — re-running OCR on clean text would degrade quality. Use **Force OCR** to override.

3. **Metadata** — sets `/Lang`, document title and `DisplayDocTitle` — what the screen reader announces when opening the document.

4. **Validation** (`core/validator.py`) — measures the output using the same character-density criteria as step 1 and reports a before/after comparison.

> The original file is **never modified**.

---

## Project Structure

```
OCRFlow/
├── gui/
│   └── app.py                    # PySide6 GUI — main window, QThread workers
├── core/
│   ├── analyzer.py               # PDF diagnosis and classification
│   ├── converter.py              # OCR + PDF/A conversion pipeline
│   ├── validator.py              # Output quality measurement
│   ├── progreso.py               # Progress reporting utilities
│   └── config.py                 # Shared constants
├── installer/
│   ├── tesseract-ocr-w64-setup-*.exe   # Tesseract 5 installer (Windows 64-bit)
│   └── gs10071w64.exe            # Ghostscript 10.07.1 installer (Windows 64-bit)
├── tests/
│   ├── crear_pdf_prueba.py       # Generates a test scanned PDF
│   ├── probar_diagnostico.py     # Tests the analyzer
│   └── probar_progreso.py        # Tests progress reporting
├── cli.py                        # Command-line interface
├── OCRFlow.vbs                   # Recommended one-click launcher (no console)
├── ejecutame.bat                 # Alternative launcher with dependency checks
├── instalador.bat                # One-click Python dependency installer
└── debug_launch.bat              # Diagnostic launcher — keeps console open
```

---

## Quick Test

```bash
# Generate a fake scanned PDF with no text layer
.venv\Scripts\python tests\crear_pdf_prueba.py

# Convert it
.venv\Scripts\python cli.py tests\prueba_escaneada.pdf -o tests\salida
```

---

## License

MIT — see [LICENSE](LICENSE)

---

*Built by [Hendry Peguero](https://github.com/Hendry-Peguero)*
