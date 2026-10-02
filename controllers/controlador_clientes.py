

from models import cliente
from helpers.formato import texto_a_centavos


def obtener_lista_clientes():
    return cliente.listar_clientes()


def obtener_cliente_por_id(id_cliente):
    return cliente.obtener_cliente(id_cliente)


def _convertir_limite_credito(texto):
    texto = texto.strip()
    if not texto:
        return None
    return texto_a_centavos(texto)


def registrar_cliente(nombre_completo, telefono, dui, direccion, correo,
                       limite_credito_texto):
    try:
        limite_credito = _convertir_limite_credito(limite_credito_texto)
        cliente.crear_cliente(
            nombre_completo, telefono, dui, direccion, correo, limite_credito
        )
        return True, f"Cliente '{nombre_completo}' registrado correctamente."
    except ValueError as error:
        return False, str(error)
    except Exception as error:
        return False, f"Error inesperado: {error}"


def modificar_cliente(id_cliente, nombre_completo, telefono, dui, direccion,
                       correo, limite_credito_texto):
    try:
        limite_credito = _convertir_limite_credito(limite_credito_texto)
        cliente.actualizar_cliente(
            id_cliente, nombre_completo, telefono, dui, direccion, correo,
            limite_credito
        )
        return True, f"Cliente '{nombre_completo}' actualizado correctamente."
    except ValueError as error:
        return False, str(error)
    except Exception as error:
        return False, f"Error inesperado: {error}"


def alternar_estado_cliente(id_cliente, estado_actual):
    try:
        nuevo_estado = 0 if estado_actual == 1 else 1
        cliente.cambiar_estado_cliente(id_cliente, nuevo_estado)
        texto_estado = "activado" if nuevo_estado == 1 else "desactivado"
        return True, f"Cliente {texto_estado} correctamente."
    except Exception as error:
        return False, f"Error inesperado: {error}"
