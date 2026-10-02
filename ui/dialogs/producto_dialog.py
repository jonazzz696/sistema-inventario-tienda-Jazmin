"""
Formulario para crear o editar un producto.

Usa exactamente las mismas funciones del controlador que la version
Tkinter (registrar_producto / modificar_producto), con los mismos
parametros en texto. Solo se agregan comprobaciones previas para dar
mensajes mas claros; las validaciones del modelo siguen activas.
"""

from PySide6.QtWidgets import QComboBox

from controllers import controlador_categorias, controlador_productos
from ui.widgets import messages
from ui.widgets.common import label
from ui.widgets.form_dialog import FormDialog
from ui.widgets.forms import (
    FormField, SearchableCombo, int_input, money_input, text_input,
)

UNIDADES_SUGERIDAS = ["unidad", "caja", "paquete", "docena", "libra", "kilogramo", "litro", "galón", "metro"]


class ProductoDialog(FormDialog):
    def __init__(self, parent, producto_existente=None):
        self.producto = producto_existente
        self.es_edicion = producto_existente is not None
        super().__init__(
            parent,
            "Editar producto" if self.es_edicion else "Nuevo producto",
            "Actualiza los datos generales del producto." if self.es_edicion
            else "Completa los datos para agregarlo al catálogo.",
            icon_name="edit" if self.es_edicion else "box",
            texto_guardar="Guardar cambios" if self.es_edicion else "Guardar producto",
        )
        self._construir()
        if self.es_edicion:
            self._precargar()
        self.campo_codigo.control.setFocus()

    def _construir(self):
        self.campo_codigo = self.add_field(
            FormField("Código", text_input("Ej. BEB-001", 40), requerido=True), 0, 0)

        unidad = QComboBox()
        unidad.setEditable(True)
        unidad.addItems(UNIDADES_SUGERIDAS)
        unidad.setCurrentText("unidad")
        self.campo_unidad = self.add_field(
            FormField("Unidad de medida", unidad, requerido=True,
                      ayuda="Elige una o escribe otra."), 0, 1)

        self.campo_nombre = self.add_field(
            FormField("Nombre del producto", text_input("Ej. Agua purificada 600 ml", 120),
                      requerido=True), 1, 0, 2)
        self.campo_descripcion = self.add_field(
            FormField("Descripción", text_input("Opcional", 250)), 2, 0, 2)

        self._categorias = list(controlador_categorias.obtener_lista_categorias())
        combo = SearchableCombo("Elige o busca una categoría")
        combo.set_items([(c["nombre"], c["id_categoria"]) for c in self._categorias],
                        mantener_seleccion=False)
        ayuda = None if self._categorias else "Aún no hay categorías. Créalas en la sección Categorías."
        self.campo_categoria = self.add_field(
            FormField("Categoría", combo, requerido=True, ayuda=ayuda), 3, 0, 2)

        self.campo_precio_compra = self.add_field(
            FormField("Precio de compra", money_input(), requerido=True), 4, 0)
        self.campo_precio_venta = self.add_field(
            FormField("Precio de venta", money_input(), requerido=True), 4, 1)

        if self.es_edicion:
            nota = label(
                f"Existencia actual: {self.producto['existencia']} "
                f"{self.producto['unidad_medida']}. La existencia se cambia desde "
                "Inventario para que quede registrado cada movimiento.",
                "info", wrap=True,
            )
            self.form.addWidget(nota, 5, 0)
            self.campo_existencia = None
        else:
            self.campo_existencia = self.add_field(
                FormField("Existencia inicial", int_input(), requerido=True,
                          ayuda="Cantidad disponible hoy."), 5, 0)

        self.campo_stock_minimo = self.add_field(
            FormField("Stock mínimo", int_input(), requerido=True,
                      ayuda="Avisa cuando la existencia llegue a este número."), 5, 1)

        self.footer_note.setText("* Campos obligatorios")

    def _precargar(self):
        p = self.producto
        self.campo_codigo.control.setText(p["codigo"])
        self.campo_nombre.control.setText(p["nombre"])
        self.campo_descripcion.control.setText(p["descripcion"] or "")
        self.campo_categoria.control.select_data(p["id_categoria"])
        self.campo_precio_compra.control.setValue(p["precio_compra"] / 100)
        self.campo_precio_venta.control.setValue(p["precio_venta"] / 100)
        self.campo_stock_minimo.control.setValue(p["stock_minimo"])
        self.campo_unidad.control.setCurrentText(p["unidad_medida"] or "unidad")

    def save(self):
        codigo = self.campo_codigo.control.text()
        nombre = self.campo_nombre.control.text()
        descripcion = self.campo_descripcion.control.text()
        unidad = self.campo_unidad.control.currentText()
        id_categoria = self.campo_categoria.control.current_data()
        precio_compra = self.campo_precio_compra.control.value()
        precio_venta = self.campo_precio_venta.control.value()
        stock_minimo = self.campo_stock_minimo.control.value()

        # Comprobaciones previas con mensajes claros (el modelo vuelve a validar).
        if not codigo.strip():
            self.show_error("Escribe el código del producto.", self.campo_codigo)
            return False
        if not nombre.strip():
            self.show_error("Escribe el nombre del producto.", self.campo_nombre)
            return False
        if not unidad.strip():
            self.show_error("Escribe la unidad de medida (por ejemplo: unidad).", self.campo_unidad)
            return False
        if id_categoria is None:
            texto = ("Elige una categoría de la lista." if self._categorias
                     else "Primero crea una categoría en la sección Categorías.")
            self.show_error(texto, self.campo_categoria)
            return False
        if precio_venta <= 0:
            self.show_error("El precio de venta debe ser mayor que 0.", self.campo_precio_venta)
            return False

        if self.es_edicion:
            exito, mensaje = controlador_productos.modificar_producto(
                self.producto["id_producto"], codigo, nombre, descripcion, id_categoria,
                f"{precio_compra:.2f}", f"{precio_venta:.2f}", str(stock_minimo), unidad,
            )
        else:
            exito, mensaje = controlador_productos.registrar_producto(
                codigo, nombre, descripcion, id_categoria,
                f"{precio_compra:.2f}", f"{precio_venta:.2f}",
                str(self.campo_existencia.control.value()), str(stock_minimo), unidad,
            )

        if not exito:
            campo = self.campo_codigo if "codigo" in mensaje.lower() else None
            self.show_error(mensaje, campo)
            return False

        messages.success(self.parentWidget(), mensaje)
        return True
