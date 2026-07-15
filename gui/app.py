"""Interfaz gráfica del conversor PDF → PDF accesible.

Ejecutar:  .venv\\Scripts\\python gui\\app.py
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ── Suprimir ventanas CMD en Windows ─────────────────────────────────────────
# ocrmypdf llama a tesseract y ghostscript via subprocess sin CREATE_NO_WINDOW;
# en apps GUI (pythonw.exe) eso abre ventanas CMD visibles. El parche siguiente
# añade CREATE_NO_WINDOW a TODOS los subprocesos del proceso.
if sys.platform == 'win32':
    _CREATE_NO_WINDOW = 0x08000000
    _Popen_orig = subprocess.Popen.__init__

    def _Popen_sin_ventana(self, args, **kwargs):
        kwargs.setdefault('creationflags', _CREATE_NO_WINDOW)
        _Popen_orig(self, args, **kwargs)

    subprocess.Popen.__init__ = _Popen_sin_ventana

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction, QColor, QFont
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFrame,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPlainTextEdit, QProgressBar, QPushButton,
    QSplitter, QStackedWidget, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from core.analyzer import Diagnostico, analizar
from core.config import IDIOMA_DOCUMENTO, SUFIJO_SALIDA
from core.converter import ConversionCancelada, convertir
from core.validator import Resultado, validar

# ─── Columnas ─────────────────────────────────────────────────────────────────
COL_ARCHIVO, COL_PAGINAS, COL_DIAG, COL_ESTADO = 0, 1, 2, 3

IDIOMAS_OCR = [
    # Combinaciones
    ('Español + Inglés',             'spa+eng'),
    ('Español + Inglés + Francés',   'spa+eng+fra'),
    ('Español + Inglés + Portugués', 'spa+eng+por'),
    # Europeos
    ('Solo español',                 'spa'),
    ('Solo inglés',                  'eng'),
    ('Francés',                      'fra'),
    ('Portugués',                    'por'),
    ('Alemán',                       'deu'),
    ('Italiano',                     'ita'),
    ('Neerlandés',                   'nld'),
    ('Polaco',                       'pol'),
    ('Ruso',                         'rus'),
    ('Catalán',                      'cat'),
    ('Checo',                        'ces'),
    ('Sueco',                        'swe'),
    ('Danés',                        'dan'),
    ('Noruego',                      'nor'),
    ('Finés',                        'fin'),
    ('Rumano',                       'ron'),
    ('Húngaro',                      'hun'),
    ('Turco',                        'tur'),
    ('Ucraniano',                    'ukr'),
    # Asiáticos / Otros
    ('Árabe',                        'ara'),
    ('Chino simplificado',           'chi_sim'),
    ('Chino tradicional',            'chi_tra'),
    ('Japonés',                      'jpn'),
    ('Coreano',                      'kor'),
    ('Hindi',                        'hin'),
    ('Vietnamita',                   'vie'),
    ('Indonesio',                    'ind'),
    ('Tailandés',                    'tha'),
    ('Hebreo',                       'heb'),
]

ETAPAS = {
    'Scanning contents':  'Examinando contenido',
    'OCR':                'Reconociendo texto',
    'PDF/A conversion':   'Convirtiendo a PDF/A',
    'Linearizing':        'Optimizando',
    'Recompressing JPEGs':'Comprimiendo imágenes',
    'Deflating JPEGs':    'Comprimiendo imágenes',
    'Optimizing PDF':     'Optimizando',
}

# Paleta estado: texto, fondo celda
ESTADO_COLORES = {
    'ok':      ('#007A40', '#E6FAF1'),
    'error':   ('#B71C1C', '#FFEBEE'),
    'aviso':   ('#C67900', '#FEF5E7'),
    'proceso': ('#065AD6', '#EEF3FD'),
    'neutro':  ('#6B80B3', '#F0F4FB'),
}

# ─── STYLESHEET ───────────────────────────────────────────────────────────────
STYLESHEET = """
QMainWindow { background: #F4F6FA; }

/* ── Barra de menú ── */
QMenuBar {
    background: #FFFFFF;
    color: #111827;
    border-bottom: 1px solid #E2E8F0;
    padding: 2px 0;
    font-size: 12px;
}
QMenuBar::item {
    padding: 4px 12px;
    background: transparent;
    color: #111827;
}
QMenuBar::item:selected { background: #EFF6FF; color: #2563EB; }
QMenuBar::item:pressed  { background: #DBEAFE; color: #2563EB; }
QMenu {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    color: #111827;
    font-size: 12px;
}
QMenu::item { padding: 6px 24px 6px 12px; }
QMenu::item:selected { background: #EFF6FF; color: #2563EB; }
QMenu::separator { height: 1px; background: #E2E8F0; margin: 4px 0; }

/* ── Sidebar ── */
#sidebar {
    background: #0F1B35;
}
#sidebarHeader {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #1C3D8F, stop:1 #0F1B35);
    min-height: 88px;
    max-height: 88px;
}
#brandName {
    color: #FFFFFF;
    font-size: 15px;
    font-weight: bold;
    letter-spacing: 1px;
}
#brandSub {
    color: #93C5FD;
    font-size: 10px;
    letter-spacing: 0.5px;
}
#sidebarDivider {
    background: #1A3060;
    min-height: 1px;
    max-height: 1px;
    border: none;
}
#navItem {
    color: #BFDBFE;
    font-size: 13px;
    padding: 10px 20px;
    background: transparent;
    border: none;
    border-radius: 0;
    text-align: left;
    min-height: 38px;
}
#navItem:hover { background: rgba(37, 99, 235, 0.40); color: #FFFFFF; }
#navItemActive {
    color: #FFFFFF;
    font-size: 13px;
    font-weight: bold;
    padding: 10px 20px 10px 17px;
    background: #1D4ED8;
    border: none;
    border-radius: 0;
    border-left: 3px solid #60A5FA;
    text-align: left;
    min-height: 38px;
}
#sidebarVersion { color: #475569; font-size: 10px; }
#sidebarAuthor  { color: #475569; font-size: 10px; }

