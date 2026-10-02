
from models import usuario
from helpers.seguridad import verificar_password
from helpers import sesion


def iniciar_sesion(nombre_usuario, password):
    
    nombre_usuario = nombre_usuario.strip()

    if not nombre_usuario or not password:
        return False, "Debes ingresar usuario y contrasena."

    fila_usuario = usuario.obtener_usuario_por_login(nombre_usuario)

    if fila_usuario is None:
        return False, "Usuario o contrasena incorrectos."

    if not verificar_password(password, fila_usuario["password_hash"]):
        return False, "Usuario o contrasena incorrectos."

    sesion.iniciar_sesion({
        "id_usuario": fila_usuario["id_usuario"],
        "nombre": fila_usuario["nombre"],
        "usuario": fila_usuario["usuario"],
        "rol": fila_usuario["rol"],
    })

    return True, f"Bienvenido, {fila_usuario['nombre']}."
