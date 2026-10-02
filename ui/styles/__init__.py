"""
Carga del tema visual.

1. Elige la primera fuente disponible de theme.FONT_FAMILIES.
2. Genera en una carpeta temporal los PNG que el QSS necesita
   (flechas de listas desplegables, check de casillas).
3. Lee theme.qss, reemplaza los marcadores {{NOMBRE}} y lo aplica
   a toda la aplicacion.
"""

import os
import tempfile

from PySide6.QtGui import QFont, QFontDatabase

from ui import theme

_CARPETA = os.path.dirname(os.path.abspath(__file__))
_RUTA_QSS = os.path.join(_CARPETA, "theme.qss")


def _elegir_fuente():
    disponibles = set(QFontDatabase.families())
    for familia in theme.FONT_FAMILIES:
        if familia in disponibles:
            return familia
    return QFont().defaultFamily()


def _generar_iconos_qss():
    from ui.icons import save_png

    carpeta = os.path.join(tempfile.gettempdir(), "tienda_jazmin_ui")
    os.makedirs(carpeta, exist_ok=True)

    iconos = {
        "ICON_CHEVRON_DOWN": ("chevron-down", theme.TEXT_MUTED, 16),
        "ICON_CHEVRON_UP": ("chevron-up", theme.TEXT_MUTED, 16),
        "ICON_CHECK_WHITE": ("check", "#ffffff", 16),
    }
    rutas = {}
    for clave, (nombre, color, tam) in iconos.items():
        ruta = os.path.join(carpeta, f"{nombre}-{color.strip('#')}.png")
        save_png(nombre, color, tam, ruta)
        # Qt acepta barras normales tambien en Windows.
        rutas[clave] = ruta.replace("\\", "/")
    return rutas


def aplicar_tema(app):
    fuente = QFont(_elegir_fuente())
    fuente.setPixelSize(theme.FONT_BODY)
    fuente.setHintingPreference(QFont.PreferNoHinting)
    app.setFont(fuente)

    with open(_RUTA_QSS, "r", encoding="utf-8") as archivo:
        qss = archivo.read()

    valores = {k: str(v) for k, v in theme.tokens().items()}
    valores.update(_generar_iconos_qss())

    for clave, valor in valores.items():
        qss = qss.replace("{{" + clave + "}}", valor)

    app.setStyleSheet(qss)
