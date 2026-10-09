"""
Pantalla de Inicio.

Todos los numeros salen de la base de datos a traves de
controllers/controlador_dashboard.py. Las tarjetas son clicables y
llevan a la seccion correspondiente (si el rol puede verla).
"""

from controllers import controlador_dashboard
from helpers import permisos
from helpers.formato import centavos_a_texto
from ui.formato_ui import etiqueta_pago, fecha_corta, plural
from ui.widgets.common import Card, button
from ui.widgets.data_table import Column, DataTable
from ui.widgets.page import Page
from ui.widgets.responsive import ResponsiveGrid
from ui.widgets.stat_card import StatCard


class DashboardPage(Page):
    def __init__(self, navigate):
        super().__init__("Inicio", "Resumen de la tienda al día de hoy.")
        self.navigate = navigate

        # Los accesos a secciones que el rol no puede ver no se muestran.
        puede = permisos.puede_ver
        self._puede_ventas = puede("ventas")

        if puede("productos"):
            self.add_action(button("Nuevo producto", "plus", "secondary" if self._puede_ventas else "primary",
                                   on_click=lambda: navigate("productos", "nuevo")))
        if self._puede_ventas:
            self.add_action(button("Nueva venta", "cart", "primary",
                                   on_click=lambda: navigate("ventas")))

        # --- Indicadores ---
        self.card_productos = StatCard("Productos activos", "box", "primary", clickable=puede("productos"))
        self.card_stock = StatCard("Stock bajo", "alert", "warning", clickable=puede("inventario"))
        self.card_ventas = StatCard("Ventas de hoy", "cart", "success", clickable=self._puede_ventas)
        self.card_credito = StatCard("Crédito pendiente", "wallet", "info", clickable=puede("creditos"))
        self.card_productos.clicked.connect(lambda: navigate("productos"))
        self.card_stock.clicked.connect(lambda: navigate("inventario"))
        self.card_ventas.clicked.connect(lambda: navigate("ventas"))
        self.card_credito.clicked.connect(lambda: navigate("creditos"))

        indicadores = ResponsiveGrid([(1080, 4), (560, 2), (0, 1)])
        for tarjeta in (self.card_productos, self.card_stock, self.card_ventas, self.card_credito):
            indicadores.add(tarjeta)
        self.content.addWidget(indicadores)

        # --- Paneles ---
        panel_stock = Card("Productos por reponer",
                           "Existencia igual o menor a su stock mínimo.")
        if puede("inventario"):
            panel_stock.add_header_widget(button("Ir a inventario", variant="ghost",
                                                 on_click=lambda: navigate("inventario")))
        self.tabla_stock = DataTable(
            [
                Column("nombre", "Producto", stretch=True),
                Column("existencia", "Existencia", align="center", width=110),
                Column("stock_minimo", "Mínimo", align="center", width=90),
            ],
            empty_text="Todo en orden: ningún producto está por debajo de su mínimo.",
            highlight=lambda f: "danger" if f["existencia"] == 0 else "warning",
            min_height=300,
        )
        panel_stock.body.addWidget(self.tabla_stock)

        panel_ventas = Card("Últimas ventas", "Las más recientes primero.")
        if self._puede_ventas:
            panel_ventas.add_header_widget(button("Ir a ventas", variant="ghost",
                                                  on_click=lambda: navigate("ventas")))
        self.tabla_ventas = DataTable(
            [
                Column("numero_venta", "No. venta", width=110),
                Column("fecha", "Fecha", fmt=fecha_corta, width=150),
                Column("tipo_pago", "Pago", align="center", width=110,
                       badge=lambda f: (etiqueta_pago(f["tipo_pago"]),
                                        "info" if f["tipo_pago"] == "credito" else "neutral")),
                Column("total", "Total", fmt=centavos_a_texto, align="right", stretch=True),
            ],
            empty_text="Todavía no hay ventas registradas. Usa \"Nueva venta\" para registrar la primera."
                       if self._puede_ventas else "Todavía no hay ventas registradas.",
            min_height=300,
        )
        panel_ventas.body.addWidget(self.tabla_ventas)

        paneles = ResponsiveGrid([(900, 2), (0, 1)])
        paneles.add(panel_stock)
        paneles.add(panel_ventas)
        self.content.addWidget(paneles, 1)

    def refresh(self):
        datos = controlador_dashboard.obtener_resumen()

        self.card_productos.set_value(datos["productos_activos"], "en el catálogo")

        cantidad_bajo = len(datos["stock_bajo"])
        self.card_stock.set_value(
            cantidad_bajo,
            "Todo en orden" if cantidad_bajo == 0
            else plural(cantidad_bajo, "producto por reponer", "productos por reponer"),
        )

        ventas = datos["ventas_hoy"]
        # Las ventas a credito no se suman hasta que el cliente paga: el total
        # es lo cobrado hoy (ventas al contado + pagos de creditos recibidos hoy).
        # Una sola linea corta; el desglose completo queda en el tooltip.
        # Muestra el mismo saldo de la tarjeta "Crédito pendiente" (todos los creditos sin pagar).
        linea = plural(ventas["cantidad"], "venta", "ventas")
        pendiente_total = datos["credito"]["total"]
        if pendiente_total:
            linea += f", crédito pendiente: {centavos_a_texto(pendiente_total)}"
        self.card_ventas.set_value(centavos_a_texto(ventas["recibido"]), linea)
        self.card_ventas.setToolTip(
            f"Al contado: {centavos_a_texto(ventas['contado'])}\n"
            f"Créditos cobrados hoy: {centavos_a_texto(ventas['cobros'])}\n"
            f"Vendido al crédito hoy: {centavos_a_texto(ventas['credito'])}\n"
            f"Falta cobrar de esas ventas: {centavos_a_texto(ventas['credito_pendiente'])}"
            + ("\nClic para abrir Ventas" if self._puede_ventas else ""))

        credito = datos["credito"]
        self.card_credito.set_value(
            centavos_a_texto(credito["total"]),
            plural(credito["clientes"], "cliente con saldo", "clientes con saldo"),
        )

        self.tabla_stock.set_rows(datos["stock_bajo"])
        self.tabla_ventas.set_rows(datos["ventas_recientes"])
