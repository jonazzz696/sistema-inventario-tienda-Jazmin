"""Menu lateral de navegacion."""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QFrame, QPushButton, QVBoxLayout

from ui import theme
from ui.icons import icon
from ui.widgets.common import divider


class Sidebar(QFrame):
    """
    Lista de secciones. items es una lista de grupos; cada grupo es una
    lista de (clave, texto, nombre_icono). Entre grupos se dibuja una
    linea divisoria. Emite page_selected(clave) al hacer clic.
    """

    page_selected = Signal(str)

    def __init__(self, grupos, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(236)

        disposicion = QVBoxLayout(self)
        disposicion.setContentsMargins(14, 18, 14, 18)
        disposicion.setSpacing(4)

        self._grupo = QButtonGroup(self)
        self._grupo.setExclusive(True)
        self._botones = {}

        for i, grupo in enumerate(grupos):
            if i > 0:
                disposicion.addSpacing(8)
                disposicion.addWidget(divider())
                disposicion.addSpacing(8)
            for clave, texto, nombre_icono in grupo:
                boton = QPushButton(f"  {texto}")
                boton.setObjectName("NavButton")
                boton.setCheckable(True)
                boton.setCursor(Qt.PointingHandCursor)
                boton.setIcon(icon(nombre_icono, theme.TEXT_MUTED, 20, checked_color=theme.PRIMARY))
                boton.setIconSize(QSize(20, 20))
                boton.clicked.connect(lambda _=False, c=clave: self.page_selected.emit(c))
                self._grupo.addButton(boton)
                self._botones[clave] = boton
                disposicion.addWidget(boton)

        disposicion.addStretch(1)

    def set_current(self, clave):
        boton = self._botones.get(clave)
        if boton is not None:
            boton.setChecked(True)

    def set_shortcut_hint(self, clave, atajo):
        boton = self._botones.get(clave)
        if boton is not None:
            boton.setToolTip(f"Atajo: {atajo}")
