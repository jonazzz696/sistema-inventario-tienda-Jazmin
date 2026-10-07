"""
Punto de entrada de Tienda Jazmin.

La interfaz ahora usa PySide6 (carpeta ui/). La logica, los modelos,
los controladores y la base de datos no cambiaron.

    pip install -r requirements.txt
    python main.py
"""

import sys

from database.conexion import inicializar_base_datos
from models.usuario import crear_admin_por_defecto


def main():

    inicializar_base_datos()

    se_creo_admin = crear_admin_por_defecto()
    if se_creo_admin:
        print(
            "Se creo un usuario administrador por defecto:\n"
            "  Usuario: admin\n"
            "  Contrasena: admin123\n"
        )

    from ui.app import run
    return run()


if __name__ == "__main__":
    sys.exit(main())
