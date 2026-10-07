"""
Modelo de Usuarios.
"""

from database.conexion import obtener_conexion
from helpers.seguridad import generar_hash


def contar_usuarios():
    """
    Devuelve cuantos usuarios existen en total. Se usa al
    arrancar el programa para saber si hay que crear un
    usuario administrador por defecto (ver database/conexion.py).
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM usuarios;")
    resultado = cursor.fetchone()
    conexion.close()

    return resultado["total"]


def obtener_usuario_por_login(nombre_usuario):
    """
    Busca un usuario por su nombre de login (columna 'usuario').
    Devuelve la fila si existe y esta activo, o None si no.

    Nota: el filtro "estado = 1" esta aqui a proposito. Un
    usuario desactivado NO debe poder iniciar sesion, aunque
    escriba la contrasena correcta - por eso ni siquiera lo
    devolvemos, para que el controlador lo trate igual que un
    usuario que no existe (mensaje generico, sin revelar si el
    problema fue "no existe" o "esta desactivado").
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT id_usuario, nombre, usuario, password_hash, rol, estado "
        "FROM usuarios WHERE usuario = ? AND estado = 1;",
        (nombre_usuario,)
    )
    fila = cursor.fetchone()
    conexion.close()

    return fila


def crear_usuario(nombre, usuario, password, rol):
    """
    Inserta un nuevo usuario, guardando la contrasena ya
    convertida en hash (nunca en texto plano).
    """
    nombre = nombre.strip()
    usuario = usuario.strip()

    if not nombre or not usuario:
        raise ValueError("El nombre y el usuario no pueden estar vacios.")

    if rol not in ("admin", "vendedor"):
        raise ValueError("El rol debe ser 'admin' o 'vendedor'.")

    if len(password) < 6:
        raise ValueError("La contrasena debe tener al menos 6 caracteres.")

    password_hash = generar_hash(password)

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            "INSERT INTO usuarios (nombre, usuario, password_hash, rol, estado) "
            "VALUES (?, ?, ?, ?, 1);",
            (nombre, usuario, password_hash, rol)
        )
        conexion.commit()
        nuevo_id = cursor.lastrowid
    except Exception as error:
        # sqlite3.IntegrityError salta aqui si el "usuario"
        # (login) ya existe, porque la columna tiene UNIQUE en
        # el schema. La convertimos en un mensaje claro.
        conexion.close()
        if "UNIQUE" in str(error):
            raise ValueError(f"El nombre de usuario '{usuario}' ya existe.")
        raise

    conexion.close()
    return nuevo_id


def crear_admin_por_defecto():
    """
    Si la tabla de usuarios esta completamente vacia (primera
    vez que se ejecuta el programa), crea un usuario
    administrador por defecto, para que exista una forma de
    entrar al sistema.

    Usuario: admin
    Contrasena: admin123

    Esto se llama automaticamente al arrancar main.py. Es
    importante que, la primera vez que uses el sistema, entres
    y crees tu propio usuario administrador con una contrasena
    fuerte, y luego (en una etapa futura, cuando tengamos el
    modulo de gestion de usuarios completo) cambies o elimines
    este usuario 'admin' por defecto.
    """
    if contar_usuarios() == 0:
        crear_usuario(
            nombre="Administrador",
            usuario="admin",
            password="admin123",
            rol="admin",
        )
        return True  # indica que SI se creo el admin por defecto
    return False
