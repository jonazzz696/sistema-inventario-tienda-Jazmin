"""Tarjeta de indicador para la pantalla de Inicio."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QVBoxLayout

from ui.widgets.common import Card, IconTile, label


class StatCard(Card):
    """
    Muestra un numero grande con su nombre y un detalle opcional.
    Si se le da un destino, toda la tarjeta es clicable (emite clicked).
    """

    clicked = Signal()

    def __init__(self, titulo, icon_name, kind="primary", clickable=False, parent=None):
        super().__init__(padding=20, spacing=12, parent=parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumWidth(200)

        fila = QHBoxLayout()
        fila.setSpacing(12)
        fila.addWidget(label(titulo, "statLabel"), 1, Qt.AlignVCenter)
        fila.addWidget(IconTile(icon_name, kind, 40, 20), 0, Qt.AlignTop)
        self.body.addLayout(fila)

        textos = QVBoxLayout()
        textos.setSpacing(2)
        self.value_label = label("-", "statValue")
        self.detail_label = label("", "caption", wrap=True)
        textos.addWidget(self.value_label)
        textos.addWidget(self.detail_label)
        self.body.addLayout(textos)

        self._clickable = clickable
        if clickable:
            self.setCursor(Qt.PointingHandCursor)
            self.setToolTip("Abrir")

    def set_value(self, valor, detalle=""):
        self.value_label.setText(str(valor))
        self.detail_label.setText(detalle)
        self.detail_label.setVisible(bool(detalle))

    def mouseReleaseEvent(self, evento):
        if self._clickable and evento.button() == Qt.LeftButton and self.rect().contains(evento.position().toPoint()):
            self.clicked.emit()
        super().mouseReleaseEvent(evento)
