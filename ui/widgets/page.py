"""
Base para todas las pantallas del contenido.

Cada pantalla hereda de Page y:
  - llama a super().__init__(titulo, subtitulo),
  - agrega sus widgets en self.content (QVBoxLayout),
  - pone botones de accion con self.add_action(boton),
  - implementa refresh(), que la ventana principal llama cada vez que
    se entra a la pantalla (asi los datos siempre estan al dia, igual
    que antes cuando se recreaba el Frame de Tkinter).

El contenido va dentro de un area desplazable: en pantallas pequenas
(1366x768 o menos) aparece una barra de desplazamiento en lugar de
cortar elementos.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QScrollArea, QVBoxLayout, QWidget

from ui.widgets.common import label


class Page(QWidget):
    def __init__(self, titulo, subtitulo="", parent=None):
        super().__init__(parent)
        self.setObjectName("PageBody")

        externo = QVBoxLayout(self)
        externo.setContentsMargins(0, 0, 0, 0)
        externo.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("PageScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        externo.addWidget(self.scroll)

        interior = QWidget()
        interior.setObjectName("PageBody")
        self.scroll.setWidget(interior)

        self.content = QVBoxLayout(interior)
        self.content.setContentsMargins(32, 28, 32, 32)
        self.content.setSpacing(20)

        encabezado = QHBoxLayout()
        encabezado.setSpacing(12)
        textos = QVBoxLayout()
        textos.setSpacing(4)
        self.title_label = label(titulo, "title")
        textos.addWidget(self.title_label)
        self.subtitle_label = label(subtitulo, "subtitle", wrap=True)
        self.subtitle_label.setVisible(bool(subtitulo))
        textos.addWidget(self.subtitle_label)
        encabezado.addLayout(textos, 1)

        self._acciones = QHBoxLayout()
        self._acciones.setSpacing(10)
        encabezado.addLayout(self._acciones)
        self.content.addLayout(encabezado)

    def add_action(self, widget):
        self._acciones.addWidget(widget, 0, Qt.AlignBottom)
        return widget

    def refresh(self):
        """Recarga los datos desde la base. Cada pantalla lo implementa."""
