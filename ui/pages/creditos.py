"""
Pantalla de Creditos (cuentas por cobrar).

- Dashboard con creditos activos, total por cobrar, cobros del mes y estados.
- Listado de creditos (uno por venta a credito) con total, pagado, saldo y estado.
- Detalle del credito con historial de pagos, "Registrar pago" y comprobante PDF.
- Saldo por cliente (vista que ya existia) con su historial de cargos y abonos.

Los estados se calculan desde los pagos: el usuario nunca los cambia a mano.
"""

from PySide6.QtWidgets import QHBoxLayout

from controllers import controlador_creditos
from reportes.formato import dinero, entero, plural
from ui.dialogs.credito_detalle_dialog import ESTADOS, CreditoDetalleDialog
from ui.dialogs.historial_credito_dialog import HistorialCreditoDialog
from ui.dialogs.pago_dialog import PagoDialog
from ui.formato_ui import fecha_corta
from ui.widgets import messages
from ui.widgets.common import Card, button, label
from ui.widgets.data_table import Column, DataTable
from ui.widgets.forms import SearchField, choice_combo
from ui.widgets.page import Page
from ui.widgets.responsive import ResponsiveGrid
from ui.widgets.stat_card import StatCard

_ORDEN_ESTADO = {"pendiente": 0, "parcial": 1, "pagados": 2}


