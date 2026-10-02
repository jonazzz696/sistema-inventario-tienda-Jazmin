"""Historial de cargos y abonos de un cliente (solo lectura)."""

from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QVBoxLayout

from controllers import controlador_creditos
from helpers.formato import centavos_a_texto
from ui.widgets.common import IconTile, button, label
from ui.widgets.data_table import Column, DataTable


class HistorialCreditoDialog(QDialog):
    def __init__(self, parent, cliente):
        """cliente: fila de obtener_clientes_con_saldo() (dict)."""
        super().__init__(parent)
        self.setWindowTitle("Historial de crédito")
        self.setModal(True)
        self.resize(860, 560)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)

        cabecera = QFrame()
        cabecera.setObjectName("DialogHeader")
        fila = QHBoxLayout(cabecera)
        fila.setContentsMargins(26, 20, 26, 18)
        fila.setSpacing(14)
        fila.addWidget(IconTile("history", "primary", 42, 21))
        textos = QVBoxLayout()
        textos.setSpacing(2)
        titulo = label(cliente["nombre_completo"], "section")
        limite = cliente.get("limite_credito")
        detalle = (f"Saldo pendiente {centavos_a_texto(cliente['saldo'])}"
                   f"   |   Límite {centavos_a_texto(limite) if limite is not None else 'sin límite'}")
        textos.addWidget(titulo)
        textos.addWidget(label(detalle, "caption"))
        fila.addLayout(textos, 1)
        raiz.addWidget(cabecera)

        columnas = [
            Column("fecha", "Fecha", width=170),
            Column("tipo", "Tipo", align="center", width=110,
                   badge=lambda f: ("Cargo", "warning") if f["tipo"] == "cargo" else ("Abono", "success")),
            Column("monto", "Monto", fmt=centavos_a_texto, align="right", width=120),
            Column("saldo_anterior", "Saldo anterior", fmt=centavos_a_texto, align="right", width=140),
            Column("saldo_nuevo", "Saldo nuevo", fmt=centavos_a_texto, align="right", width=130),
            Column("descripcion", "Descripción", stretch=True),
        ]
        tabla = DataTable(columnas, empty_text="Este cliente todavía no tiene movimientos de crédito.")
        tabla.set_rows(controlador_creditos.obtener_historial_cliente(cliente["id_cliente"]))

        cuerpo = QVBoxLayout()
        cuerpo.setContentsMargins(26, 20, 26, 20)
        cuerpo.addWidget(tabla)
        raiz.addLayout(cuerpo, 1)

        pie = QFrame()
        pie.setObjectName("DialogFooter")
        botones = QHBoxLayout(pie)
        botones.setContentsMargins(26, 14, 26, 14)
        botones.addStretch(1)
        cerrar = button("Cerrar", variant="secondary", on_click=self.accept)
        botones.addWidget(cerrar)
        raiz.addWidget(pie)
