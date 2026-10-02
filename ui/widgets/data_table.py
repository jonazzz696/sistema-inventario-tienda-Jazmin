"""
Tabla reutilizable para todas las pantallas.

Cada pantalla solo describe sus columnas con Column(...) y le pasa
las filas tal cual las devuelven los controladores (sqlite3.Row o
dict). La tabla se encarga de:

- formato de cada celda (moneda, textos vacios...),
- etiquetas de estado de color (Activo / Inactivo, Entrada / Salida),
- resaltar filas (stock bajo, cliente con deuda),
- buscar sin distinguir mayusculas ni tildes,
- ordenar por columna usando el valor real (no el texto formateado),
- mostrar un mensaje util cuando no hay filas.
"""

import unicodedata

from PySide6.QtCore import (
    QAbstractTableModel, QModelIndex, QRectF, QSortFilterProxyModel, Qt, Signal,
)
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView, QHeaderView, QLabel, QStackedLayout, QStyle,
    QStyledItemDelegate, QStyleOptionViewItem, QTableView, QWidget,
)

from ui import theme

BADGE_ROLE = int(Qt.UserRole) + 1
RAW_ROLE = int(Qt.UserRole) + 2

_ALIGN = {
    "left": Qt.AlignLeft | Qt.AlignVCenter,
    "center": Qt.AlignCenter,
    "right": Qt.AlignRight | Qt.AlignVCenter,
}


def normalizar(texto):
    """'Categoría' -> 'categoria' (para buscar sin importar tildes)."""
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    return "".join(c for c in texto if not unicodedata.combining(c)).lower()


class Column:
    """
    Describe una columna.

    key:     clave de la fila (p. ej. "nombre", "precio_venta").
    title:   texto del encabezado.
    fmt:     funcion valor -> texto a mostrar (opcional).
    value:   funcion fila -> valor, si la columna combina varios campos.
    badge:   funcion fila -> (texto, tipo) para mostrar una etiqueta de
             color; tipo es "success", "warning", "danger", "info" o "neutral".
    align:   "left", "center" o "right".
    width:   ancho inicial en px. stretch=True reparte el espacio sobrante.
    """

    def __init__(self, key, title, fmt=None, value=None, badge=None,
                 align="left", width=120, stretch=False):
        self.key = key
        self.title = title
        self.fmt = fmt
        self.value = value
        self.badge = badge
        self.align = align
        self.width = width
        self.stretch = stretch

    def raw(self, fila):
        if self.value is not None:
            return self.value(fila)
        return fila.get(self.key) if isinstance(fila, dict) else fila[self.key]

    def text(self, fila):
        if self.badge is not None:
            return self.badge(fila)[0]
        valor = self.raw(fila)
        if self.fmt is not None:
            return self.fmt(valor)
        return "" if valor is None else str(valor)


class RowsModel(QAbstractTableModel):
    def __init__(self, columns, highlight=None, parent=None):
        super().__init__(parent)
        self.columns = columns
        self.highlight = highlight
        self.rows = []

    def set_rows(self, filas):
        self.beginResetModel()
        # sqlite3.Row -> dict, para poder usar .get() y guardar copias.
        self.rows = [dict(f) for f in filas]
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.columns)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self.columns[section].title
            if role == Qt.TextAlignmentRole:
                return _ALIGN[self.columns[section].align]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        fila = self.rows[index.row()]
        columna = self.columns[index.column()]

        if role == Qt.DisplayRole:
            return columna.text(fila)
        if role == Qt.ToolTipRole:
            texto = columna.text(fila)
            return texto if len(texto) > 28 else None
        if role == Qt.TextAlignmentRole:
            return _ALIGN[columna.align]
        if role == BADGE_ROLE and columna.badge is not None:
            return columna.badge(fila)[1]
        if role == RAW_ROLE:
            valor = columna.raw(fila)
            return valor if valor is not None else ""
        if role == Qt.BackgroundRole and self.highlight is not None:
            tipo = self.highlight(fila)
            if tipo in theme.ROW_HIGHLIGHT:
                return QBrush(QColor(theme.ROW_HIGHLIGHT[tipo]))
        return None


