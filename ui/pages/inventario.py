"""
Pantalla de Inventario (entradas y salidas manuales).

Usa, sin cambios:
  controlador_inventario.registrar_movimiento_manual(id, tipo, cantidad_texto, motivo)
  controlador_inventario.obtener_historial(id_producto=None)
  controlador_inventario.obtener_productos_stock_bajo()
  controlador_productos.obtener_lista_productos()

El filtro por producto del historial usa el parametro id_producto que
obtener_historial() ya tenia, aunque la pantalla anterior no lo usaba.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QButtonGroup, QGridLayout, QHBoxLayout, QVBoxLayout

from controllers import controlador_inventario, controlador_productos
from ui.formato_ui import fecha_corta
from ui.widgets import messages
from ui.widgets.common import Card, button, label
from ui.widgets.data_table import Column, DataTable
from ui.widgets.forms import (
    FormField, SearchField, SearchableCombo, choice_combo, int_input, text_input,
)
from ui.widgets.page import Page
from ui.icons import icon
from ui import theme


class InventarioPage(Page):
    def __init__(self, navigate):
        super().__init__(
            "Inventario",
            "Registra entradas y salidas de mercadería. Cada cambio queda en el historial.",
        )
        self.navigate = navigate
        self._productos = {}

        self.content.addWidget(self._crear_formulario())

        # --- Stock bajo ---
        tarjeta_bajo = Card("Productos con stock bajo", "Existencia igual o menor a su stock mínimo.")
        self.tabla_bajo = DataTable(
            [
                Column("codigo", "Código", width=120),
                Column("nombre", "Producto", stretch=True),
                Column("existencia", "Existencia", align="center", width=120),
                Column("stock_minimo", "Stock mínimo", align="center", width=130),
            ],
            empty_text="No hay productos con stock bajo por ahora.",
            highlight=lambda f: "danger" if f["existencia"] == 0 else "warning",
            min_height=190,
        )
        self.tabla_bajo.row_activated.connect(self._preparar_entrada)
        tarjeta_bajo.body.addWidget(self.tabla_bajo)
        tarjeta_bajo.body.addWidget(label("Doble clic en un producto para registrar una entrada.", "caption"))
        self.content.addWidget(tarjeta_bajo)

        # --- Historial ---
        tarjeta_historial = Card("Historial de movimientos", "Los más recientes primero (últimos 100).")
        filtros = QHBoxLayout()
        filtros.setSpacing(10)
        self.buscador = SearchField("Buscar en el historial")
        self.buscador.textChanged.connect(self._aplicar_filtros)
        filtros.addWidget(self.buscador, 2)
        self.filtro_producto = SearchableCombo("Todos los productos")
        self.filtro_producto.setMinimumWidth(260)
        self.filtro_producto.currentIndexChanged.connect(self._recargar_historial)
        self.filtro_producto.lineEdit().textChanged.connect(self._al_escribir_filtro_producto)
        filtros.addWidget(self.filtro_producto, 2)
        self.filtro_tipo = choice_combo([("Entradas y salidas", None), ("Solo entradas", "entrada"),
                                         ("Solo salidas", "salida")])
        self.filtro_tipo.currentIndexChanged.connect(self._aplicar_filtros)
        filtros.addWidget(self.filtro_tipo, 1)
        tarjeta_historial.body.addLayout(filtros)

        self.tabla_historial = DataTable(
            [
                Column("fecha", "Fecha", fmt=fecha_corta, width=150),
                Column("producto", "Producto", width=260,
                       value=lambda f: f"{f['codigo']} - {f['nombre_producto']}"),
                Column("tipo", "Tipo", align="center", width=110,
                       badge=lambda f: ("Entrada", "success") if f["tipo"] == "entrada" else ("Salida", "info")),
                Column("cantidad", "Cantidad", align="center", width=100),
                Column("existencia_nueva", "Existencia resultante", align="center", width=170),
                Column("descripcion", "Motivo", stretch=True),
            ],
            empty_text="Todavía no hay movimientos registrados.",
            empty_filtered_text="No hay movimientos con esos filtros.",
            min_height=320,
        )
        tarjeta_historial.body.addWidget(self.tabla_historial, 1)
        self.content.addWidget(tarjeta_historial, 1)

    # --- Formulario ---

    def _crear_formulario(self):
        tarjeta = Card("Registrar movimiento")
        rejilla = QGridLayout()
        rejilla.setHorizontalSpacing(16)
        rejilla.setVerticalSpacing(14)
        rejilla.setColumnStretch(0, 3)
        rejilla.setColumnStretch(1, 2)

        self.combo_producto = SearchableCombo("Escribe el código o nombre del producto")
        self.combo_producto.currentIndexChanged.connect(self._mostrar_existencia)
        self.combo_producto.lineEdit().textChanged.connect(self._mostrar_existencia)
        self.campo_producto = FormField("Producto", self.combo_producto, requerido=True)
        rejilla.addWidget(self.campo_producto, 0, 0)

        # Selector Entrada / Salida
        contenedor_tipo = QVBoxLayout()
        contenedor_tipo.setSpacing(6)
        contenedor_tipo.addWidget(label("Tipo de movimiento", "fieldLabel"))
        fila_tipo = QHBoxLayout()
        fila_tipo.setSpacing(8)
        self.grupo_tipo = QButtonGroup(self)
        self.boton_entrada = button("Entrada", variant="secondary")
        self.boton_salida = button("Salida", variant="secondary")
        for boton, tipo, nombre_icono in ((self.boton_entrada, "entrada", "arrow-in"),
                                          (self.boton_salida, "salida", "arrow-out")):
            boton.setCheckable(True)
            boton.setProperty("segment", True)
            boton.setProperty("tipo", tipo)
            boton.setIcon(icon(nombre_icono, theme.TEXT_MUTED, 18, checked_color=theme.PRIMARY))
            self.grupo_tipo.addButton(boton)
            fila_tipo.addWidget(boton, 1)
        self.boton_entrada.setChecked(True)
        self.grupo_tipo.buttonToggled.connect(self._al_cambiar_tipo)
        contenedor_tipo.addLayout(fila_tipo)
        rejilla.addLayout(contenedor_tipo, 0, 1)

        self.info_existencia = label("Elige un producto para ver su existencia actual.", "info", wrap=True)
        rejilla.addWidget(self.info_existencia, 1, 0, 1, 2)

        self.entrada_cantidad = int_input(1, 1_000_000)
        self.entrada_cantidad.setValue(1)
        self.campo_cantidad = FormField("Cantidad", self.entrada_cantidad, requerido=True)
        self.entrada_motivo = text_input("Ej. Compra a proveedor, producto dañado, ajuste", 200)
        self.entrada_motivo.returnPressed.connect(self._registrar)
        self.campo_motivo = FormField("Motivo (opcional)", self.entrada_motivo)

        fila_final = QHBoxLayout()
        fila_final.setSpacing(16)
        fila_final.addWidget(self.campo_cantidad, 1)
        fila_final.addWidget(self.campo_motivo, 3)
        self.boton_registrar = button("Registrar entrada", "check", "primary", large=True,
                                      on_click=self._registrar)
        fila_final.addWidget(self.boton_registrar, 0, Qt.AlignBottom)
        rejilla.addLayout(fila_final, 2, 0, 1, 2)

        tarjeta.body.addLayout(rejilla)
        return tarjeta

    def _tipo(self):
        boton = self.grupo_tipo.checkedButton()
        return boton.property("tipo") if boton else "entrada"

    def _al_cambiar_tipo(self, *_):
        self.boton_registrar.setText("Registrar entrada" if self._tipo() == "entrada" else "Registrar salida")

    def _mostrar_existencia(self, *_):
        id_producto = self.combo_producto.current_data()
        p = self._productos.get(id_producto)
        if p is None:
            self.info_existencia.setText("Elige un producto para ver su existencia actual.")
            return
        estado = "" if p["estado"] == 1 else "   (producto inactivo)"
        self.info_existencia.setText(
            f"Existencia actual: {p['existencia']} {p['unidad_medida']}"
            f"      Stock mínimo: {p['stock_minimo']}{estado}"
        )

    def _preparar_entrada(self, fila):
        self.combo_producto.select_data(fila["id_producto"])
        self.boton_entrada.setChecked(True)
        self.entrada_cantidad.setFocus()
        self.entrada_cantidad.selectAll()
        self.scroll.verticalScrollBar().setValue(0)

    def _registrar(self):
        self.campo_producto.set_invalid(False)
        id_producto = self.combo_producto.current_data()
        if id_producto is None:
            self.campo_producto.set_invalid(True)
            messages.warning(self, "Falta el producto", "Elige un producto de la lista para registrar el movimiento.")
            self.combo_producto.setFocus()
            return

        tipo = self._tipo()
        cantidad = self.entrada_cantidad.value()
        exito, mensaje = controlador_inventario.registrar_movimiento_manual(
            id_producto, tipo, str(cantidad), self.entrada_motivo.text()
        )
        if exito:
            messages.success(self, mensaje)
            self.entrada_cantidad.setValue(1)
            self.entrada_motivo.clear()
            self.refresh()
            self.combo_producto.select_data(id_producto)
        else:
            messages.error(self, "No se pudo registrar el movimiento", mensaje)

    # --- Datos ---

    def refresh(self):
        productos = controlador_productos.obtener_lista_productos()
        self._productos = {p["id_producto"]: dict(p) for p in productos}
        pares = [(f"{p['codigo']} - {p['nombre']}", p["id_producto"]) for p in productos]
        self.combo_producto.set_items(pares)
        self._mostrar_existencia()

        filtro = self.filtro_producto.current_data()
        self.filtro_producto.blockSignals(True)
        self.filtro_producto.set_items(pares, mantener_seleccion=False)
        if filtro is not None:
            self.filtro_producto.select_data(filtro)
        self.filtro_producto.blockSignals(False)

        self.tabla_bajo.set_rows(controlador_inventario.obtener_productos_stock_bajo())
        self._recargar_historial()

    def _al_escribir_filtro_producto(self, texto):
        # Al borrar el texto se vuelve a "Todos los productos".
        if not texto.strip():
            self._recargar_historial()

    def _recargar_historial(self, *_):
        id_producto = self.filtro_producto.current_data()
        self.tabla_historial.set_rows(controlador_inventario.obtener_historial(id_producto=id_producto))
        self._aplicar_filtros()

    def _aplicar_filtros(self, *_):
        tipo = self.filtro_tipo.currentData()
        self.tabla_historial.set_predicate(lambda f: tipo is None or f["tipo"] == tipo)
        self.tabla_historial.set_filter_text(self.buscador.text())
