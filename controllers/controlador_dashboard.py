"""
Controlador del panel de Inicio (NUEVO - agregado con la interfaz PySide6).

Reune en un solo diccionario los datos que muestra la pantalla de
Inicio. Reutiliza las funciones que ya existian (stock bajo y ventas
recientes) y solo agrega las consultas nuevas de models/estadisticas.py.
"""

from models import estadisticas, movimiento_inventario, venta


def obtener_resumen():
    stock_bajo = movimiento_inventario.listar_productos_stock_bajo()
    return {
        "productos_activos": estadisticas.contar_productos_activos(),
        "stock_bajo": stock_bajo,
        "ventas_hoy": estadisticas.resumen_ventas_del_dia(),
        "credito": estadisticas.resumen_credito_pendiente(),
        "ventas_recientes": venta.listar_ventas_recientes(limite=6),
    }