/* ── Topbar ── */
#topbar {
    background: #FFFFFF;
    border-bottom: 1px solid #C7D5F0;
    min-height: 56px;
    max-height: 56px;
}
#topbarTitle { color: #0A1F4E; font-size: 15px; font-weight: bold; }
#statusPill {
    background: #E6FAF1;
    border-radius: 9px;
    padding: 2px 10px;
    color: #007A40;
    font-size: 11px;
    font-weight: 600;
    max-height: 22px;
}
#statusPillBusy {
    background: #EEF3FD;
    border-radius: 9px;
    padding: 2px 10px;
    color: #065AD6;
    font-size: 11px;
    font-weight: 600;
    max-height: 22px;
}

/* ── Área de contenido ── */
#contentBody { background: #F4F6FA; }

/* ── Tarjetas ── */
#card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
}
#cardHeader {
    background: #FFFFFF;
    border-bottom: 1px solid #E2E8F0;
    border-radius: 10px 10px 0 0;
    min-height: 44px;
    max-height: 44px;
}
#cardHeaderTitle {
    color: #111827;
    font-size: 13px;
    font-weight: bold;
}
#toolbar {
    background: #F8FAFC;
    border-radius: 10px 10px 0 0;
    border-bottom: 1px solid #E2E8F0;
}

/* ── Zona de arrastre ── */
#dropZone {
    background: #EFF6FF;
    border: 2px dashed #2563EB;
    border-radius: 10px;
    min-height: 120px;
}
#dropTitle { color: #111827; font-size: 14px; font-weight: bold; }
#dropSub   { color: #64748B; font-size: 11px; }

/* ── Botones base ── */
QPushButton {
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 5px 14px;
    background: #FFFFFF;
    color: #374151;
    font-size: 12px;
    min-height: 28px;
}
QPushButton:hover   { background: #EFF6FF; border-color: #2563EB; color: #2563EB; }
QPushButton:pressed { background: #DBEAFE; }
QPushButton:disabled { background: #F9FAFB; color: #9CA3AF; border-color: #F1F5F9; }

/* ── Botón CONVERTIR ── */
#btnConvertir {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #2563EB, stop:1 #1D4ED8);
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: bold;
    padding: 10px 36px;
    min-height: 42px;
}
#btnConvertir:hover   { background: #1D4ED8; }
#btnConvertir:pressed { background: #1E40AF; }
#btnConvertir:disabled { background: #93C5FD; color: #FFFFFF; }

/* ── Botón CANCELAR ── */
#btnCancelar {
    background: #FFFFFF;
    color: #64748B;
    border: 1.5px solid #E2E8F0;
    border-radius: 8px;
    font-size: 13px;
    font-weight: bold;
    padding: 10px 20px;
    min-height: 42px;
}
#btnCancelar:hover    { background: #EFF6FF; border-color: #2563EB; color: #2563EB; }
#btnCancelar:pressed  { background: #DBEAFE; }
#btnCancelar:disabled { color: #E2E8F0; border-color: #F1F5F9; }

/* ── Tabla ── */
QTableWidget {
    gridline-color: transparent;
    border: none;
    font-size: 12px;
    selection-background-color: #EFF6FF;
    selection-color: #2563EB;
    alternate-background-color: #F8FAFC;
    background: #FFFFFF;
}
QTableWidget::item { padding: 7px 10px; }
QHeaderView::section {
    background: #F8FAFC;
    border: none;
    border-bottom: 1px solid #E2E8F0;
    padding: 8px 10px;
    font-weight: bold;
    font-size: 11px;
    color: #64748B;
}

/* ── Barra de progreso ── */
QProgressBar {
    border: none;
    border-radius: 4px;
    background: #DBEAFE;
    max-height: 8px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #2563EB, stop:1 #60A5FA);
    border-radius: 4px;
}

/* ── Panel de detalle ── */
#detalle {
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    font-family: Consolas, "Courier New", monospace;
    font-size: 12px;
    background: #F8FAFC;
    color: #374151;
}

/* ── Barra de estado ── */
QStatusBar {
    background: #FFFFFF;
    border-top: 1px solid #E2E8F0;
    color: #64748B;
    font-size: 11px;
    padding: 2px 8px;
}

/* ── Controles ── */
QComboBox {
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 4px 8px;
    background: #F8FAFC;
    min-width: 160px;
    min-height: 28px;
    font-size: 12px;
    color: #111827;
}
QComboBox:hover { border-color: #2563EB; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    border: 1px solid #E2E8F0;
    background: #FFFFFF;
    selection-background-color: #EFF6FF;
    selection-color: #2563EB;
}

