"""
Graficos de la interfaz, dibujados con QPainter.

No dependen de bibliotecas extra y usan los colores del tema. Todos
muestran un mensaje cuando no hay datos, y los de barras muestran el
valor exacto al pasar el mouse.

  BarChart         barras verticales (una o varias series), eje de tiempo
  HorizontalBars   ranking (productos mas vendidos)
  DonutChart       distribucion (ventas por metodo de pago)
"""

import math

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QToolTip, QWidget

from ui import theme


def _paso_bonito(maximo, divisiones=4):
    if maximo <= 0:
        return 1
    bruto = maximo / divisiones
    magnitud = 10 ** math.floor(math.log10(bruto))
    for factor in (1, 2, 2.5, 5, 10):
        if bruto <= factor * magnitud:
            return factor * magnitud
    return 10 * magnitud


def _fuente(base, px, negrita=False):
    fuente = QFont(base)
    fuente.setPixelSize(px)
    if negrita:
        fuente.setWeight(QFont.Weight.DemiBold)
    return fuente


class _Chart(QWidget):
    def __init__(self, altura=260, vacio="Sin datos en este período.", parent=None):
        super().__init__(parent)
        self._vacio = vacio
        self._altura = altura
        self.setMinimumHeight(altura)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMouseTracking(True)

    def sizeHint(self):
        return QSize(400, self._altura)

    def _pintar_vacio(self, painter):
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        painter.setPen(QPen(QColor(theme.BORDER), 1, Qt.DashLine))
        painter.setBrush(QColor(theme.SURFACE_ALT))
        painter.drawRoundedRect(rect, 10, 10)
        painter.setPen(QColor(theme.TEXT_MUTED))
        painter.setFont(_fuente(self.font(), 14))
        painter.drawText(rect, Qt.AlignCenter | Qt.TextWordWrap, self._vacio)


class BarChart(_Chart):
    """
    series: lista de (nombre, color). formato: funcion valor -> texto
    (para el eje y el tooltip).
    """

    def __init__(self, series, formato=None, altura=260, vacio="Sin datos en este período.",
                 formato_tooltip=None, parent=None):
        super().__init__(altura, vacio, parent)
        self._series = series
        self._formato = formato or (lambda v: f"{v:,.0f}")
        self._formato_tooltip = formato_tooltip or self._formato
        self._etiquetas = []
        self._valores = []          # una lista por serie
        self._zonas = []            # (QRectF, indice) para el tooltip

    def set_data(self, etiquetas, valores_por_serie):
        self._etiquetas = list(etiquetas)
        self._valores = [list(v) for v in valores_por_serie]
        self.update()

    def _maximo(self):
        return max((max(v) for v in self._valores if v), default=0)

    def paintEvent(self, _evento):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self._zonas = []
        maximo = self._maximo()
        if not self._etiquetas or maximo <= 0:
            self._pintar_vacio(painter)
            return

        fuente_eje = _fuente(self.font(), 12)
        metrica = QFontMetrics(fuente_eje)
        paso = _paso_bonito(maximo)
        tope = paso * math.ceil(maximo / paso)
        marcas = [paso * i for i in range(int(round(tope / paso)) + 1)]
        ancho_eje = max(metrica.horizontalAdvance(self._formato(m)) for m in marcas) + 12

        alto_leyenda = 28 if len(self._series) > 1 else 6
        area = QRectF(ancho_eje, alto_leyenda, self.width() - ancho_eje - 8,
                      self.height() - alto_leyenda - 28)

        # Leyenda
        if len(self._series) > 1:
            x = area.left()
            painter.setFont(_fuente(self.font(), 13))
            for nombre, color in self._series:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(color))
                painter.drawRoundedRect(QRectF(x, 6, 12, 12), 3, 3)
                painter.setPen(QColor(theme.TEXT))
                painter.drawText(QPointF(x + 18, 17), nombre)
                x += 18 + QFontMetrics(painter.font()).horizontalAdvance(nombre) + 22

        # Lineas guia y valores del eje
        painter.setFont(fuente_eje)
        for m in marcas:
            y = area.bottom() - (m / tope) * area.height()
            painter.setPen(QPen(QColor(theme.BORDER), 1))
            painter.drawLine(QPointF(area.left(), y), QPointF(area.right(), y))
            painter.setPen(QColor(theme.TEXT_MUTED))
            painter.drawText(QRectF(0, y - 9, ancho_eje - 8, 18), Qt.AlignRight | Qt.AlignVCenter, self._formato(m))

        # Barras
        n = len(self._etiquetas)
        series_n = len(self._valores)
        ancho_grupo = area.width() / n
        hueco = min(ancho_grupo * 0.28, 18)
        ancho_barra = max(2.0, (ancho_grupo - hueco) / series_n)
        radio = min(4.0, ancho_barra / 3)

        for i in range(n):
            x0 = area.left() + i * ancho_grupo + hueco / 2
            for s in range(series_n):
                valor = self._valores[s][i] if i < len(self._valores[s]) else 0
                if valor <= 0:
                    continue
                alto = (valor / tope) * area.height()
                rect = QRectF(x0 + s * ancho_barra, area.bottom() - alto, ancho_barra - (1 if series_n > 1 else 0), alto)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(self._series[s][1]))
                painter.drawRoundedRect(rect, radio, radio)
                painter.drawRect(QRectF(rect.left(), rect.bottom() - radio, rect.width(), radio))
            self._zonas.append((QRectF(area.left() + i * ancho_grupo, area.top(), ancho_grupo, area.height() + 28), i))

        # Etiquetas del eje X (se saltan si no caben)
        painter.setPen(QColor(theme.TEXT_MUTED))
        ancho_etiqueta = max(metrica.horizontalAdvance(t) for t in self._etiquetas) + 10
        salto = max(1, math.ceil(ancho_etiqueta / ancho_grupo))
        for i, texto in enumerate(self._etiquetas):
            if i % salto:
                continue
            x = area.left() + i * ancho_grupo
            painter.drawText(QRectF(x - 20, area.bottom() + 6, ancho_grupo + 40, 18), Qt.AlignHCenter | Qt.AlignTop, texto)

    def mouseMoveEvent(self, evento):
        punto = evento.position()
        for rect, i in self._zonas:
            if rect.contains(punto):
                lineas = [self._etiquetas[i]]
                for (nombre, _), valores in zip(self._series, self._valores):
                    lineas.append(f"{nombre}: {self._formato_tooltip(valores[i])}")
                QToolTip.showText(evento.globalPosition().toPoint(), "\n".join(lineas), self)
                return
        QToolTip.hideText()


