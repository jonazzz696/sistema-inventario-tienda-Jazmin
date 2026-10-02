"""
Formulario para crear o editar un cliente.

Llama a controlador_clientes.registrar_cliente / modificar_cliente
con los mismos parametros de texto que la version anterior.
"""

from controllers import controlador_clientes
from ui.widgets import messages
from ui.widgets.form_dialog import FormDialog
from ui.widgets.forms import FormField, money_text_input, text_input


class ClienteDialog(FormDialog):
    def __init__(self, parent, cliente_existente=None):
        self.cliente = cliente_existente
        self.es_edicion = cliente_existente is not None
        super().__init__(
            parent,
            "Editar cliente" if self.es_edicion else "Nuevo cliente",
            "Solo el nombre y el teléfono son obligatorios.",
            icon_name="edit" if self.es_edicion else "user",
            texto_guardar="Guardar cambios" if self.es_edicion else "Guardar cliente",
            ancho=620,
        )
        self._construir()
        if self.es_edicion:
            self._precargar()
        self.campo_nombre.control.setFocus()

    def _construir(self):
        self.campo_nombre = self.add_field(
            FormField("Nombre completo", text_input("Ej. María López", 120), requerido=True), 0, 0, 2)
        self.campo_telefono = self.add_field(
            FormField("Teléfono", text_input("Ej. 7000-0000", 30), requerido=True), 1, 0)
        self.campo_dui = self.add_field(
            FormField("DUI", text_input("Opcional", 20)), 1, 1)
        self.campo_direccion = self.add_field(
            FormField("Dirección", text_input("Opcional", 200)), 2, 0, 2)
        self.campo_correo = self.add_field(
            FormField("Correo", text_input("Opcional", 120)), 3, 0)
        self.campo_limite = self.add_field(
            FormField("Límite de crédito", money_text_input("Sin límite"),
                      ayuda="Déjalo vacío si el cliente no tiene límite."), 3, 1)
        self.footer_note.setText("* Campos obligatorios")

    def _precargar(self):
        c = self.cliente
        self.campo_nombre.control.setText(c["nombre_completo"])
        self.campo_telefono.control.setText(c["telefono"])
        self.campo_dui.control.setText(c["dui"] or "")
        self.campo_direccion.control.setText(c["direccion"] or "")
        self.campo_correo.control.setText(c["correo"] or "")
        if c["limite_credito"] is not None:
            self.campo_limite.control.setText(f"{c['limite_credito'] / 100:.2f}")

    def save(self):
        nombre = self.campo_nombre.control.text()
        telefono = self.campo_telefono.control.text()
        dui = self.campo_dui.control.text()
        direccion = self.campo_direccion.control.text()
        correo = self.campo_correo.control.text()
        limite = self.campo_limite.control.text()

        if not nombre.strip():
            self.show_error("Escribe el nombre del cliente.", self.campo_nombre)
            return False
        if not telefono.strip():
            self.show_error("Escribe el teléfono del cliente.", self.campo_telefono)
            return False
        if limite.strip() in (".",):
            self.show_error("El límite de crédito no es un número válido.", self.campo_limite)
            return False

        if self.es_edicion:
            exito, mensaje = controlador_clientes.modificar_cliente(
                self.cliente["id_cliente"], nombre, telefono, dui, direccion, correo, limite)
        else:
            exito, mensaje = controlador_clientes.registrar_cliente(
                nombre, telefono, dui, direccion, correo, limite)

        if not exito:
            texto = mensaje.lower()
            campo = (self.campo_telefono if "telefono" in texto else
                     self.campo_nombre if "nombre" in texto else
                     self.campo_limite if "numero" in texto or "precio" in texto else None)
            self.show_error(mensaje, campo)
            return False

        messages.success(self.parentWidget(), mensaje)
        return True
