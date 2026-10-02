
from models import movimiento_inventario


def registrar_movimiento_manual(id_producto, tipo, cantidad_texto, descripcion):
    
    try:
        cantidad = int(cantidad_texto)
    except ValueError:
        return False, "La cantidad debe ser un numero entero."

    if cantidad <= 0:
        return False, "La cantidad debe ser mayor a cero."

    try:
        nueva_existencia = movimiento_inventario.registrar_movimiento(
            id_producto, tipo, cantidad, descripcion=descripcion.strip() or None
        )
        return True, f"Movimiento registrado. Nueva existencia: {nueva_existencia}."
    except ValueError as error:
        return False, str(error)
    except Exception as error:
        return False, f"Error inesperado: {error}"


def obtener_historial(id_producto=None):
    return movimiento_inventario.listar_movimientos(id_producto=id_producto)


def obtener_productos_stock_bajo():
    return movimiento_inventario.listar_productos_stock_bajo()
