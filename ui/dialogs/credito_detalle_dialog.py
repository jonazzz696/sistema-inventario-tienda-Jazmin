"""
Detalle de un credito: resumen, productos de la venta, historial de
pagos y acciones (Registrar pago / Generar comprobante).
"""

import os

from PySide6.QtCore import QStandardPaths, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog, QFileDialog, QFrame, QHBoxLayout, QLabel, QProgressBar, QScrollArea,
    QVBoxLayout, QWidget,
)

from controllers import controlador_creditos
from reportes.formato import ETIQUETA_PAGO, dinero, fecha_hora
from ui import theme
from ui.dialogs.pago_dialog import PagoDialog
from ui.icons import icon
from ui.widgets import messages
from ui.widgets.common import Card, IconTile, button, label
from ui.widgets.data_table import Column, DataTable

ESTADOS = {
    "pendiente": ("Pendiente", "danger"),
    "parcial": ("Parcial", "warning"),
    "pagado": ("Pagado", "success"),
}


def etiqueta_estado(estado):
    """QLabel con forma de pastilla, del color del estado."""
    texto, tipo = ESTADOS[estado]
    color, fondo = theme.BADGE_COLORS[tipo]
    etiqueta = QLabel(texto)
    etiqueta.setAlignment(Qt.AlignCenter)
    etiqueta.setStyleSheet(f"background: {fondo}; color: {color}; border-radius: 13px; "
                           f"padding: 4px 14px; font-size: 13px; font-weight: 600;")
    return etiqueta


