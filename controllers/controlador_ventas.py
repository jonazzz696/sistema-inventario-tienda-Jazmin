
from models import venta, producto
from helpers import sesion


def obtener_productos_para_venta():
    todos = producto.listar_productos(solo_activos=True)
    return [p for p in todos if p["existencia"] > 0]


def registrar_venta(tipo_pago, id_cliente, carrito):
    
    usuario_actual = sesion.obtener_usuario_actual()

    if usuario_actual is None:
        return False, "No hay una sesion activa.", None

    try:
        resultado = venta.registrar_venta(
            id_usuario=usuario_actual["id_usuario"],
            tipo_pago=tipo_pago,
            id_cliente=id_cliente,
            items=carrito,
        )
        return True, f"Venta {resultado['numero_venta']} registrada correctamente.", resultado
    except ValueError as error:
        return False, str(error), None
    except Exception as error:
        return False, f"Error inesperado: {error}", None


def obtener_ventas_recientes():
    return venta.listar_ventas_recientes()
