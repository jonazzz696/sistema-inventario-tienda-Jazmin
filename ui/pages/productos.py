"""
Pantalla de Productos.

Funciones existentes que usa (sin cambios):
  controlador_productos.obtener_lista_productos()
  controlador_productos.obtener_producto_por_id()
  controlador_productos.alternar_estado_producto()
  controlador_categorias.obtener_lista_categorias()
  + ProductoDialog -> registrar_producto / modificar_producto

Nota: el sistema no borra productos (se desactivan para no perder el
historial de ventas), por eso la accion es Activar/Desactivar.
"""

from PySide6.QtWidgets import QHBoxLayout

from controllers import controlador_categorias, controlador_productos
from helpers.formato import centavos_a_texto
from ui.dialogs.producto_dialog import ProductoDialog
from ui.formato_ui import badge_estado
from ui.widgets import messages
from ui.widgets.common import Card, button, label
from ui.widgets.data_table import Column, DataTable
from ui.widgets.forms import SearchField, choice_combo
from ui.widgets.page import Page


def _badge_stock(fila):
    if fila["estado"] != 1:
        return ("Sin uso", "neutral")
    if fila["existencia"] == 0:
        return ("Agotado", "danger")
    if fila["existencia"] <= fila["stock_minimo"]:
        return ("Bajo", "warning")
    return ("Disponible", "success")


