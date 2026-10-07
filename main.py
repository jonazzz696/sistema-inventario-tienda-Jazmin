"""
Punto de entrada de Tienda Jazmin.

La interfaz ahora usa PySide6 (carpeta ui/). La logica, los modelos,
los controladores y la base de datos no cambiaron.

    pip install -r requirements.txt
    python main.py
"""

import sys

from database.conexion import inicializar_base_datos
from models.usuario import crear_usuarios_por_defecto


def main():

    inicializar_base_datos()

    for login, password in crear_usuarios_por_defecto():
        print(
            "Se creo un usuario por defecto:\n"
            f"  Usuario: {login}\n"
            f"  Contrasena: {password}\n"
        )

    from ui.app import run
    return run()


if __name__ == "__main__":
    sys.exit(main())
