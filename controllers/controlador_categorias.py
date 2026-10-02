
from models import categoria


def obtener_lista_categorias():
    return categoria.listar_categorias()


def registrar_categoria(nombre):

    try:
        categoria.crear_categoria(nombre)
        return True, f"Categoria '{nombre}' registrada correctamente."
    except ValueError as error:
        return False, str(error)
    except Exception as error:
        return False, f"Error inesperado: {error}"