QCheckBox { font-size: 12px; color: #111827; spacing: 6px; }
QCheckBox::indicator {
    width: 15px;
    height: 15px;
    border: 1.5px solid #E2E8F0;
    border-radius: 3px;
    background: #FFFFFF;
}
QCheckBox::indicator:checked { background: #2563EB; border-color: #2563EB; }
QCheckBox::indicator:hover   { border-color: #2563EB; }

QLineEdit {
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 5px 8px;
    background: #F8FAFC;
    font-size: 12px;
    min-height: 28px;
    color: #111827;
}
QLineEdit:focus { border-color: #2563EB; }

QLabel { color: #111827; }

/* ── Diálogos ── */
QMessageBox { background: #FFFFFF; }
QMessageBox QLabel { color: #111827; background: transparent; }
QMessageBox QPushButton {
    min-width: 80px;
    background: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 6px 18px;
    font-weight: 600;
}
QMessageBox QPushButton:hover { background: #1D4ED8; }
"""


# ─── Workers ──────────────────────────────────────────────────────────────────

class Analizador(QThread):
    listo = Signal(int, object)

    def __init__(self, items: list[tuple[int, Path]]):
        super().__init__()
        self.items = items

    def run(self):
        for fila, ruta in self.items:
            try:
                diag = analizar(ruta)
            except Exception as e:
                diag = Diagnostico(ruta=str(ruta), error=str(e)[:120])
            self.listo.emit(fila, diag)


class InstaladorIdiomas(QThread):
    """Descarga e instala paquetes de idioma de Tesseract en segundo plano."""

    progreso  = Signal(str, object)  # (descripcion, fraccion 0-1 | None)
    terminado = Signal(bool, str)    # (exito, mensaje_error)

    def __init__(self, codigos: list[str]):
        super().__init__()
        self.codigos = codigos

    def run(self):
        from core import tesseract_langs as tl
        for codigo in self.codigos:
            try:
                tl.instalar_idioma(
                    codigo,
                    progreso=lambda desc, frac: self.progreso.emit(desc, frac),
                )
            except Exception as e:
                self.terminado.emit(False, str(e))
                return
        self.terminado.emit(True, '')


class Convertidor(QThread):
    archivo_inicia  = Signal(int, int, int)
    progreso_pagina = Signal(int, str, float)
    fila_lista      = Signal(int, str, str, str)
    todo_listo      = Signal(int, int)

    def __init__(self, trabajos, carpeta_salida, idioma_ocr, pdfa, forzar=False):
        super().__init__()
        self.trabajos       = trabajos
        self.carpeta_salida = carpeta_salida
        self.idioma_ocr     = idioma_ocr
        self.pdfa           = pdfa
        self.forzar         = forzar
        self._cancelado     = False

    def cancelar(self):
        self._cancelado = True

    def run(self):
        ok = errores = 0
        try:
            total = len(self.trabajos)
            for i, (fila, ruta, diag) in enumerate(self.trabajos, 1):
                if self._cancelado:
                    self.fila_lista.emit(fila, 'neutro', 'Cancelado (no iniciado)', '')
                    continue
                self.archivo_inicia.emit(i, total, fila)
                carpeta = Path(self.carpeta_salida) if self.carpeta_salida else ruta.parent
                salida  = carpeta / (ruta.stem + SUFIJO_SALIDA + '.pdf')

                def al_progresar(desc, frac, fila=fila):
                    etapa = ETAPAS.get(desc, desc or 'Procesando')
                    self.progreso_pagina.emit(fila, etapa, frac if frac is not None else -1.0)

                try:
                    convertir(
                        ruta, salida, diag,
                        idioma_ocr=self.idioma_ocr,
                        pdfa=self.pdfa,
                        forzar=self.forzar,
                        progreso=al_progresar,
                        cancelar=lambda: self._cancelado,
                    )
                    res     = validar(salida)
                    detalle = _detalle_resultado(diag, res, salida)
                    if res.legible_por_lector:
                        ok += 1
                        self.fila_lista.emit(
                            fila, 'ok',
                            f'Accesible — legible {res.ratio_legible:.0%} → {salida.name}',
                            detalle + f'\n@salida={salida}')
                    else:
                        errores += 1
                        self.fila_lista.emit(
                            fila, 'aviso',
                            f'Calidad baja (legible {res.ratio_legible:.0%})',
                            detalle + '\nADVERTENCIA: revisar el escaneo original.'
                            + f'\n@salida={salida}')
                except ConversionCancelada:
                    self.fila_lista.emit(fila, 'neutro', 'Cancelado por el usuario', '')
                except Exception as e:
                    errores += 1
                    self.fila_lista.emit(fila, 'error', f'ERROR: {str(e)[:150]}', str(e))
        finally:
            self.todo_listo.emit(ok, errores)


def _detalle_resultado(diag: Diagnostico, res: Resultado, salida: Path) -> str:
    return (
        f'Resultado: {salida}\n'
        f'  Antes : {diag.caracteres} caracteres  '
        f'legible {diag.ratio_legible:.0%}  basura {diag.ratio_basura:.0%}\n'
        f'  Ahora : {res.caracteres} caracteres  '
        f'legible {res.ratio_legible:.0%}  basura {res.ratio_basura:.0%}\n'
        f'  Idioma anunciado: {res.idioma or "FALTA"}   '
        f'Título: {res.titulo or "FALTA"}\n'
        f'  Tags de estructura: {"sí" if res.tiene_tags else "pendiente (etapa 3)"}'
    )


# ─── Widgets auxiliares ───────────────────────────────────────────────────────

class DropZona(QWidget):
    """Pantalla inicial: instrucciones de arrastre cuando la cola está vacía."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('dropZone')
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(10)

        icono = QLabel('⬆')
        icono.setAlignment(Qt.AlignCenter)
        icono.setStyleSheet('font-size: 44px; color: #2563EB;')

        titulo = QLabel('Arrastra los PDFs aquí')
        titulo.setObjectName('dropTitle')
        titulo.setAlignment(Qt.AlignCenter)

        sub = QLabel('o usa el botón  + Agregar PDFs  (Ctrl + O)')
        sub.setObjectName('dropSub')
        sub.setAlignment(Qt.AlignCenter)

        formatos = QLabel('Soporta escaneos, documentos mixtos y PDFs nativos')
        formatos.setAlignment(Qt.AlignCenter)
        formatos.setStyleSheet('font-size: 10px; color: #64748B; margin-top: 4px;')

        lay.addWidget(icono)
        lay.addWidget(titulo)
        lay.addWidget(sub)
        lay.addWidget(formatos)


def _sep_v() -> QFrame:
    sep = QFrame()
    sep.setFrameShape(QFrame.VLine)
    sep.setStyleSheet('color: #C7D5F0; max-width: 1px;')
    return sep


# ─── Ventana principal ────────────────────────────────────────────────────────

class Ventana(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('OCRFlow')
        self.resize(1160, 740)
        self.setMinimumSize(860, 560)
        self.setAcceptDrops(True)

        self.trabajos: list[dict]                = []
        self.hilo: Convertidor | None            = None
        self._instalador: InstaladorIdiomas | None = None
        self._analizadores: list[Analizador]     = []

        self._crear_menu()
        self._construir_ui()
        self.barra = self.statusBar()
        self.barra.showMessage(
            'Listo. Arrastra PDFs a la ventana o usa Ctrl+O para agregar archivos.')

    # ── Menú ──────────────────────────────────────────────────────────────────
    def _crear_menu(self):
        m = self.menuBar().addMenu('&Archivo')
        self._accion(m, 'Agregar &PDFs…',    'Ctrl+O',        self.elegir_archivos)
        self._accion(m, 'Agregar &carpeta…', 'Ctrl+Shift+O',  self.elegir_carpeta)
        m.addSeparator()
        self._accion(m, '&Salir',            'Ctrl+Q',        self.close)
        h = self.menuBar().addMenu('&Ayuda')
        self._accion(h, '&Acerca de…', None, self.acerca_de)

    def _accion(self, menu, texto, atajo, slot):
        a = QAction(texto, self)
        if atajo:
            a.setShortcut(atajo)
        a.triggered.connect(slot)
        menu.addAction(a)

    # ── Construcción de la UI ─────────────────────────────────────────────────
    def _construir_ui(self):
        raiz = QWidget()
        self.setCentralWidget(raiz)
        root_lay = QHBoxLayout(raiz)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        # Sidebar izquierdo
        root_lay.addWidget(self._w_sidebar())

        # Columna derecha: topbar + cuerpo
        col = QWidget()
        col.setObjectName('contentBody')
        col_lay = QVBoxLayout(col)
        col_lay.setContentsMargins(0, 0, 0, 0)
        col_lay.setSpacing(0)
        col_lay.addWidget(self._w_topbar())

        cuerpo = QWidget()
        cuerpo_lay = QVBoxLayout(cuerpo)
        cuerpo_lay.setContentsMargins(20, 16, 20, 14)
        cuerpo_lay.setSpacing(14)
        cuerpo_lay.addWidget(self._w_ajustes())
        cuerpo_lay.addWidget(self._w_cola(), stretch=1)
        cuerpo_lay.addWidget(self._w_acciones())
        col_lay.addWidget(cuerpo, stretch=1)

        root_lay.addWidget(col, stretch=1)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _w_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName('sidebar')
        sidebar.setFixedWidth(224)
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Cabecera
        hdr = QFrame()
        hdr.setObjectName('sidebarHeader')
        hdr_lay = QVBoxLayout(hdr)
        hdr_lay.setContentsMargins(20, 22, 20, 18)
        hdr_lay.setSpacing(4)
        brand = QLabel('OCRFlow')
        brand.setObjectName('brandName')
        brand.setAccessibleName('OCRFlow — Conversor de documentos')
        sub = QLabel('Conversor OCR / Accesibilidad')
        sub.setObjectName('brandSub')
        hdr_lay.addWidget(brand)
        hdr_lay.addWidget(sub)
        lay.addWidget(hdr)

        # Separador
        div = QFrame()
        div.setObjectName('sidebarDivider')
        lay.addWidget(div)

        # Ítems de navegación
        nav_items = [
            ('Convertir PDF', True,  self.elegir_archivos),
            ('Acerca de',     False, self.acerca_de),
        ]
        for label, active, slot in nav_items:
            btn = QPushButton(label)
            btn.setObjectName('navItemActive' if active else 'navItem')
            btn.setFlat(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setAccessibleName(label)
            if slot:
                btn.clicked.connect(slot)
            lay.addWidget(btn)

        lay.addStretch()

        # Pie
        foot = QFrame()
        foot_lay = QVBoxLayout(foot)
        foot_lay.setContentsMargins(20, 10, 20, 18)
        foot_lay.setSpacing(2)
        v = QLabel('v1.0.0')
        v.setObjectName('sidebarVersion')
        n = QLabel('Hendry Peguero')
        n.setObjectName('sidebarAuthor')
        foot_lay.addWidget(v)
        foot_lay.addWidget(n)
        lay.addWidget(foot)

        return sidebar

    # ── Topbar ────────────────────────────────────────────────────────────────
    def _w_topbar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName('topbar')
        row = QHBoxLayout(bar)
        row.setContentsMargins(24, 0, 24, 0)
        row.setSpacing(12)

        title = QLabel('OCRFlow — Conversor de PDF Accesible')
        title.setObjectName('topbarTitle')
        row.addWidget(title)
        row.addStretch()

        self._status_pill = QLabel('● Listo')
        self._status_pill.setObjectName('statusPill')
        row.addWidget(self._status_pill)

        return bar

    # ── Ajustes ───────────────────────────────────────────────────────────────
    def _w_ajustes(self) -> QWidget:
        card = QFrame()
        card.setObjectName('card')
        outer = QVBoxLayout(card)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Cabecera de tarjeta
        hdr = QFrame()
        hdr.setObjectName('cardHeader')
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(14, 0, 14, 0)
        lbl_hdr = QLabel('Opciones de conversión')
        lbl_hdr.setObjectName('cardHeaderTitle')
        hdr_lay.addWidget(lbl_hdr)
        outer.addWidget(hdr)

        # Controles
        body = QWidget()
        row = QHBoxLayout(body)
        row.setContentsMargins(14, 10, 14, 10)
        row.setSpacing(16)

        lbl_idioma = QLabel('Idioma OCR:')
        lbl_idioma.setStyleSheet('color: #64748B; font-size: 11px;')
        self.combo_idioma = QComboBox()
        for txt, cod in IDIOMAS_OCR:
            self.combo_idioma.addItem(txt, cod)
        self.combo_idioma.setAccessibleName('Idioma del reconocimiento de texto')
        lbl_idioma.setBuddy(self.combo_idioma)
        row.addWidget(lbl_idioma)
        row.addWidget(self.combo_idioma)

        self.check_pdfa = QCheckBox('PDF/A (archivado)')
        self.check_pdfa.setChecked(True)
        self.check_pdfa.setToolTip('Genera la salida en formato PDF/A, ideal para archivos a largo plazo')
        row.addWidget(self.check_pdfa)

        self.check_forzar = QCheckBox('Forzar OCR')
        self.check_forzar.setToolTip(
            'Rehacer el OCR aunque el PDF ya tenga texto legible.\n'
            'Útil cuando el diagnóstico automático se equivoca.')
        self.check_forzar.toggled.connect(self._recontar)
        row.addWidget(self.check_forzar)

        row.addWidget(_sep_v())

        lbl_sal = QLabel('Guardar en:')
        lbl_sal.setStyleSheet('color: #64748B; font-size: 11px;')
        self.campo_salida = QLineEdit()
        self.campo_salida.setPlaceholderText('Junto al archivo original')
        self.campo_salida.setAccessibleName('Carpeta de salida')
        lbl_sal.setBuddy(self.campo_salida)
        btn_sal = QPushButton('Elegir…')
        btn_sal.clicked.connect(self.elegir_salida)
        row.addWidget(lbl_sal)
        row.addWidget(self.campo_salida, 1)
        row.addWidget(btn_sal)

        outer.addWidget(body)
        return card

    # ── Cola de archivos ──────────────────────────────────────────────────────
    def _w_cola(self) -> QWidget:
        card = QFrame()
        card.setObjectName('card')
        lay = QVBoxLayout(card)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Barra superior de la cola
        toolbar = QFrame()
        toolbar.setObjectName('toolbar')
        trow = QHBoxLayout(toolbar)
        trow.setContentsMargins(14, 8, 14, 8)
        trow.setSpacing(8)

        lbl = QLabel('Cola de archivos')
        lbl.setObjectName('cardHeaderTitle')
        trow.addWidget(lbl)
        trow.addStretch()

        self.btn_agregar = QPushButton('+ Agregar PDFs…')
        self.btn_agregar.setToolTip('Ctrl+O')
        self.btn_agregar.clicked.connect(self.elegir_archivos)
        trow.addWidget(self.btn_agregar)

        self.btn_carpeta = QPushButton('+ Carpeta…')
        self.btn_carpeta.setToolTip('Ctrl+Shift+O')
        self.btn_carpeta.clicked.connect(self.elegir_carpeta)
        trow.addWidget(self.btn_carpeta)

        self.btn_limpiar = QPushButton('Limpiar lista')
        self.btn_limpiar.clicked.connect(self.limpiar)
        trow.addWidget(self.btn_limpiar)
        lay.addWidget(toolbar)

        # Stack: zona vacía / tabla con detalle
        self.stack = QStackedWidget()
        self.stack.addWidget(DropZona())   # índice 0 — vacío

        splitter = QSplitter(Qt.Vertical)

        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(['Archivo', 'Págs', 'Diagnóstico', 'Estado'])
        self.tabla.setAccessibleName('Cola de archivos PDF')
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setShowGrid(False)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        cab = self.tabla.horizontalHeader()
        cab.setSectionResizeMode(COL_ARCHIVO, QHeaderView.ResizeToContents)
        cab.setSectionResizeMode(COL_PAGINAS, QHeaderView.ResizeToContents)
        cab.setSectionResizeMode(COL_DIAG,    QHeaderView.Stretch)
        cab.setSectionResizeMode(COL_ESTADO,  QHeaderView.Stretch)
        self.tabla.itemSelectionChanged.connect(self.mostrar_detalle)
        self.tabla.itemActivated.connect(self.abrir_resultado)
        splitter.addWidget(self.tabla)

        self.detalle = QPlainTextEdit()
        self.detalle.setReadOnly(True)
        self.detalle.setObjectName('detalle')
        self.detalle.setAccessibleName('Detalle del archivo seleccionado')
        self.detalle.setPlaceholderText(
            'Selecciona un archivo para ver su diagnóstico y resultado.\n'
            'Doble clic o Enter sobre un convertido para abrirlo.')
        self.detalle.setMaximumHeight(130)
        splitter.addWidget(self.detalle)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)

        self.stack.addWidget(splitter)     # índice 1 — con archivos
        lay.addWidget(self.stack, 1)
        return card

    # ── Barra de acciones ─────────────────────────────────────────────────────
    def _w_acciones(self) -> QWidget:
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 4, 0, 0)
        h.setSpacing(12)

        # Progreso (etiqueta + barra)
        prog = QVBoxLayout()
        prog.setSpacing(5)
        self.etiqueta_progreso = QLabel('')
        self.etiqueta_progreso.setStyleSheet('color: #64748B; font-size: 11px;')
        self.progreso = QProgressBar()
        self.progreso.setRange(0, 1000)
        self.progreso.setValue(0)
        self.progreso.setTextVisible(False)
        self.progreso.setAccessibleName('Progreso de la conversión actual')
        prog.addWidget(self.etiqueta_progreso)
        prog.addWidget(self.progreso)
        h.addLayout(prog, 1)

        h.addSpacing(16)

        self.btn_cancelar = QPushButton('Cancelar')
        self.btn_cancelar.setObjectName('btnCancelar')
        self.btn_cancelar.setShortcut('Escape')
        self.btn_cancelar.setEnabled(False)
        self.btn_cancelar.setAccessibleName('Cancelar la conversión en curso')
        self.btn_cancelar.clicked.connect(self.cancelar)
        h.addWidget(self.btn_cancelar)

        self.btn_convertir = QPushButton('⚡  Convertir   F5')
        self.btn_convertir.setObjectName('btnConvertir')
        self.btn_convertir.setShortcut('F5')
        self.btn_convertir.setDefault(True)
        self.btn_convertir.setAccessibleName('Convertir todos los PDFs pendientes')
        self.btn_convertir.clicked.connect(self.convertir_todo)
        h.addWidget(self.btn_convertir)
        return row

    # ── Arrastrar y soltar ────────────────────────────────────────────────────
    def dragEnterEvent(self, ev):
        if any(u.toLocalFile().lower().endswith('.pdf') for u in ev.mimeData().urls()):
            ev.acceptProposedAction()

    def dropEvent(self, ev):
        rutas = [u.toLocalFile() for u in ev.mimeData().urls()
                 if u.toLocalFile().lower().endswith('.pdf')]
        self.agregar(rutas)

    # ── Gestión de archivos ───────────────────────────────────────────────────
    def elegir_archivos(self):
        rutas, _ = QFileDialog.getOpenFileNames(
            self, 'Elegir PDFs', '', 'Documentos PDF (*.pdf)')
        self.agregar(rutas)

    def elegir_carpeta(self):
        carpeta = QFileDialog.getExistingDirectory(self, 'Elegir carpeta con PDFs')
        if not carpeta:
            return
        rutas = sorted(str(p) for p in Path(carpeta).glob('*.pdf'))
        if not rutas:
            QMessageBox.information(self, 'OCRFlow',
                                    'Esa carpeta no contiene archivos PDF.')
            return
        self.agregar(rutas)

    def elegir_salida(self):
        carpeta = QFileDialog.getExistingDirectory(self, 'Carpeta de salida')
        if carpeta:
            self.campo_salida.setText(carpeta)

    def agregar(self, rutas: list[str]):
        if self.hilo and self.hilo.isRunning():
            return
        ya = {t['ruta'] for t in self.trabajos}
        nuevos: list[tuple[int, Path]] = []
        for r in rutas:
            ruta = Path(r)
            if ruta in ya or not ruta.exists():
                continue
            ya.add(ruta)
            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)
            self.tabla.setItem(fila, COL_ARCHIVO, QTableWidgetItem(ruta.name))
            self.tabla.setItem(fila, COL_PAGINAS, QTableWidgetItem('…'))
            self.tabla.setItem(fila, COL_DIAG,    QTableWidgetItem('Analizando…'))
            self._poner_estado(fila, 'proceso', '↻  Analizando…')
            self.trabajos.append({
                'ruta': ruta, 'diag': None, 'fila': fila,
                'pendiente': False, 'detalle': '', 'salida': None,
            })
            nuevos.append((fila, ruta))
        if not nuevos:
            return
        self._sync_stack()
        hilo = Analizador(nuevos)
        hilo.listo.connect(self.al_analizar)
        hilo.finished.connect(self._cleanup_analizador)
        self._analizadores.append(hilo)
        hilo.start()
        self.barra.showMessage(f'Analizando {len(nuevos)} archivo(s)…')

    def _sync_stack(self):
        self.stack.setCurrentIndex(0 if not self.trabajos else 1)

    def al_analizar(self, fila: int, diag: Diagnostico):
        trabajo = self._trabajo(fila)
        if trabajo is None:
            return
        trabajo['diag'] = diag
        self.tabla.setItem(fila, COL_PAGINAS,
                           QTableWidgetItem(str(diag.paginas) if diag.paginas else '?'))
        self.tabla.setItem(fila, COL_DIAG, QTableWidgetItem(diag.resumen()))

        if diag.error or diag.encriptado:
            self._poner_estado(fila, 'error', '✖  No se puede procesar')
        elif diag.ya_es_accesible:
            self._poner_estado(fila, 'ok', '✔  Ya es accesible')
        else:
            trabajo['pendiente'] = True
            self._poner_estado(fila, 'aviso', '⚠  Pendiente')

        trabajo['detalle'] = f'Archivo: {diag.ruta}\nDiagnóstico: {diag.resumen()}'
        pendientes  = sum(1 for t in self.trabajos if t['pendiente'])
        analizando  = sum(1 for t in self.trabajos if t['diag'] is None)
        msg = f'{len(self.trabajos)} archivo(s) en cola — {pendientes} por convertir.'
        if analizando:
            msg += f'  Analizando {analizando} más…'
        self.barra.showMessage(msg)
        self.mostrar_detalle()

    def limpiar(self):
        if self.hilo and self.hilo.isRunning():
            return
        self.tabla.setRowCount(0)
        self.trabajos.clear()
        self.detalle.clear()
        self.progreso.setRange(0, 1000)
        self.progreso.setValue(0)
        self.etiqueta_progreso.setText('')
        self._sync_stack()
        self.barra.showMessage('Lista vacía. Agrega PDFs para comenzar.')

    # ── Conversión ────────────────────────────────────────────────────────────
    def convertir_todo(self):
        if self.hilo and self.hilo.isRunning():
            return
        if any(t['diag'] is None for t in self.trabajos):
            QMessageBox.information(self, 'OCRFlow',
                                    'Espera a que termine el análisis de los archivos.')
            return
        forzar = self.check_forzar.isChecked()
        cola = [(t['fila'], t['ruta'], t['diag'])
                for t in self.trabajos if self._convertible(t, forzar)]
        if not cola:
            QMessageBox.information(
                self, 'OCRFlow',
                'No hay archivos por convertir.\n\n'
                'Los PDFs marcados como "ya accesibles" se omiten.\n'
                'Activa "Forzar OCR" para procesarlos igualmente.')
            return

        # ── Verificar idiomas de Tesseract antes de convertir ──────────────
        idioma_ocr = self.combo_idioma.currentData()
        from core import tesseract_langs as tl
        faltantes = tl.idiomas_faltantes(idioma_ocr)
        if faltantes:
            lista = '\n'.join(f'  •  {c}' for c in faltantes)
            resp = QMessageBox.question(
                self, 'OCRFlow — Idiomas de Tesseract faltantes',
                f'Los siguientes paquetes de idioma no están instalados en Tesseract:\n\n'
                f'{lista}\n\n'
                f'¿Descargarlos e instalarlos ahora?\n'
                f'(Puede solicitarse permiso de administrador si el directorio\n'
                f'de Tesseract está protegido)',
                QMessageBox.Yes | QMessageBox.No,
            )
            if resp != QMessageBox.Yes:
                return
            self._instalar_y_convertir(faltantes, cola, idioma_ocr, forzar)
            return

        self._iniciar_conversion(cola, idioma_ocr, forzar)

    def _instalar_y_convertir(self, faltantes, cola, idioma_ocr, forzar):
        """Instala los idiomas faltantes y, al terminar, inicia la conversión."""
        self._bloquear(True)
        self._status_pill.setObjectName('statusPillBusy')
        self._status_pill.setText('● Instalando idiomas…')
        self._status_pill.style().unpolish(self._status_pill)
        self._status_pill.style().polish(self._status_pill)
        self.progreso.setRange(0, 0)  # barra indeterminada mientras descarga
        self.barra.showMessage(
            f'Descargando paquetes de idioma de Tesseract: {", ".join(faltantes)}…'
        )
        self._instalador = InstaladorIdiomas(faltantes)
        self._instalador.progreso.connect(self._al_progreso_instalacion)
        self._instalador.terminado.connect(
            lambda ok, err: self._al_terminar_instalacion(ok, err, cola, idioma_ocr, forzar)
        )
        self._instalador.start()

    def _al_progreso_instalacion(self, desc: str, frac):
        self.barra.showMessage(desc)
        if frac is not None:
            self.progreso.setRange(0, 1000)
            self.progreso.setValue(int(frac * 1000))
        else:
            self.progreso.setRange(0, 0)

    def _al_terminar_instalacion(self, ok: bool, error_msg: str, cola, idioma_ocr, forzar):
        self.progreso.setRange(0, 1000)
        self.progreso.setValue(0)
        if not ok:
            self._bloquear(False)
            self._status_pill.setObjectName('statusPill')
            self._status_pill.setText('● Listo')
            self._status_pill.style().unpolish(self._status_pill)
            self._status_pill.style().polish(self._status_pill)
            QMessageBox.critical(
                self, 'OCRFlow — Error de instalación',
                f'No se pudieron instalar los paquetes de idioma:\n\n{error_msg}'
            )
            return
        self.barra.showMessage('Idiomas instalados correctamente. Iniciando conversión…')
        self._iniciar_conversion(cola, idioma_ocr, forzar)

    def _iniciar_conversion(self, cola, idioma_ocr, forzar):
        """Crea y arranca el hilo Convertidor."""
        self._bloquear(True)
        self._status_pill.setObjectName('statusPillBusy')
        self._status_pill.setText('● Procesando…')
        self._status_pill.style().unpolish(self._status_pill)
        self._status_pill.style().polish(self._status_pill)
        self.hilo = Convertidor(
            cola,
            self.campo_salida.text().strip(),
            idioma_ocr,
            self.check_pdfa.isChecked(),
            forzar,
        )
        self.hilo.archivo_inicia.connect(self.al_iniciar_archivo)
        self.hilo.progreso_pagina.connect(self.al_progresar)
        self.hilo.fila_lista.connect(self.al_terminar_fila)
        self.hilo.todo_listo.connect(self.al_terminar_todo)
        self.hilo.start()

    def cancelar(self):
        if self.hilo and self.hilo.isRunning():
            self.hilo.cancelar()
            self.btn_cancelar.setEnabled(False)
            self.barra.showMessage(
                'Cancelando… se detendrá al terminar el archivo actual.')

    def al_iniciar_archivo(self, actual: int, total: int, fila: int):
        nombre = self.tabla.item(fila, COL_ARCHIVO).text()
        self.etiqueta_progreso.setText(f'Archivo {actual} de {total}: {nombre}')
        self.barra.showMessage(f'Convirtiendo {nombre}  ({actual} de {total})…')
        self._poner_estado(fila, 'proceso', '↻  Convirtiendo…')

    def al_progresar(self, fila: int, etapa: str, fraccion: float):
        if fraccion < 0:
            self.progreso.setRange(0, 0)
            self._poner_estado(fila, 'proceso', f'↻  {etapa}…')
        else:
            self.progreso.setRange(0, 1000)
            self.progreso.setValue(int(fraccion * 1000))
            self._poner_estado(fila, 'proceso', f'↻  {etapa} — {fraccion:.0%}')

    def al_terminar_fila(self, fila: int, estado: str, texto: str, detalle: str):
        iconos = {'ok': '✔', 'error': '✖', 'aviso': '⚠', 'neutro': '–', 'proceso': '↻'}
        icono  = iconos.get(estado, '')
        self._poner_estado(fila, estado, f'{icono}  {texto}' if icono else texto)
        trabajo = self._trabajo(fila)
        if trabajo is not None:
            if '@salida=' in detalle:
                detalle, _, salida = detalle.rpartition('\n@salida=')
                trabajo['salida'] = Path(salida)
            if detalle:
                trabajo['detalle'] += '\n\n' + detalle
            trabajo['pendiente'] = estado == 'neutro'
        self.mostrar_detalle()

    def al_terminar_todo(self, ok: int, errores: int):
        self._bloquear(False)
        self.hilo = None
        self.progreso.setRange(0, 1000)
        self.progreso.setValue(0)
        self.etiqueta_progreso.setText('')
        self._status_pill.setObjectName('statusPill')
        self._status_pill.setText('● Listo')
        self._status_pill.style().unpolish(self._status_pill)
        self._status_pill.style().polish(self._status_pill)
        pendientes = sum(1 for t in self.trabajos if t['pendiente'])
        partes = [f'{ok} convertido(s) correctamente']
        if errores:
            partes.append(f'{errores} con problema(s)')
        if pendientes:
            partes.append(f'{pendientes} cancelado(s)')
        self.barra.showMessage('Terminado: ' + ', '.join(partes) + '.')

    def _cleanup_analizador(self):
        hilo = self.sender()
        try:
            self._analizadores.remove(hilo)
        except ValueError:
            pass

    # ── Utilidades ────────────────────────────────────────────────────────────
    def _bloquear(self, ocupado: bool):
        for w in (self.btn_agregar, self.btn_carpeta,
                  self.btn_limpiar, self.btn_convertir):
            w.setEnabled(not ocupado)
        for w in (self.combo_idioma, self.check_pdfa,
                  self.check_forzar, self.campo_salida):
            w.setEnabled(not ocupado)
        self.btn_cancelar.setEnabled(ocupado)

    def _convertible(self, trabajo: dict, forzar: bool) -> bool:
        diag = trabajo['diag']
        if diag is None or diag.error or diag.encriptado:
            return False
        if diag.ya_es_accesible and not forzar:
            return False
        return True

    def _recontar(self):
        if self.hilo and self.hilo.isRunning():
            return
        forzar        = self.check_forzar.isChecked()
        por_convertir = sum(1 for t in self.trabajos if self._convertible(t, forzar))
        listos        = sum(1 for t in self.trabajos if t['diag'] is not None)
        if listos:
            self.barra.showMessage(
                f'{len(self.trabajos)} archivo(s) en cola — '
                f'{por_convertir} por convertir'
                + (' (forzando OCR).' if forzar else '.'))

    def _trabajo(self, fila: int) -> dict | None:
        for t in self.trabajos:
            if t['fila'] == fila:
                return t
        return None

    def _poner_estado(self, fila: int, clave: str, texto: str):
        color_fg, color_bg = ESTADO_COLORES.get(clave, ('#6B80B3', '#F0F4FB'))
        celda = QTableWidgetItem(texto)
        celda.setForeground(QColor(color_fg))
        celda.setBackground(QColor(color_bg))
        self.tabla.setItem(fila, COL_ESTADO, celda)

    def mostrar_detalle(self):
        fila    = self.tabla.currentRow()
        trabajo = self._trabajo(fila) if fila >= 0 else None
        self.detalle.setPlainText(trabajo['detalle'] if trabajo else '')

    def abrir_resultado(self):
        fila    = self.tabla.currentRow()
        trabajo = self._trabajo(fila) if fila >= 0 else None
        if trabajo and trabajo['salida'] and Path(trabajo['salida']).exists():
            os.startfile(trabajo['salida'])

    def acerca_de(self):
        QMessageBox.about(
            self, 'Acerca de — OCRFlow',
            '<b>OCRFlow</b> &nbsp;v1.0.0<br>'
            'Convierte PDFs escaneados o defectuosos en documentos legibles<br>'
            'por lectores de pantalla (Narrador de Windows, NVDA, JAWS).<br><br>'
            '<b>Desarrollado por:</b> Hendry Peguero<br>'
            '<b>GitHub:</b> github.com/Hendry-Peguero<br><br>'
            f'<b>Idioma del documento:</b> {IDIOMA_DOCUMENTO}<br>'
            '<b>Motor:</b> OCRmyPDF + Tesseract + pikepdf<br><br>'
            'El archivo original nunca se modifica.')

    def closeEvent(self, ev):
        if self._instalador and self._instalador.isRunning():
            resp = QMessageBox.question(
                self, 'OCRFlow',
                'Se está descargando un idioma de Tesseract. ¿Cancelar y salir?')
            if resp != QMessageBox.Yes:
                ev.ignore()
                return
            self._instalador.terminate()
            self._instalador.wait(5000)
        if self.hilo and self.hilo.isRunning():
            resp = QMessageBox.question(
                self, 'OCRFlow',
                'Hay una conversión en curso. ¿Cancelar y salir?')
            if resp != QMessageBox.Yes:
                ev.ignore()
                return
            self.hilo.cancelar()
            self.hilo.wait(15000)
        ev.accept()


# ─── Verificación de dependencias del sistema ────────────────────────────────

def _verificar_dependencias_externas(parent=None):
    """Muestra un aviso si Tesseract o Ghostscript no están disponibles."""
    faltantes = []

    if not shutil.which('tesseract'):
        # Comprobar ruta de instalación estándar en Windows
        pf = os.environ.get('ProgramFiles', r'C:\Program Files')
        if not Path(pf, 'Tesseract-OCR', 'tesseract.exe').exists():
            faltantes.append(
                'Tesseract OCR no encontrado.\n'
                '  Descarga: https://github.com/UB-Mannheim/tesseract/releases\n'
                '  Activa los idiomas Spanish y English durante la instalación.\n'
                '  Marca "Add Tesseract to PATH" al instalar.'
            )

    gs_ok = shutil.which('gswin64c') or shutil.which('gswin32c') or shutil.which('gs')
    if not gs_ok:
        pf = os.environ.get('ProgramFiles', r'C:\Program Files')
        gs_dir = Path(pf, 'gs')
        if gs_dir.exists():
            for sub in gs_dir.iterdir():
                if (sub / 'bin' / 'gswin64c.exe').exists():
                    gs_ok = True
                    break
        if not gs_ok:
            faltantes.append(
                'Ghostscript no encontrado.\n'
                '  Descarga: https://www.ghostscript.com/releases/gsdnld.html\n'
                '  Elige la versión Windows 64-bit.'
            )

    if faltantes:
        dlg = QMessageBox(parent)
        dlg.setWindowTitle('OCRFlow — Dependencias faltantes')
        dlg.setIcon(QMessageBox.Warning)
        dlg.setText(
            'Las siguientes dependencias no están instaladas.\n'
            'La conversión OCR no funcionará hasta que las instales:\n\n'
            + '\n\n'.join(faltantes)
        )
        dlg.exec()


# ─── Punto de entrada ─────────────────────────────────────────────────────────

def _forzar_foco(ventana):
    """Fuerza la ventana al frente usando Win32 cuando Qt no es suficiente."""
    ventana.setWindowFlag(Qt.WindowStaysOnTopHint, False)
    ventana.show()
    ventana.raise_()
    ventana.activateWindow()
    try:
        import ctypes
        hwnd = int(ventana.winId())
        sw = ctypes.windll.user32.ShowWindow
        sfw = ctypes.windll.user32.SetForegroundWindow
        sw(hwnd, 9)   # SW_RESTORE
        sfw(hwnd)
    except Exception:
        pass


def main():
    # Corregir TESSDATA_PREFIX inválido antes de cualquier llamada a OCR
    from core import tesseract_langs as _tl
    _tl.inicializar()

    app = QApplication(sys.argv)
    app.setApplicationName('OCRFlow')

    fuente = QFont('Segoe UI', 10)
    app.setFont(fuente)
    app.setStyleSheet(STYLESHEET)

    ventana = Ventana()
    ventana.setWindowFlag(Qt.WindowStaysOnTopHint, True)
    ventana.show()

    from PySide6.QtCore import QTimer
    QTimer.singleShot(200, lambda: _forzar_foco(ventana))

    _verificar_dependencias_externas(ventana)

    sys.exit(app.exec())


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, IOError):
        pass
    main()