class HorizontalBars(_Chart):
    """Ranking: cada fila es (nombre, valor, texto_a_mostrar)."""

    ALTO_FILA = 34

    def __init__(self, color=theme.PRIMARY, vacio="Sin datos en este período.", parent=None):
        super().__init__(120, vacio, parent)
        self._color = color
        self._filas = []

    def set_data(self, filas):
        self._filas = list(filas)
        self._altura = max(120, len(self._filas) * self.ALTO_FILA + 8)
        self.setMinimumHeight(self._altura)
        self.updateGeometry()
        self.update()

    def paintEvent(self, _evento):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        maximo = max((v for _, v, _ in self._filas), default=0)
        if maximo <= 0:
            self._pintar_vacio(painter)
            return

        fuente = _fuente(self.font(), 13)
        fuente_valor = _fuente(self.font(), 12, negrita=True)
        painter.setFont(fuente)
        metrica = QFontMetrics(fuente)
        ancho_nombre = min(self.width() * 0.38, max(metrica.horizontalAdvance(n) for n, _, _ in self._filas) + 12)
        ancho_valor = max(QFontMetrics(fuente_valor).horizontalAdvance(t) for _, _, t in self._filas) + 12
        ancho_barras = max(40.0, self.width() - ancho_nombre - ancho_valor - 4)

        for i, (nombre, valor, texto) in enumerate(self._filas):
            y = 4 + i * self.ALTO_FILA
            painter.setFont(fuente)
            painter.setPen(QColor(theme.TEXT))
            nombre_corto = metrica.elidedText(nombre, Qt.ElideRight, int(ancho_nombre - 10))
            painter.drawText(QRectF(0, y, ancho_nombre - 10, self.ALTO_FILA - 6),
                             Qt.AlignRight | Qt.AlignVCenter, nombre_corto)
            fondo = QRectF(ancho_nombre, y + 7, ancho_barras, self.ALTO_FILA - 20)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(theme.SURFACE_ALT))
            painter.drawRoundedRect(fondo, 5, 5)
            barra = QRectF(fondo.left(), fondo.top(), max(4.0, ancho_barras * valor / maximo), fondo.height())
            painter.setBrush(QColor(self._color))
            painter.drawRoundedRect(barra, 5, 5)
            painter.setFont(fuente_valor)
            painter.setPen(QColor(theme.TEXT_MUTED))
            painter.drawText(QRectF(fondo.right() + 8, y, ancho_valor, self.ALTO_FILA - 6),
                             Qt.AlignLeft | Qt.AlignVCenter, texto)


class DonutChart(_Chart):
    """Partes: lista de (nombre, valor, color, detalle)."""

    def __init__(self, formato=None, altura=240, vacio="Sin datos en este período.", parent=None):
        super().__init__(altura, vacio, parent)
        self._partes = []
        self._formato = formato or (lambda v: f"{v:,.0f}")

    def set_data(self, partes):
        self._partes = [p for p in partes if p[1] > 0]
        self.update()

    def paintEvent(self, _evento):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        total = sum(p[1] for p in self._partes)
        if total <= 0:
            self._pintar_vacio(painter)
            return

        diametro = min(self.height() - 20, self.width() * 0.42)
        grosor = diametro * 0.2
        rect = QRectF(10 + grosor / 2, (self.height() - diametro) / 2 + grosor / 2,
                      diametro - grosor, diametro - grosor)
        inicio = 90 * 16
        for nombre, valor, color, _ in self._partes:
            arco = -int(round(valor / total * 360 * 16))
            painter.setPen(QPen(QColor(color), grosor, Qt.SolidLine, Qt.FlatCap))
            painter.drawArc(rect, inicio, arco)
            inicio += arco

        # Total al centro
        painter.setPen(QColor(theme.TEXT))
        painter.setFont(_fuente(self.font(), 16, negrita=True))
        painter.drawText(rect.adjusted(0, -10, 0, -10), Qt.AlignCenter, self._formato(total))
        painter.setPen(QColor(theme.TEXT_MUTED))
        painter.setFont(_fuente(self.font(), 12))
        painter.drawText(rect.adjusted(0, 22, 0, 22), Qt.AlignCenter, "total")

        # Leyenda
        x = 10 + diametro + 24
        alto_item = 44
        y = (self.height() - len(self._partes) * alto_item) / 2
        for nombre, valor, color, detalle in self._partes:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(color))
            painter.drawRoundedRect(QRectF(x, y + 4, 12, 12), 3, 3)
            painter.setPen(QColor(theme.TEXT))
            painter.setFont(_fuente(self.font(), 14, negrita=True))
            painter.drawText(QPointF(x + 20, y + 15), f"{nombre}  {valor / total * 100:.0f}%")
            painter.setPen(QColor(theme.TEXT_MUTED))
            painter.setFont(_fuente(self.font(), 12))
            painter.drawText(QPointF(x + 20, y + 33), detalle)
            y += alto_item
