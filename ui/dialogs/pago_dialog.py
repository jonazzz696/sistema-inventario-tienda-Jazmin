"""
Formulario "Registrar pago" de un credito.

Llama a controlador_creditos.registrar_pago(), que valida el monto y
guarda el pago en una transaccion. Este formulario solo agrega ayudas:
boton para pagar el saldo completo y una vista previa del resultado.
"""

from datetime import date, datetime

from PySide6.QtCore import QDate, QLocale, Qt
from PySide6.QtWidgets import QDateEdit, QFrame, QGridLayout, QHBoxLayout

from controllers import controlador_creditos
from helpers.formato import texto_a_centavos
from reportes.formato import dinero, fecha_hora
from ui.widgets import messages
from ui.widgets.common import button, label
from ui.widgets.form_dialog import FormDialog
from ui.widgets.forms import FormField, choice_combo, money_text_input, text_input

_ESTADO_TEXTO = {"pendiente": "pendiente", "parcial": "con pago parcial", "pagado": "pagado por completo"}


class PagoDialog(FormDialog):
    def __init__(self, parent, credito):
        """credito: diccionario de controlador_creditos.obtener_credito()."""
        self.credito = credito
        self.resultado = None
        super().__init__(parent, "Registrar pago",
                         f"Crédito {credito['numero_venta']} de {credito['nombre_completo']}",
                         icon_name="dollar", texto_guardar="Registrar pago", ancho=600)
        self._construir()
        self.campo_monto.control.setFocus()

    def _construir(self):
        c = self.credito

        # --- Resumen del credito ---
        resumen = QFrame()
        resumen.setProperty("card", True)
        rejilla = QGridLayout(resumen)
        rejilla.setContentsMargins(16, 14, 16, 14)
        rejilla.setHorizontalSpacing(24)
        rejilla.setVerticalSpacing(8)
        filas = [
            ("Cliente", c["nombre_completo"]),
            ("Fecha de la venta", fecha_hora(c["fecha"])),
            ("Total del crédito", dinero(c["total"])),
            ("Pagado anteriormente", dinero(c["pagado"])),
        ]
        for i, (titulo, valor) in enumerate(filas):
            rejilla.addWidget(label(titulo, "caption"), i // 2 * 2, i % 2)
            etiqueta = label(valor)
            etiqueta.setStyleSheet("font-size: 15px; font-weight: 600;")
            rejilla.addWidget(etiqueta, i // 2 * 2 + 1, i % 2)
        rejilla.addWidget(label("Saldo pendiente", "caption"), 4, 0, 1, 2)
        saldo = label(dinero(c["saldo"]), "bigTotal")
        saldo.setStyleSheet("font-size: 28px;")
        rejilla.addWidget(saldo, 5, 0, 1, 2)
        self.form.addWidget(resumen, 0, 0, 1, 2)

        # --- Monto ---
        self.entrada_monto = money_text_input("0.00")
        fila_monto = QHBoxLayout()
        fila_monto.setSpacing(8)
        self.campo_monto = FormField("Monto del pago", self.entrada_monto, requerido=True,
                                     ayuda=f"Máximo {dinero(c['saldo'])}.")
        fila_monto.addWidget(self.campo_monto, 1)
        self._campos.append(self.campo_monto)
        completo = button("Pagar saldo completo", variant="secondary",
                          on_click=lambda: self.entrada_monto.setText(f"{c['saldo'] / 100:.2f}"))
        fila_monto.addWidget(completo, 0, Qt.AlignVCenter)
        self.form.addLayout(fila_monto, 1, 0, 1, 2)

        # --- Metodo y fecha ---
        self.combo_metodo = choice_combo([("Efectivo", "efectivo"), ("Tarjeta", "tarjeta"), ("Otro", "otro")])
        self.add_field(FormField("Método de pago", self.combo_metodo, requerido=True), 2, 0)

        self.entrada_fecha = QDateEdit()
        self.entrada_fecha.setCalendarPopup(True)
        self.entrada_fecha.setDisplayFormat("dd/MM/yyyy")
        locale = QLocale(QLocale.Language.Spanish, QLocale.Country.ElSalvador)
        self.entrada_fecha.setLocale(locale)
        self.entrada_fecha.calendarWidget().setLocale(locale)
        hoy = date.today()
        venta = datetime.strptime(c["fecha"][:10], "%Y-%m-%d").date()
        self.entrada_fecha.setDateRange(QDate(venta.year, venta.month, venta.day), QDate(hoy.year, hoy.month, hoy.day))
        self.entrada_fecha.setDate(QDate(hoy.year, hoy.month, hoy.day))
        self.campo_fecha = self.add_field(FormField("Fecha del pago", self.entrada_fecha, requerido=True), 2, 1)

        self.entrada_obs = text_input("Opcional, por ejemplo: pagó en tienda", 200)
        self.add_field(FormField("Observación", self.entrada_obs), 3, 0, 2)

        self.vista_previa = label("", "info", wrap=True)
        self.form.addWidget(self.vista_previa, 4, 0, 1, 2)
        self.entrada_monto.textChanged.connect(self._actualizar_vista_previa)
        self._actualizar_vista_previa()

        self.footer_note.setText("No se crea otra venta ni se modifica el inventario.")

    def _actualizar_vista_previa(self, *_):
        c = self.credito
        texto = self.entrada_monto.text().strip()
        try:
            monto = texto_a_centavos(texto) if texto and texto != "." else 0
        except ValueError:
            monto = 0
        if monto <= 0:
            self.vista_previa.setText("Escribe el monto para ver cómo queda el crédito.")
            return
        if monto > c["saldo"]:
            self.vista_previa.setText(f"El monto supera el saldo pendiente de {dinero(c['saldo'])}.")
            return
        pagado = c["pagado"] + monto
        estado = "pagado" if pagado >= c["total"] else "parcial"
        self.vista_previa.setText(
            f"Después de este pago: pagado {dinero(pagado)} de {dinero(c['total'])}, "
            f"saldo {dinero(c['total'] - pagado)}. El crédito quedará {_ESTADO_TEXTO[estado]}.")

    def save(self):
        exito, mensaje, resultado = controlador_creditos.registrar_pago(
            self.credito["id_venta"],
            self.entrada_monto.text(),
            self.combo_metodo.currentData(),
            self.entrada_fecha.date().toPython(),
            self.entrada_obs.text(),
        )
        if not exito:
            campo = self.campo_fecha if "fecha" in mensaje.lower() else self.campo_monto
            self.show_error(mensaje, campo)
            return False
        self.resultado = resultado
        messages.success(self.parentWidget(), mensaje)
        return True
