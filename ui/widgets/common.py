"""
Piezas pequenas que usan todas las pantallas.

Los estilos viven en styles/theme.qss; aqui solo se marcan los
widgets con propiedades (variant, role, card...) para que el QSS
sepa como pintarlos. Asi no hay colores escritos en cada pantalla.
"""

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)

from ui import theme
from ui.icons import icon

_COLOR_ICONO = {
    "primary": "#ffffff",
    "danger": "#ffffff",
    "secondary": theme.TEXT,
    "ghost": theme.TEXT_MUTED,
}


def repolish(widget):
    """Vuelve a aplicar el QSS despues de cambiar una propiedad dinamica."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


def label(texto="", role=None, wrap=False, parent=None):
    etiqueta = QLabel(texto, parent)
    if role:
        etiqueta.setProperty("role", role)
    if wrap:
        etiqueta.setWordWrap(True)
    return etiqueta


def button(texto, icon_name=None, variant="secondary", large=False, tooltip=None, on_click=None):
    """
    Crea un boton con el estilo del tema.

    variant: "primary" (accion principal, una por zona), "secondary",
             "ghost" (accion de bajo peso) o "danger" (acciones destructivas).
    """
    boton = QPushButton(texto)
    boton.setProperty("variant", variant)
    if large:
        boton.setProperty("size", "large")
    if icon_name:
        boton.setIcon(icon(icon_name, _COLOR_ICONO.get(variant, theme.TEXT), 18))
        boton.setIconSize(QSize(18, 18))
    if tooltip:
        boton.setToolTip(tooltip)
    boton.setCursor(Qt.PointingHandCursor)
    if on_click:
        boton.clicked.connect(on_click)
    return boton


class Card(QFrame):
    """Panel blanco con borde suave. Su layout interno es self.body."""

    def __init__(self, titulo=None, subtitulo=None, padding=20, spacing=14, parent=None):
        super().__init__(parent)
        self.setProperty("card", True)
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(padding, padding, padding, padding)
        self.body.setSpacing(spacing)

        self.header = None
        self.subtitle_label = None
        if titulo:
            self.header = QHBoxLayout()
            self.header.setSpacing(12)
            textos = QVBoxLayout()
            textos.setSpacing(2)
            textos.addWidget(label(titulo, "section"))
            if subtitulo:
                self.subtitle_label = label(subtitulo, "caption", wrap=True)
                textos.addWidget(self.subtitle_label)
            self.header.addLayout(textos, 1)
            self.body.addLayout(self.header)

    def add_header_widget(self, widget):
        """Agrega un boton u otro control a la derecha del titulo."""
        if self.header is not None:
            self.header.addWidget(widget, 0, Qt.AlignTop)


class IconTile(QLabel):
    """Cuadro de color suave con un icono dentro (tarjetas del inicio, mensajes)."""

    def __init__(self, icon_name, kind="primary", size=44, icon_size=22, parent=None):
        super().__init__(parent)
        from ui.icons import pixmap

        colores = {
            "primary": (theme.PRIMARY, theme.PRIMARY_SOFT),
            **{k: v for k, v in theme.BADGE_COLORS.items()},
        }
        color, fondo = colores.get(kind, colores["primary"])
        self.setObjectName("IconTile")
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        self.setPixmap(pixmap(icon_name, color, icon_size))
        self.setStyleSheet(f"background: {fondo}; border-radius: {size // 4}px;")


def hspacer():
    espacio = QWidget()
    espacio.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    return espacio


def divider():
    linea = QFrame()
    linea.setObjectName("SidebarDivider")
    linea.setFrameShape(QFrame.NoFrame)
    return linea
