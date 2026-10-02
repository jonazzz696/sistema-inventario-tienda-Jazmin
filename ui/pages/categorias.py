"""
Pantalla de Categorias.

Usa: controlador_categorias.obtener_lista_categorias() y
     controlador_categorias.registrar_categoria(nombre)
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout

from controllers import controlador_categorias
from ui import theme
from ui.formato_ui import badge_estado
from ui.widgets import messages
from ui.widgets.common import Card, button, label
from ui.widgets.data_table import Column, DataTable
from ui.widgets.forms import FormField, SearchField, text_input
from ui.widgets.page import Page


class CategoriasPage(Page):
    def __init__(self, navigate):
        super().__init__("Categorías", "Agrupa los productos para encontrarlos más rápido.")
        self.navigate = navigate

        # --- Formulario ---
        formulario = Card("Nueva categoría")
        fila = QHBoxLayout()
        fila.setSpacing(12)
        self.entrada_nombre = text_input("Ej. Bebidas, Abarrotes, Limpieza", 80)
        self.entrada_nombre.returnPressed.connect(self._registrar)
        self.campo_nombre = FormField("Nombre", self.entrada_nombre, requerido=True)
        fila.addWidget(self.campo_nombre, 1)
        self.boton_agregar = button("Agregar categoría", "plus", "primary", on_click=self._registrar)
        fila.addWidget(self.boton_agregar, 0, Qt.AlignBottom)
        formulario.body.addLayout(fila)
        self.error = label("", "caption")
        self.error.setStyleSheet(f"color: {theme.DANGER};")
        self.error.hide()
        formulario.body.addWidget(self.error)
        self.content.addWidget(formulario)

        # --- Listado ---
        listado = Card("Categorías registradas")
        self.buscador = SearchField("Buscar categoría")
        self.buscador.textChanged.connect(lambda t: self.tabla.set_filter_text(t))
        listado.add_header_widget(self.buscador)
        self.tabla = DataTable(
            [
                Column("nombre", "Nombre", stretch=True),
                Column("estado", "Estado", align="center", width=130, badge=badge_estado),
            ],
            empty_text="Aún no hay categorías. Escribe un nombre arriba y pulsa \"Agregar categoría\".",
            min_height=320,
        )
        listado.body.addWidget(self.tabla, 1)
        self.content.addWidget(listado, 1)

    def refresh(self):
        self.tabla.set_rows(controlador_categorias.obtener_lista_categorias())
        self.tabla.set_filter_text(self.buscador.text())

    def _registrar(self):
        nombre = self.entrada_nombre.text()
        self.campo_nombre.set_invalid(False)
        self.error.hide()
        if not nombre.strip():
            self.campo_nombre.set_invalid(True)
            self.error.setText("Escribe el nombre de la categoría.")
            self.error.show()
            self.entrada_nombre.setFocus()
            return

        exito, mensaje = controlador_categorias.registrar_categoria(nombre)
        if exito:
            messages.success(self, mensaje)
            self.entrada_nombre.clear()
            self.refresh()
            self.tabla.select_by("nombre", nombre.strip())
        else:
            self.campo_nombre.set_invalid(True)
            self.error.setText(mensaje)
            self.error.show()