class ProductosPage(Page):
    def __init__(self, navigate):
        super().__init__("Productos", "Catálogo de productos, precios y existencias.")
        self.navigate = navigate

        self.add_action(button("Nuevo producto", "plus", "primary", on_click=self._nuevo))

        tarjeta = Card(padding=18)

        # --- Barra de busqueda y filtros ---
        barra = QHBoxLayout()
        barra.setSpacing(10)
        self.buscador = SearchField("Buscar por código, nombre o categoría")
        self.buscador.textChanged.connect(self._aplicar_filtros)
        barra.addWidget(self.buscador, 2)

        self.filtro_categoria = choice_combo([("Todas las categorías", None)])
        self.filtro_categoria.setMinimumWidth(200)
        self.filtro_categoria.currentIndexChanged.connect(self._aplicar_filtros)
        barra.addWidget(self.filtro_categoria, 1)

        self.filtro_estado = choice_combo([("Activos", 1), ("Inactivos", 0), ("Todos", None)])
        self.filtro_estado.setMinimumWidth(140)
        self.filtro_estado.currentIndexChanged.connect(self._aplicar_filtros)
        barra.addWidget(self.filtro_estado)
        barra.addStretch(0)

        self.boton_editar = button("Editar", "edit", "secondary", on_click=self._editar,
                                   tooltip="Editar el producto seleccionado (doble clic)")
        self.boton_estado = button("Desactivar", "power", "secondary", on_click=self._alternar_estado)
        barra.addWidget(self.boton_editar)
        barra.addWidget(self.boton_estado)
        tarjeta.body.addLayout(barra)

        # --- Tabla ---
        self.tabla = DataTable(
            [
                Column("codigo", "Código", width=120),
                Column("nombre", "Producto", stretch=True),
                Column("nombre_categoria", "Categoría", width=170),
                Column("precio_venta", "Precio venta", fmt=centavos_a_texto, align="right", width=130),
                Column("existencia", "Existencia", align="center", width=110),
                Column("stock", "Stock", align="center", width=120, badge=_badge_stock,
                       value=lambda f: (f["estado"] != 1, f["existencia"] - f["stock_minimo"])),
                Column("estado", "Estado", align="center", width=110, badge=badge_estado),
            ],
            empty_text="Aún no hay productos. Usa \"Nuevo producto\" para agregar el primero.",
            empty_filtered_text="Ningún producto coincide con la búsqueda o los filtros.",
            highlight=lambda f: ("danger" if f["estado"] == 1 and f["existencia"] == 0 else
                                 "warning" if f["estado"] == 1 and f["existencia"] <= f["stock_minimo"]
                                 else None),
            min_height=380,
        )
        self.tabla.selection_changed.connect(self._al_seleccionar)
        self.tabla.row_activated.connect(lambda _: self._editar())
        tarjeta.body.addWidget(self.tabla, 1)

        self.resumen = label("", "caption")
        tarjeta.body.addWidget(self.resumen)

        self.content.addWidget(tarjeta, 1)
        self._al_seleccionar(None)

    # --- Datos ---

    def refresh(self, seleccionar_id=None):
        categoria_elegida = self.filtro_categoria.currentData()
        self.filtro_categoria.blockSignals(True)
        self.filtro_categoria.clear()
        self.filtro_categoria.addItem("Todas las categorías", None)
        for c in controlador_categorias.obtener_lista_categorias():
            self.filtro_categoria.addItem(c["nombre"], c["id_categoria"])
        indice = self.filtro_categoria.findData(categoria_elegida)
        self.filtro_categoria.setCurrentIndex(max(indice, 0))
        self.filtro_categoria.blockSignals(False)

        self.tabla.set_rows(controlador_productos.obtener_lista_productos())
        self._aplicar_filtros()
        if seleccionar_id is not None:
            self.tabla.select_by("id_producto", seleccionar_id)

    def _aplicar_filtros(self, *_):
        id_categoria = self.filtro_categoria.currentData()
        estado = self.filtro_estado.currentData()

        def predicado(fila):
            if id_categoria is not None and fila["id_categoria"] != id_categoria:
                return False
            if estado is not None and fila["estado"] != estado:
                return False
            return True

        self.tabla.set_predicate(predicado)
        self.tabla.set_filter_text(self.buscador.text())
        visibles = self.tabla.proxy.rowCount()
        total = len(self.tabla.rows())
        self.resumen.setText(f"Mostrando {visibles} de {total} productos.")

    def _al_seleccionar(self, fila):
        hay = fila is not None
        self.boton_editar.setEnabled(hay)
        self.boton_estado.setEnabled(hay)
        self.boton_estado.setText("Activar" if hay and fila["estado"] != 1 else "Desactivar")

    # --- Acciones ---

    def run_action(self, accion):
        if accion == "nuevo":
            self._nuevo()

    def _nuevo(self):
        if ProductoDialog(self).exec():
            self.refresh()

    def _editar(self):
        fila = self.tabla.selected_row()
        if fila is None:
            messages.warning(self, "Selecciona un producto", "Haz clic en un producto de la tabla y luego pulsa Editar.")
            return
        datos = controlador_productos.obtener_producto_por_id(fila["id_producto"])
        if datos is None:
            messages.error(self, "Producto no encontrado", "Este producto ya no existe. Se actualizará la lista.")
            self.refresh()
            return
        if ProductoDialog(self, datos).exec():
            self.refresh(seleccionar_id=fila["id_producto"])

    def _alternar_estado(self):
        fila = self.tabla.selected_row()
        if fila is None:
            return
        datos = controlador_productos.obtener_producto_por_id(fila["id_producto"])
        if datos is None:
            self.refresh()
            return

        if datos["estado"] == 1:
            ok = messages.confirm(
                self, "¿Desactivar producto?",
                f"\"{datos['nombre']}\" dejará de aparecer para nuevas ventas. "
                "Su historial se conserva y puedes activarlo de nuevo cuando quieras.",
                confirmar="Desactivar",
            )
        else:
            ok = messages.confirm(
                self, "¿Activar producto?",
                f"\"{datos['nombre']}\" volverá a estar disponible para vender.",
                confirmar="Activar",
            )
        if not ok:
            return

        exito, mensaje = controlador_productos.alternar_estado_producto(datos["id_producto"], datos["estado"])
        if exito:
            messages.success(self, mensaje)
            self.refresh(seleccionar_id=datos["id_producto"])
        else:
            messages.error(self, "No se pudo cambiar el estado", mensaje)
