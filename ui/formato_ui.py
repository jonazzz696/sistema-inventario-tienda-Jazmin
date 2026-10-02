"""
Formatos de presentacion usados solo por la interfaz.
(Los formatos de dinero siguen viniendo de helpers/formato.py.)
"""

from datetime import datetime

METODOS_PAGO = [
    ("Efectivo", "efectivo"),
    ("Tarjeta", "tarjeta"),
    ("Otro", "otro"),
    ("Crédito", "credito"),
]
_ETIQUETA_PAGO = {clave: texto for texto, clave in METODOS_PAGO}


def fecha_corta(texto):
    """'2026-09-24 14:05:33' -> '24/09/2026 14:05'. Si no se puede leer, se deja igual."""
    if not texto:
        return ""
    for patron in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            fecha = datetime.strptime(str(texto), patron)
            return fecha.strftime("%d/%m/%Y %H:%M") if "%H" in patron else fecha.strftime("%d/%m/%Y")
        except ValueError:
            continue
    return str(texto)


def etiqueta_pago(clave):
    return _ETIQUETA_PAGO.get(clave, (clave or "").capitalize())


def badge_estado(fila, clave="estado"):
    return ("Activo", "success") if fila[clave] == 1 else ("Inactivo", "neutral")


def plural(n, singular, plural_):
    return f"{n} {singular if n == 1 else plural_}"
