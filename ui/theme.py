"""
Tokens de diseno (colores y tamanos) en un solo lugar.

La hoja de estilos (styles/theme.qss) usa estos mismos valores a
traves de marcadores {{NOMBRE}}, y el codigo Python los usa donde
Qt no permite QSS (dibujo de etiquetas de estado, iconos, etc.).
Si quieres cambiar el color principal del sistema, cambialo aqui.
"""

# Superficies
BACKGROUND = "#F1F4F3"      # fondo general de la aplicacion
SURFACE = "#FFFFFF"         # tarjetas, paneles, tablas
SURFACE_ALT = "#F7F9F8"     # encabezados de tabla, zonas secundarias
BORDER = "#DFE5E3"
BORDER_STRONG = "#C9D2CF"

# Texto
TEXT = "#1B2624"
TEXT_MUTED = "#5E6B68"
TEXT_SUBTLE = "#95A09D"

# Color principal (navegacion y acciones)
PRIMARY = "#12695F"
PRIMARY_HOVER = "#0E594F"
PRIMARY_PRESSED = "#0A4740"
PRIMARY_SOFT = "#E2F0ED"
PRIMARY_LIGHT = "#8FC7BE"    # serie secundaria en graficos (p. ej. ventas vs. dinero recibido)

# Colores de estado (solo para estados, no para decorar)
SUCCESS = "#2B7A4B"
SUCCESS_SOFT = "#E3F2E8"
WARNING = "#A86A12"
WARNING_SOFT = "#FBF0DC"
DANGER = "#BE3A2E"
DANGER_SOFT = "#FBE8E5"
DANGER_HOVER = "#A33026"
INFO = "#2E68AE"
INFO_SOFT = "#E4EDF8"

# Tipografia (px). Qt escala automaticamente en pantallas HiDPI.
FONT_FAMILIES = ["Segoe UI", "Inter", "SF Pro Text", "Roboto", "Noto Sans", "Helvetica Neue", "Arial"]
FONT_BODY = 15
FONT_SMALL = 13
FONT_TABLE = 14

# Filas de tabla
TABLE_ROW_HEIGHT = 46

# Colores por tipo de etiqueta de estado: (texto, fondo)
BADGE_COLORS = {
    "success": (SUCCESS, SUCCESS_SOFT),
    "warning": (WARNING, WARNING_SOFT),
    "danger": (DANGER, DANGER_SOFT),
    "info": (INFO, INFO_SOFT),
    "neutral": (TEXT_MUTED, "#ECEFEE"),
}

# Fondo suave de fila resaltada (stock bajo, cliente con deuda...)
ROW_HIGHLIGHT = {
    "danger": "#FDF3F1",
    "warning": "#FDF7EC",
}


def tokens():
    """Diccionario NOMBRE -> valor, para reemplazar en el QSS."""
    return {k: v for k, v in globals().items() if k.isupper() and isinstance(v, (str, int))}
