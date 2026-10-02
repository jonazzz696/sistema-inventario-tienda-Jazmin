"""
Base para formularios en ventana modal (nuevo/editar producto, cliente...).

Estructura:
    Encabezado (icono + titulo + descripcion)
    Cuerpo (self.form: QGridLayout de 2 columnas)
    Mensaje de error en rojo (oculto hasta que haga falta)
    Pie con [Cancelar] [Guardar]

Las subclases implementan save(); si devuelve True el dialogo se cierra.
Los errores se muestran dentro del mismo formulario, sin ventanas
emergentes encima, y se marca en rojo el campo con problema.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from ui.widgets.common import IconTile, button, label


class FormDialog(QDialog):
    def __init__(self, parent, titulo, descripcion="", icon_name="edit",
                 texto_guardar="Guardar", ancho=640):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setModal(True)
        self.setMinimumWidth(min(ancho, 560))
        self._campos = []

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)

        # --- Encabezado ---
        cabecera = QFrame()
        cabecera.setObjectName("DialogHeader")
        fila = QHBoxLayout(cabecera)
        fila.setContentsMargins(26, 20, 26, 18)
        fila.setSpacing(14)
        fila.addWidget(IconTile(icon_name, "primary", 42, 21), 0, Qt.AlignTop)
        textos = QVBoxLayout()
        textos.setSpacing(2)
        etiqueta = QLabel(titulo)
        etiqueta.setObjectName("DialogTitle")
        textos.addWidget(etiqueta)
        if descripcion:
            textos.addWidget(label(descripcion, "caption", wrap=True))
        fila.addLayout(textos, 1)
        raiz.addWidget(cabecera)

        # --- Cuerpo desplazable (por si la pantalla es baja) ---
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QScrollArea.NoFrame)
        cuerpo = QWidget()
        self.form = QGridLayout(cuerpo)
        self.form.setContentsMargins(26, 22, 26, 8)
        self.form.setHorizontalSpacing(18)
        self.form.setVerticalSpacing(16)
        self.form.setColumnStretch(0, 1)
        self.form.setColumnStretch(1, 1)
        area.setWidget(cuerpo)
        raiz.addWidget(area, 1)

        self.error_label = QLabel()
        self.error_label.setObjectName("ErrorBanner")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        contenedor_error = QVBoxLayout()
        contenedor_error.setContentsMargins(26, 4, 26, 14)
        contenedor_error.addWidget(self.error_label)
        raiz.addLayout(contenedor_error)

        # --- Pie ---
        pie = QFrame()
        pie.setObjectName("DialogFooter")
        botones = QHBoxLayout(pie)
        botones.setContentsMargins(26, 14, 26, 14)
        botones.setSpacing(10)
        self.footer_note = label("", "caption")
        botones.addWidget(self.footer_note, 1)
        self.cancel_button = button("Cancelar", variant="secondary", on_click=self.reject)
        self.save_button = button(texto_guardar, "check", variant="primary", on_click=self._on_save)
        self.save_button.setAutoDefault(False)
        self.cancel_button.setAutoDefault(False)
        botones.addWidget(self.cancel_button)
        botones.addWidget(self.save_button)
        raiz.addWidget(pie)

        # Ctrl+Enter guarda desde cualquier campo.
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self._on_save)
        QShortcut(QKeySequence("Ctrl+Enter"), self, activated=self._on_save)

        self._ancho = ancho

    # --- Construccion ---

    def add_field(self, campo, fila, columna=0, span=1):
        self.form.addWidget(campo, fila, columna, 1, span)
        self._campos.append(campo)
        return campo

    def showEvent(self, evento):
        super().showEvent(evento)
        pantalla = QGuiApplication.primaryScreen()
        if pantalla is not None:
            disponible = pantalla.availableGeometry()
            self.resize(min(self._ancho, disponible.width() - 40),
                        min(self.sizeHint().height(), disponible.height() - 60))

    # --- Errores ---

    def show_error(self, mensaje, campo=None):
        self.error_label.setText(mensaje)
        self.error_label.show()
        for c in self._campos:
            c.set_invalid(False)
        if campo is not None:
            campo.set_invalid(True)
            campo.control.setFocus()

    def clear_error(self):
        self.error_label.hide()
        for c in self._campos:
            c.set_invalid(False)

    # --- Guardar ---

    def _on_save(self):
        self.clear_error()
        if self.save():
            self.accept()

    def save(self):
        """Implementar en la subclase. Devolver True si se guardo."""
        return True
