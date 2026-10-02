"""
Mensajes del sistema.

- confirm(...)  pregunta antes de una accion importante.
- error / warning / info(...)  avisos que requieren leerse.
- success(...)  aviso flotante breve (no interrumpe) para confirmar
  que algo se guardo. Si la ventana no tiene zona de avisos, se usa
  un dialogo normal.
"""

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget,
)

from ui.icons import pixmap
from ui.widgets.common import IconTile, button

_TIPOS = {
    "error": ("x", "danger"),
    "warning": ("alert", "warning"),
    "info": ("info", "info"),
    "success": ("check", "success"),
    "question": ("info", "primary"),
    "danger": ("trash", "danger"),
}


class MessageDialog(QDialog):
    def __init__(self, parent, kind, titulo, texto, confirmar=None, cancelar=None,
                 variante_confirmar="primary"):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setModal(True)
        self.setMinimumWidth(440)
        self.setMaximumWidth(560)

        nombre_icono, tipo = _TIPOS.get(kind, _TIPOS["info"])

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)

        cuerpo = QHBoxLayout()
        cuerpo.setContentsMargins(26, 26, 26, 22)
        cuerpo.setSpacing(18)
        cuerpo.addWidget(IconTile(nombre_icono, tipo, 44, 22), 0, Qt.AlignTop)

        textos = QVBoxLayout()
        textos.setSpacing(6)
        etiqueta_titulo = QLabel(titulo)
        etiqueta_titulo.setObjectName("MessageTitle")
        etiqueta_titulo.setWordWrap(True)
        etiqueta_texto = QLabel(texto)
        etiqueta_texto.setObjectName("MessageText")
        etiqueta_texto.setWordWrap(True)
        etiqueta_texto.setTextInteractionFlags(Qt.TextSelectableByMouse)
        textos.addWidget(etiqueta_titulo)
        textos.addWidget(etiqueta_texto)
        cuerpo.addLayout(textos, 1)
        raiz.addLayout(cuerpo)

        pie = QFrame()
        pie.setObjectName("DialogFooter")
        botones = QHBoxLayout(pie)
        botones.setContentsMargins(22, 14, 22, 14)
        botones.setSpacing(10)
        botones.addStretch(1)
        if cancelar:
            boton_cancelar = button(cancelar, variant="secondary", on_click=self.reject)
            botones.addWidget(boton_cancelar)
        boton_ok = button(confirmar or "Entendido", variant=variante_confirmar, on_click=self.accept)
        boton_ok.setDefault(True)
        boton_ok.setAutoDefault(True)
        botones.addWidget(boton_ok)
        raiz.addWidget(pie)

        # En confirmaciones peligrosas, el foco inicial va a Cancelar.
        if cancelar and variante_confirmar == "danger":
            boton_cancelar.setFocus()
        else:
            boton_ok.setFocus()


def confirm(parent, titulo, texto, confirmar="Confirmar", cancelar="Cancelar", danger=False):
    dialogo = MessageDialog(
        parent, "danger" if danger else "question", titulo, texto,
        confirmar=confirmar, cancelar=cancelar,
        variante_confirmar="danger" if danger else "primary",
    )
    return dialogo.exec() == QDialog.Accepted


def error(parent, titulo, texto):
    MessageDialog(parent, "error", titulo, texto).exec()


def warning(parent, titulo, texto):
    MessageDialog(parent, "warning", titulo, texto).exec()


def info(parent, titulo, texto):
    MessageDialog(parent, "info", titulo, texto).exec()


def success(widget, texto):
    """Muestra un aviso flotante en la ventana principal."""
    ventana = widget.window() if widget is not None else None
    # Si el widget esta dentro de un dialogo que ya se cerro, subimos al padre.
    while ventana is not None and not hasattr(ventana, "show_toast") and ventana.parentWidget():
        ventana = ventana.parentWidget().window()
    if ventana is not None and hasattr(ventana, "show_toast"):
        ventana.show_toast(texto)
    else:
        MessageDialog(widget, "success", "Listo", texto).exec()


class Toast(QFrame):
    """Aviso flotante en la esquina inferior derecha que se oculta solo."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        disposicion = QHBoxLayout(self)
        disposicion.setContentsMargins(16, 12, 20, 12)
        disposicion.setSpacing(12)
        self._icono = QLabel()
        self._icono.setPixmap(pixmap("check", "#7FD3A3", 20))
        self._texto = QLabel()
        self._texto.setWordWrap(True)
        self._texto.setMaximumWidth(420)
        disposicion.addWidget(self._icono, 0, Qt.AlignTop)
        disposicion.addWidget(self._texto, 1)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)
        self.hide()

    def show_message(self, texto, ms=3500):
        self._texto.setText(texto)
        self.adjustSize()
        self.reposition()
        self.show()
        self.raise_()
        self._timer.start(ms)

    def reposition(self):
        padre = self.parentWidget()
        if padre is None:
            return
        margen = 24
        self.move(padre.width() - self.width() - margen, padre.height() - self.height() - margen)
