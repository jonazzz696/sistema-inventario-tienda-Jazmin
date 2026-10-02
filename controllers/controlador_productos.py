
from models import producto
from helpers.formato import texto_a_centavos


def obtener_lista_productos():
    return producto.listar_productos()


def obtener_producto_por_id(id_producto):
    return producto.obtener_producto(id_producto)


def registrar_producto(codigo, nombre, descripcion, id_categoria,
                        precio_compra_texto, precio_venta_texto,
                        existencia_texto, stock_minimo_texto, unidad_medida):
    try:
        precio_compra = texto_a_centavos(precio_compra_texto)
        precio_venta = texto_a_centavos(precio_venta_texto)
        existencia = int(existencia_texto)
        stock_minimo = int(stock_minimo_texto)

        if existencia < 0 or stock_minimo < 0:
            return False, "La existencia y el stock minimo no pueden ser negativos."

        producto.crear_producto(
            codigo, nombre, descripcion, id_categoria,
            precio_compra, precio_venta, existencia,
            stock_minimo, unidad_medida
        )
        return True, f"Producto '{nombre}' registrado correctamente."

    except ValueError as error:
        return False, str(error)
    except Exception as error:
        return False, f"Error inesperado: {error}"


def modificar_producto(id_producto, codigo, nombre, descripcion, id_categoria,
                        precio_compra_texto, precio_venta_texto,
                        stock_minimo_texto, unidad_medida):
    try:
        precio_compra = texto_a_centavos(precio_compra_texto)
        precio_venta = texto_a_centavos(precio_venta_texto)
        stock_minimo = int(stock_minimo_texto)

        if stock_minimo < 0:
            return False, "El stock minimo no puede ser negativo."

        producto.actualizar_producto(
            id_producto, codigo, nombre, descripcion, id_categoria,
            precio_compra, precio_venta, stock_minimo, unidad_medida
        )
        return True, f"Producto '{nombre}' actualizado correctamente."

    except ValueError as error:
        return False, str(error)
    except Exception as error:
        return False, f"Error inesperado: {error}"


def alternar_estado_producto(id_producto, estado_actual):
    """
    Si el producto esta activo (1), lo desactiva (0), y
    viceversa. Devuelve (exito, mensaje).
    """
    try:
        nuevo_estado = 0 if estado_actual == 1 else 1
        producto.cambiar_estado_producto(id_producto, nuevo_estado)
        texto_estado = "activado" if nuevo_estado == 1 else "desactivado"
        return True, f"Producto {texto_estado} correctamente."
    except Exception as error:
        return False, f"Error inesperado: {error}"