class CreditosPage(Page):
    def __init__(self, navigate):
        super().__init__("Créditos", "Ventas al crédito, pagos de los clientes y saldos por cobrar.")
        self.navigate = navigate

        self.boton_detalle = self.add_action(
            button("Ver detalle", "eye", "secondary", on_click=self._ver_detalle,
                   tooltip="Historial de pagos y comprobante (doble clic en la fila)"))
        self.boton_pago = self.add_action(
            button("Registrar pago", "dollar", "primary", large=True, on_click=self._registrar_pago))

        # --- Dashboard ---
        self.card_activos = StatCard("Créditos activos", "wallet", "primary", clickable=True)
        self.card_por_cobrar = StatCard("Total por cobrar", "dollar", "info")
        self.card_cobrado = StatCard("Cobrado este mes", "receipt", "success")
        self.card_pendientes = StatCard("Pendientes", "alert", "danger", clickable=True)
        self.card_parciales = StatCard("Parciales", "history", "warning", clickable=True)
        self.card_pagados = StatCard("Pagados", "check", "success", clickable=True)
        for tarjeta, filtro in ((self.card_activos, "activos"), (self.card_pendientes, "pendiente"),
                                (self.card_parciales, "parcial"), (self.card_pagados, "pagado")):
            tarjeta.clicked.connect(lambda f=filtro: self._filtrar_por(f))
        tablero = ResponsiveGrid([(1000, 3), (560, 2), (0, 1)])
        for tarjeta in (self.card_activos, self.card_por_cobrar, self.card_cobrado,
                        self.card_pendientes, self.card_parciales, self.card_pagados):
            tablero.add(tarjeta)
        self.content.addWidget(tablero)

        # --- Listado de creditos ---
        tarjeta = Card("Créditos por venta", "Doble clic en un crédito para ver sus pagos o registrar uno nuevo.")
        barra = QHBoxLayout()
        barra.setSpacing(10)
        self.buscador = SearchField("Buscar por cliente o número de venta")
        self.buscador.textChanged.connect(self._aplicar_filtros)
        barra.addWidget(self.buscador, 2)
        self.filtro_estado = choice_combo([
            ("Activos (pendientes y parciales)", "activos"), ("Pendientes", "pendiente"),
            ("Parciales", "parcial"), ("Pagados", "pagado"), ("Todos", None)])
        self.filtro_estado.setMinimumWidth(260)
        self.filtro_estado.currentIndexChanged.connect(self._aplicar_filtros)
        barra.addWidget(self.filtro_estado)
        barra.addStretch(1)
        tarjeta.body.addLayout(barra)

        self.tabla = DataTable(
            [
                Column("numero_venta", "Crédito", width=120),
                Column("fecha", "Fecha", fmt=fecha_corta, width=150),
                Column("nombre_completo", "Cliente", stretch=True),
                Column("total", "Total", fmt=dinero, align="right", width=120),
                Column("pagado", "Pagado", fmt=dinero, align="right", width=120),
                Column("saldo", "Saldo", fmt=dinero, align="right", width=120),
                Column("estado_credito", "Estado", align="center", width=130,
                       value=lambda f: _ORDEN_ESTADO[f["estado_credito"]],
                       badge=lambda f: ESTADOS[f["estado_credito"]]),
                Column("ultimo_pago", "Último pago", fmt=lambda v: fecha_corta(v) if v else "Sin pagos", width=150),
            ],
            empty_text="Todavía no hay ventas al crédito. Se crean desde Ventas eligiendo el método Crédito.",
            empty_filtered_text="No hay créditos con esos filtros.",
            min_height=360,
        )
        self.tabla.selection_changed.connect(self._al_seleccionar)
        self.tabla.row_activated.connect(lambda _: self._ver_detalle())
        tarjeta.body.addWidget(self.tabla, 1)
        self.resumen_lista = label("", "caption")
        tarjeta.body.addWidget(self.resumen_lista)
        self.content.addWidget(tarjeta, 1)

        # --- Saldo por cliente (vista anterior, se conserva) ---
        tarjeta_clientes = Card("Saldo por cliente",
                                "Suma de todos los créditos de cada cliente activo (cargos menos pagos).")
        self.boton_historial = button("Ver movimientos", "history", "secondary", on_click=self._ver_historial_cliente)
        self.boton_historial.setEnabled(False)
        tarjeta_clientes.add_header_widget(self.boton_historial)
        self.tabla_clientes = DataTable(
            [
                Column("nombre_completo", "Cliente", stretch=True),
                Column("telefono", "Teléfono", width=140),
                Column("limite_credito", "Límite de crédito", align="right", width=160,
                       fmt=lambda v: "Sin límite" if v is None else dinero(v),
                       value=lambda f: float("inf") if f["limite_credito"] is None else f["limite_credito"]),
                Column("saldo", "Saldo pendiente", fmt=dinero, align="right", width=160),
                Column("situacion", "Situación", align="center", width=130,
                       value=lambda f: f["saldo"] > 0,
                       badge=lambda f: ("Con saldo", "warning") if f["saldo"] > 0 else ("Al día", "success")),
            ],
            empty_text="No hay clientes activos.",
            min_height=220,
        )
        self.tabla_clientes.selection_changed.connect(lambda f: self.boton_historial.setEnabled(f is not None))
        self.tabla_clientes.row_activated.connect(lambda _: self._ver_historial_cliente())
        tarjeta_clientes.body.addWidget(self.tabla_clientes)
        self.content.addWidget(tarjeta_clientes)

        self._al_seleccionar(None)

    # ------------------------------------------------------------------
    # Datos
    # ------------------------------------------------------------------

    def refresh(self, seleccionar_id=None):
        creditos = controlador_creditos.obtener_creditos()
        r = controlador_creditos.resumen_creditos(creditos)

        self.card_activos.set_value(entero(r["activos"]), "pendientes y parciales")
        mayor = r["cliente_mayor"]
        self.card_por_cobrar.set_value(
            dinero(r["por_cobrar"]),
            f"Mayor saldo: {mayor[0]} ({dinero(mayor[1])})" if mayor else "Nadie tiene saldo pendiente")
        self.card_cobrado.set_value(dinero(r["cobrado_mes"]),
                                    f"{plural(r['pagos_mes'], 'pago', 'pagos')} en {r['mes'].lower()}")
        self.card_pendientes.set_value(entero(r["pendientes"]), "sin ningún pago")
        self.card_parciales.set_value(entero(r["parciales"]), "con pagos, aún con saldo")
        self.card_pagados.set_value(entero(r["pagados"]), f"total cobrado: {dinero(r['total_cobrado'])}")

        self.tabla.set_rows(creditos)
        self._aplicar_filtros()
        if seleccionar_id is not None:
            self.tabla.select_by("id_venta", seleccionar_id)

        self.tabla_clientes.set_rows(controlador_creditos.obtener_clientes_con_saldo())

    def _filtrar_por(self, filtro):
        self.filtro_estado.setCurrentIndex(max(0, self.filtro_estado.findData(filtro)))

    def _aplicar_filtros(self, *_):
        filtro = self.filtro_estado.currentData()

        def predicado(fila):
            if filtro is None:
                return True
            if filtro == "activos":
                return fila["estado_credito"] != "pagado"
            return fila["estado_credito"] == filtro

        self.tabla.set_predicate(predicado)
        self.tabla.set_filter_text(self.buscador.text())
        self.resumen_lista.setText(
            f"Mostrando {self.tabla.proxy.rowCount()} de {plural(len(self.tabla.rows()), 'crédito', 'créditos')}.")

    def _al_seleccionar(self, fila):
        self.boton_detalle.setEnabled(fila is not None)
        puede_pagar = fila is not None and fila["estado_credito"] != "pagado"
        self.boton_pago.setEnabled(puede_pagar)
        self.boton_pago.setToolTip("Este crédito ya está pagado por completo." if fila is not None and not puede_pagar
                                   else "Registrar un pago del crédito seleccionado")

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    def _ver_detalle(self):
        fila = self.tabla.selected_row()
        if fila is None:
            messages.warning(self, "Selecciona un crédito", "Haz clic en un crédito de la tabla para ver su detalle.")
            return
        dialogo = CreditoDetalleDialog(self, fila["id_venta"])
        dialogo.exec()
        if dialogo.hubo_cambios:
            self.refresh(seleccionar_id=fila["id_venta"])

    def _registrar_pago(self):
        fila = self.tabla.selected_row()
        if fila is None:
            messages.warning(self, "Selecciona un crédito", "Haz clic en el crédito que el cliente va a pagar.")
            return
        credito = controlador_creditos.obtener_credito(fila["id_venta"])
        if credito is None:
            self.refresh()
            return
        if credito["estado_credito"] == "pagado":
            messages.info(self, "Crédito completado", "Este crédito ya está pagado por completo.")
            return
        if PagoDialog(self, credito).exec():
            self.refresh(seleccionar_id=fila["id_venta"])

    def _ver_historial_cliente(self):
        fila = self.tabla_clientes.selected_row()
        if fila is None:
            return
        HistorialCreditoDialog(self, fila).exec()