class CreditoDetalleDialog(QDialog):
    def __init__(self, parent, id_venta):
        super().__init__(parent)
        self.id_venta = id_venta
        self.hubo_cambios = False
        self.credito = None
        self.setWindowTitle("Detalle del crédito")
        self.setModal(True)
        self.resize(900, 720)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)

        # --- Encabezado ---
        cabecera = QFrame()
        cabecera.setObjectName("DialogHeader")
        fila = QHBoxLayout(cabecera)
        fila.setContentsMargins(26, 20, 26, 18)
        fila.setSpacing(14)
        fila.addWidget(IconTile("wallet", "primary", 44, 22), 0, Qt.AlignTop)
        textos = QVBoxLayout()
        textos.setSpacing(2)
        self.titulo = QLabel()
        self.titulo.setObjectName("DialogTitle")
        self.subtitulo = label("", "caption")
        textos.addWidget(self.titulo)
        textos.addWidget(self.subtitulo)
        fila.addLayout(textos, 1)
        self.contenedor_estado = QHBoxLayout()
        fila.addLayout(self.contenedor_estado)
        raiz.addWidget(cabecera)

        # --- Cuerpo desplazable ---
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QScrollArea.NoFrame)
        cuerpo = QWidget()
        self.cuerpo = QVBoxLayout(cuerpo)
        self.cuerpo.setContentsMargins(26, 20, 26, 20)
        self.cuerpo.setSpacing(16)
        area.setWidget(cuerpo)
        raiz.addWidget(area, 1)

        # Cliente
        self.info_cliente = label("", "info", wrap=True)
        self.cuerpo.addWidget(self.info_cliente)

        # Montos
        montos = QHBoxLayout()
        montos.setSpacing(12)
        self.valor_total = self._tile(montos, "Total del crédito")
        self.valor_pagado = self._tile(montos, "Pagado")
        self.valor_saldo = self._tile(montos, "Saldo pendiente", destacado=True)
        self.cuerpo.addLayout(montos)

        self.progreso = QProgressBar()
        self.progreso.setRange(0, 100)
        self.progreso.setTextVisible(False)
        self.progreso.setFixedHeight(10)
        self.texto_progreso = label("", "caption")
        self.cuerpo.addWidget(self.progreso)
        self.cuerpo.addWidget(self.texto_progreso)

        # Historial de pagos
        card_pagos = Card("Historial de pagos", "Cómo se ha pagado la deuda, del primer pago al último.")
        self.tabla_pagos = DataTable(
            [
                Column("fecha", "Fecha", fmt=fecha_hora, width=150),
                Column("monto", "Monto", fmt=dinero, align="right", width=110),
                Column("metodo_pago", "Método", align="center", width=110,
                       fmt=lambda v: ETIQUETA_PAGO.get(v, v or "Otro")),
                Column("saldo_despues", "Saldo después", fmt=dinero, align="right", width=130),
                Column("usuario", "Registró", width=140),
                Column("observacion", "Observación", stretch=True),
            ],
            empty_text="Aún no hay pagos registrados para este crédito.",
            min_height=170,
        )
        card_pagos.body.addWidget(self.tabla_pagos)
        self.cuerpo.addWidget(card_pagos)

        # Productos de la venta
        card_productos = Card("Productos de la venta", "Se descontaron del inventario al hacer la venta.")
        self.tabla_productos = DataTable(
            [
                Column("nombre", "Producto", stretch=True,
                       value=lambda f: f"{f['codigo']} - {f['nombre']}"),
                Column("cantidad", "Cantidad", align="center", width=100),
                Column("precio_unitario", "Precio", fmt=dinero, align="right", width=110),
                Column("subtotal", "Subtotal", fmt=dinero, align="right", width=120),
            ],
            empty_text="Sin productos.",
            min_height=140,
        )
        card_productos.body.addWidget(self.tabla_productos)
        self.cuerpo.addWidget(card_productos)

        # --- Pie ---
        pie = QFrame()
        pie.setObjectName("DialogFooter")
        botones = QHBoxLayout(pie)
        botones.setContentsMargins(26, 14, 26, 14)
        botones.setSpacing(10)
        self.boton_comprobante = button("Generar comprobante", "file", "secondary",
                                        on_click=self._generar_comprobante)
        botones.addWidget(self.boton_comprobante)
        botones.addStretch(1)
        botones.addWidget(button("Cerrar", variant="ghost", on_click=self.accept))
        self.boton_pagar = button("Registrar pago", "dollar", "primary", large=True, on_click=self._registrar_pago)
        botones.addWidget(self.boton_pagar)
        raiz.addWidget(pie)

        self._cargar()

    def _tile(self, fila, titulo, destacado=False):
        caja = QFrame()
        caja.setProperty("card", True)
        if destacado:
            caja.setStyleSheet(f"QFrame[card=\"true\"] {{ background: {theme.PRIMARY_SOFT}; "
                               f"border-color: {theme.PRIMARY_LIGHT}; }}")
        disposicion = QVBoxLayout(caja)
        disposicion.setContentsMargins(16, 12, 16, 12)
        disposicion.setSpacing(2)
        disposicion.addWidget(label(titulo, "statLabel"))
        valor = label("", "statValue")
        disposicion.addWidget(valor)
        fila.addWidget(caja, 1)
        return valor

    def _cargar(self):
        c = controlador_creditos.obtener_credito(self.id_venta)
        if c is None:
            messages.error(self, "Crédito no encontrado", "Este crédito ya no existe o la venta fue anulada.")
            self.reject()
            return
        self.credito = c
        self.titulo.setText(f"Crédito {c['numero_venta']}")
        self.subtitulo.setText(f"Venta del {fecha_hora(c['fecha'])}, atendió {c['vendedor']}")
        while self.contenedor_estado.count():
            item = self.contenedor_estado.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.contenedor_estado.addWidget(etiqueta_estado(c["estado_credito"]), 0, Qt.AlignTop)

        contacto = f"Teléfono: {c['telefono']}" if c.get("telefono") else ""
        self.info_cliente.setText(f"Cliente: {c['nombre_completo']}" + (f"      {contacto}" if contacto else ""))
        self.valor_total.setText(dinero(c["total"]))
        self.valor_pagado.setText(dinero(c["pagado"]))
        self.valor_saldo.setText(dinero(c["saldo"]))
        porcentaje = int(c["pagado"] * 100 / c["total"]) if c["total"] else 100
        self.progreso.setValue(min(100, porcentaje))
        self.texto_progreso.setText(
            f"{porcentaje}% pagado en {c['pagos']} {'pago' if c['pagos'] == 1 else 'pagos'}.")

        self.tabla_pagos.set_rows(c["historial"])
        self.tabla_productos.set_rows(c["productos"])

        if c["estado_credito"] == "pagado":
            self.boton_pagar.setEnabled(False)
            self.boton_pagar.setText("Crédito completado")
            self.boton_pagar.setIcon(icon("check", theme.SUCCESS, 18))
        else:
            self.boton_pagar.setEnabled(True)
            self.boton_pagar.setText("Registrar pago")
            self.boton_pagar.setIcon(icon("dollar", "#ffffff", 18))

    def _registrar_pago(self):
        dialogo = PagoDialog(self, self.credito)
        if dialogo.exec():
            self.hubo_cambios = True
            self._cargar()

    def _generar_comprobante(self):
        c = self.credito
        carpeta = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation) or os.path.expanduser("~")
        from datetime import date
        nombre = f"Credito_{c['numero_venta']}_{date.today().isoformat()}.pdf"
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar comprobante", os.path.join(carpeta, nombre),
                                              "Documento PDF (*.pdf)")
        if not ruta:
            return
        if not ruta.lower().endswith(".pdf"):
            ruta += ".pdf"
        exito, mensaje = controlador_creditos.exportar_comprobante(c, ruta)
        if not exito:
            messages.error(self, "No se pudo guardar el comprobante", mensaje)
            return
        if messages.confirm(self, "Comprobante guardado", f"El archivo se guardó en:\n{ruta}\n\n¿Quieres abrirlo ahora?",
                            confirmar="Abrir PDF", cancelar="Cerrar"):
            QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))
