"""
Formulario para cambiar contrasenas (solo administrador).

El administrador puede cambiar la suya o la de una cuenta de ventas;
en ambos casos confirma con su contrasena actual. La validacion vive
en controlador_usuarios.cambiar_password.
"""

from PySide6.QtWidgets import QLineEdit

from controllers import controlador_usuarios
from ui.widgets.form_dialog import FormDialog
from ui.widgets.forms import FormField, choice_combo


def _password_input(placeholder):
    campo = QLineEdit()
    campo.setPlaceholderText(placeholder)
    campo.setEchoMode(QLineEdit.Password)
    campo.setMaxLength(128)
    return campo


class PasswordDialog(FormDialog):
    def __init__(self, parent):
        super().__init__(
            parent,
            "Cambiar contraseña",
            "Elige la cuenta y confirma con tu contraseña de administrador.",
            icon_name="lock",
            texto_guardar="Cambiar contraseña",
            ancho=560,
        )
        self.mensaje_exito = ""

        self.campo_cuenta = self.add_field(
            FormField("Cuenta", choice_combo(controlador_usuarios.listar_cuentas_editables()),
                      requerido=True), 0, 0, 2)
        self.campo_actual = self.add_field(
            FormField("Tu contraseña actual", _password_input("Contraseña del administrador"),
                      requerido=True), 1, 0, 2)
        self.campo_nueva = self.add_field(
            FormField("Nueva contraseña", _password_input("Mínimo 6 caracteres"),
                      requerido=True), 2, 0)
        self.campo_confirmacion = self.add_field(
            FormField("Confirmar nueva contraseña", _password_input("Repite la nueva contraseña"),
                      requerido=True), 2, 1)

        self.campo_actual.control.setFocus()

    def save(self):
        exito, mensaje, campo = controlador_usuarios.cambiar_password(
            self.campo_cuenta.control.currentData(),
            self.campo_actual.control.text(),
            self.campo_nueva.control.text(),
            self.campo_confirmacion.control.text(),
        )
        if not exito:
            campos = {"actual": self.campo_actual, "nueva": self.campo_nueva,
                      "confirmacion": self.campo_confirmacion}
            self.show_error(mensaje, campos.get(campo))
            return False

        self.mensaje_exito = mensaje
        return True
