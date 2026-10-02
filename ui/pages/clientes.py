"""
Pantalla de Clientes.

Usa, sin cambios:
  controlador_clientes.obtener_lista_clientes()
  controlador_clientes.obtener_cliente_por_id()
  controlador_clientes.alternar_estado_cliente()
  + ClienteDialog -> registrar_cliente / modificar_cliente
"""

from PySide6.QtWidgets import QHBoxLayout

from controllers import controlador_clientes
from helpers.formato import centavos_a_texto
from ui.dialogs.cliente_dialog import ClienteDialog
from ui.formato_ui import badge_estado
from ui.widgets import messages
from ui.widgets.common import Card, button, label
from ui.widgets.data_table import Column, DataTable
from ui.widgets.forms import SearchField, choice_combo
from ui.widgets.page import Page


def _texto_limite(valor):
    return "Sin límite" if valor is None else centavos_a_texto(valor)


class ClientesPage(Page):
    def __init__(self, navigate):
        super().__init__("Clientes", "Datos de contacto y límite de crédito de cada cliente.")
        self.navigate = navigate
        self.add_action(button("Nuevo cliente", "plus", "primary", on_click=self._nuevo))

        tarjeta = Card(padding=18)
        barra = QHBoxLayout()
        barra.setSpacing(10)
        self.buscador = SearchField("Buscar por nombre, teléfono o DUI")
        self.buscador.textChanged.connect(self._aplicar_filtros)
        barra.addWidget(self.buscador, 2)
        self.filtro_estado = choice_combo([("Activos", 1), ("Inactivos", 0), ("Todos", None)])
        self.filtro_estado.setMinimumWidth(140)
        self.filtro_estado.currentIndexChanged.connect(self._aplicar_filtros)
        barra.addWidget(self.filtro_estado)
        barra.addStretch(1)
        self.boton_editar = button("Editar", "edit", "secondary", on_click=self._editar,
                                   tooltip="Editar el cliente seleccionado (doble clic)")
        self.boton_estado = button("Desactivar", "power", "secondary", on_click=self._alternar_estado)
        barra.addWidget(self.boton_editar)
        barra.addWidget(self.boton_estado)
        tarjeta.body.addLayout(barra)

        self.tabla = DataTable(
            [
                Column("nombre_completo", "Nombre", stretch=True),
                Column("telefono", "Teléfono", width=140),
                Column("dui", "DUI", width=130),
                Column("correo", "Correo", width=200),
                Column("limite_credito", "Límite de crédito", fmt=_texto_limite, align="right", width=160,
                       value=lambda f: float("inf") if f["limite_credito"] is None else f["limite_credito"]),
                Column("estado", "Estado", align="center", width=110, badge=badge_estado),
            ],
            empty_text="Aún no hay clientes. Usa \"Nuevo cliente\" para registrar el primero.",
            empty_filtered_text="Ningún cliente coincide con la búsqueda.",
            min_height=380,
        )
        self.tabla.selection_changed.connect(self._al_seleccionar)
        self.tabla.row_activated.connect(lambda _: self._editar())
        tarjeta.body.addWidget(self.tabla, 1)
        self.resumen = label("", "caption")
        tarjeta.body.addWidget(self.resumen)
        self.content.addWidget(tarjeta, 1)
        self._al_seleccionar(None)

    def refresh(self, seleccionar_id=None):
        self.tabla.set_rows(controlador_clientes.obtener_lista_clientes())
        self._aplicar_filtros()
        if seleccionar_id is not None:
            self.tabla.select_by("id_cliente", seleccionar_id)

    def _aplicar_filtros(self, *_):
        estado = self.filtro_estado.currentData()
        self.tabla.set_predicate(lambda f: estado is None or f["estado"] == estado)
        self.tabla.set_filter_text(self.buscador.text())
        self.resumen.setText(f"Mostrando {self.tabla.proxy.rowCount()} de {len(self.tabla.rows())} clientes.")

    def _al_seleccionar(self, fila):
        hay = fila is not None
        self.boton_editar.setEnabled(hay)
        self.boton_estado.setEnabled(hay)
        self.boton_estado.setText("Activar" if hay and fila["estado"] != 1 else "Desactivar")

    def run_action(self, accion):
        if accion == "nuevo":
            self._nuevo()

    def _nuevo(self):
        if ClienteDialog(self).exec():
            self.refresh()

    def _editar(self):
        fila = self.tabla.selected_row()
        if fila is None:
            messages.warning(self, "Selecciona un cliente", "Haz clic en un cliente de la tabla y luego pulsa Editar.")
            return
        datos = controlador_clientes.obtener_cliente_por_id(fila["id_cliente"])
        if datos is None:
            self.refresh()
            return
        if ClienteDialog(self, datos).exec():
            self.refresh(seleccionar_id=fila["id_cliente"])

    def _alternar_estado(self):
        fila = self.tabla.selected_row()
        if fila is None:
            return
        datos = controlador_clientes.obtener_cliente_por_id(fila["id_cliente"])
        if datos is None:
            self.refresh()
            return

        if datos["estado"] == 1:
            ok = messages.confirm(
                self, "¿Desactivar cliente?",
                f"\"{datos['nombre_completo']}\" no aparecerá al registrar ventas. "
                "Sus ventas y su historial de crédito se conservan.",
                confirmar="Desactivar",
            )
        else:
            ok = messages.confirm(self, "¿Activar cliente?",
                                  f"\"{datos['nombre_completo']}\" volverá a estar disponible en ventas.",
                                  confirmar="Activar")
        if not ok:
            return

        exito, mensaje = controlador_clientes.alternar_estado_cliente(datos["id_cliente"], datos["estado"])
        if exito:
            messages.success(self, mensaje)
            self.refresh(seleccionar_id=datos["id_cliente"])
        else:
            messages.error(self, "No se pudo cambiar el estado", mensaje)