class FilterProxy(QSortFilterProxyModel):
    """Filtro por texto libre + un filtro adicional opcional (funcion fila -> bool)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._texto = ""
        self._predicado = None
        self.setSortRole(RAW_ROLE)
        self.setSortCaseSensitivity(Qt.CaseInsensitive)

    def set_text(self, texto):
        self._texto = normalizar(texto.strip())
        self.invalidateFilter()

    def set_predicate(self, predicado):
        self._predicado = predicado
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        modelo = self.sourceModel()
        fila = modelo.rows[source_row]
        if self._predicado is not None and not self._predicado(fila):
            return False
        if not self._texto:
            return True
        contenido = " ".join(c.text(fila) for c in modelo.columns)
        return all(parte in normalizar(contenido) for parte in self._texto.split())

    def lessThan(self, izquierda, derecha):
        a = izquierda.data(RAW_ROLE)
        b = derecha.data(RAW_ROLE)
        try:
            return a < b
        except TypeError:
            return normalizar(a) < normalizar(b)


class BadgeDelegate(QStyledItemDelegate):
    """Dibuja una etiqueta redondeada de color en las columnas de estado."""

    def paint(self, painter, option, index):
        tipo = index.data(BADGE_ROLE)
        if tipo is None:
            super().paint(painter, option, index)
            return

        # Fondo de la celda (seleccion, hover, fila resaltada) igual que el resto.
        opcion = QStyleOptionViewItem(option)
        self.initStyleOption(opcion, index)
        opcion.text = ""
        widget = option.widget
        estilo = widget.style() if widget else None
        if estilo:
            estilo.drawControl(QStyle.CE_ItemViewItem, opcion, painter, widget)

        texto = index.data(Qt.DisplayRole) or ""
        color, fondo = theme.BADGE_COLORS.get(tipo, theme.BADGE_COLORS["neutral"])

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        fuente = QFont(option.font)
        fuente.setPixelSize(13)
        fuente.setWeight(QFont.Weight.DemiBold)
        painter.setFont(fuente)
        metrica = painter.fontMetrics()
        ancho = metrica.horizontalAdvance(texto) + 22
        alto = 26
        rect = option.rect
        columnas = getattr(index.model().sourceModel(), "columns", None) \
            if hasattr(index.model(), "sourceModel") else None
        centrado = bool(columnas) and columnas[index.column()].align == "center"
        if centrado:
            x = rect.x() + (rect.width() - ancho) / 2
        else:
            x = rect.x() + 12
        y = rect.y() + (rect.height() - alto) / 2
        pastilla = QRectF(x, y, ancho, alto)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(fondo))
        painter.drawRoundedRect(pastilla, alto / 2, alto / 2)
        painter.setPen(QPen(QColor(color)))
        painter.drawText(pastilla, Qt.AlignCenter, texto)
        painter.restore()


class DataTable(QWidget):
    """
    Tabla lista para usar.

    Senales:
        selection_changed(dict | None)  al cambiar la fila seleccionada
        row_activated(dict)             doble clic o Enter sobre una fila
    """

    selection_changed = Signal(object)
    row_activated = Signal(object)

    def __init__(self, columns, empty_text="No hay datos para mostrar.",
                 empty_filtered_text="No hay resultados con esa busqueda.",
                 highlight=None, min_height=260, parent=None):
        super().__init__(parent)
        self.columns = columns
        self._empty_text = empty_text
        self._empty_filtered_text = empty_filtered_text

        self.model = RowsModel(columns, highlight, self)
        self.proxy = FilterProxy(self)
        self.proxy.setSourceModel(self.model)

        self.view = QTableView()
        self.view.setModel(self.proxy)
        self.view.setItemDelegate(BadgeDelegate(self.view))
        self.view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.view.setShowGrid(False)
        self.view.setWordWrap(False)
        self.view.setMouseTracking(True)
        self.view.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.view.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.view.setMinimumHeight(min_height)
        self.view.setTextElideMode(Qt.ElideRight)
        self.view.setFocusPolicy(Qt.StrongFocus)

        vertical = self.view.verticalHeader()
        vertical.setVisible(False)
        vertical.setDefaultSectionSize(theme.TABLE_ROW_HEIGHT)
        vertical.setSectionResizeMode(QHeaderView.Fixed)

        horizontal = self.view.horizontalHeader()
        horizontal.setHighlightSections(False)
        horizontal.setMinimumSectionSize(70)
        horizontal.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        horizontal.setSortIndicatorShown(True)
        for i, columna in enumerate(columns):
            if columna.stretch:
                horizontal.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                horizontal.setSectionResizeMode(i, QHeaderView.Interactive)
                self.view.setColumnWidth(i, columna.width)
        # Arranca sin orden aplicado: respeta el orden que da la consulta SQL.
        horizontal.setSortIndicator(-1, Qt.AscendingOrder)
        self.view.setSortingEnabled(True)

        self.empty_label = QLabel()
        self.empty_label.setProperty("role", "empty")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setWordWrap(True)
        self.empty_label.setMinimumHeight(min(min_height, 160))

        self._stack = QStackedLayout(self)
        self._stack.setContentsMargins(0, 0, 0, 0)
        self._stack.addWidget(self.view)
        self._stack.addWidget(self.empty_label)

        self.view.selectionModel().selectionChanged.connect(self._on_selection)
        self.view.doubleClicked.connect(self._on_activated)
        self.view.activated.connect(self._on_activated)
        for senal in (self.proxy.modelReset, self.proxy.rowsInserted,
                      self.proxy.rowsRemoved, self.proxy.layoutChanged):
            senal.connect(self._update_empty_state)

        self._update_empty_state()

    # --- API publica ---

    def set_rows(self, filas):
        self.model.set_rows(filas)
        self._update_empty_state()
        self.selection_changed.emit(None)

    def rows(self):
        return self.model.rows

    def set_filter_text(self, texto):
        self.proxy.set_text(texto)
        self._update_empty_state()

    def set_predicate(self, predicado):
        self.proxy.set_predicate(predicado)
        self._update_empty_state()

    def selected_row(self):
        indices = self.view.selectionModel().selectedRows() if self.view.selectionModel() else []
        if not indices:
            return None
        fila_fuente = self.proxy.mapToSource(indices[0]).row()
        if 0 <= fila_fuente < len(self.model.rows):
            return self.model.rows[fila_fuente]
        return None

    def selected_source_index(self):
        indices = self.view.selectionModel().selectedRows()
        return self.proxy.mapToSource(indices[0]).row() if indices else None

    def select_by(self, key, valor):
        """Vuelve a seleccionar la fila cuyo campo key == valor (tras recargar)."""
        for i, fila in enumerate(self.model.rows):
            if fila.get(key) == valor:
                indice = self.proxy.mapFromSource(self.model.index(i, 0))
                if indice.isValid():
                    self.view.selectRow(indice.row())
                    self.view.scrollTo(indice)
                return

    def set_empty_text(self, texto):
        self._empty_text = texto
        self._update_empty_state()

    # --- internos ---

    def _on_selection(self, *_):
        self.selection_changed.emit(self.selected_row())

    def _on_activated(self, indice):
        fila = self.model.rows[self.proxy.mapToSource(indice).row()]
        self.row_activated.emit(fila)

    def _update_empty_state(self, *_):
        if self.proxy.rowCount() > 0:
            self._stack.setCurrentWidget(self.view)
            return
        hay_datos = self.model.rowCount() > 0
        self.empty_label.setText(self._empty_filtered_text if hay_datos else self._empty_text)
        self._stack.setCurrentWidget(self.empty_label)
