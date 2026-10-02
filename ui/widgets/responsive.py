"""
Rejilla que se reacomoda sola segun el ancho disponible.

Ejemplo: 4 tarjetas en una fila en 1920x1080, 2x2 en 1366x768 y
una debajo de otra en ventanas muy angostas.
"""

from PySide6.QtWidgets import QGridLayout, QWidget


class ResponsiveGrid(QWidget):
    def __init__(self, breakpoints, spacing=18, parent=None):
        """
        breakpoints: lista de (ancho_minimo, columnas) de mayor a menor,
        p. ej. [(1100, 4), (640, 2), (0, 1)].
        """
        super().__init__(parent)
        self._breakpoints = sorted(breakpoints, reverse=True)
        self._items = []
        self._columnas = None
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(spacing)
        self.grid.setVerticalSpacing(spacing)

    def add(self, widget, peso=1):
        self._items.append((widget, peso))
        self._reflow(force=True)

    def _columnas_para(self, ancho):
        for minimo, columnas in self._breakpoints:
            if ancho >= minimo:
                return columnas
        return 1

    def _reflow(self, force=False):
        columnas = self._columnas_para(self.width())
        if columnas == self._columnas and not force:
            return
        self._columnas = columnas
        for widget, _ in self._items:
            self.grid.removeWidget(widget)
        for c in range(self.grid.columnCount()):
            self.grid.setColumnStretch(c, 0)
        for i, (widget, peso) in enumerate(self._items):
            fila, col = divmod(i, columnas)
            self.grid.addWidget(widget, fila, col)
            if fila == 0:
                self.grid.setColumnStretch(col, peso)

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        self._reflow()
