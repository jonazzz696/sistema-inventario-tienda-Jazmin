
_usuario_actual = None


def iniciar_sesion(datos_usuario):
    global _usuario_actual
    
    _usuario_actual = datos_usuario


def obtener_usuario_actual():
    
    return _usuario_actual


def cerrar_sesion():

    global _usuario_actual
    _usuario_actual = None


def hay_sesion_activa():

    return _usuario_actual is not None
