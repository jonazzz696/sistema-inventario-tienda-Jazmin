"""
Modelo de Categorias.

Un "modelo" en este proyecto es simplemente un archivo con
funciones que saben como leer y escribir una tabla especifica
de la base de datos. La vista y el controlador NUNCA deberian
escribir SQL directamente - siempre pasan por aqui.

Esto es equivalente a lo que hacia tu model.php en PHP: aislar
las consultas SQL en un solo lugar, para que si cambias de
motor de base de datos (o si hay un bug en una consulta), solo
tengas que tocar este archivo.
"""

from database.conexion import obtener_conexion


def listar_categorias(solo_activas=False):
    """
    Devuelve una lista de todas las categorias.

    El parametro solo_activas es opcional (por eso tiene un
    valor por defecto, False). Si se llama listar_categorias()
    sin argumentos, trae todas. Si se llama
    listar_categorias(solo_activas=True), trae solo las que
    tienen estado = 1.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    if solo_activas:
        cursor.execute(
            "SELECT id_categoria, nombre, estado FROM categorias "
            "WHERE estado = 1 ORDER BY nombre;"
        )
    else:
        cursor.execute(
            "SELECT id_categoria, nombre, estado FROM categorias "
            "ORDER BY nombre;"
        )

    # fetchall() trae todas las filas del resultado. Gracias al
    # row_factory que configuramos en conexion.py, cada fila se
    # puede leer como diccionario (fila["nombre"]).
    filas = cursor.fetchall()
    conexion.close()

    return filas


def crear_categoria(nombre):
    """
    Inserta una nueva categoria. Devuelve el id_categoria
    generado, o lanza un ValueError si el nombre esta vacio.

    Nota: aqui validamos que el nombre no este vacio ANTES de
    tocar la base de datos. La tabla no tiene una restriccion
    CHECK para esto porque un nombre vacio ("") es tecnicamente
    un TEXT valido para SQLite - la regla de "no puede estar
    vacio" es una regla de negocio, no de tipo de dato, y esas
    se validan en el modelo o el controlador, no en el schema.
    """
    nombre = nombre.strip()  # quita espacios sobrantes al inicio/final

    if not nombre:
        raise ValueError("El nombre de la categoria no puede estar vacio.")

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    # El "?" es un marcador de posicion (placeholder). SQLite
    # sustituye el "?" por el valor de forma segura, evitando
    # SQL Injection. NUNCA se debe armar la consulta pegando
    # el valor directamente en el texto (ej. f"...'{nombre}'"),
    # porque eso es justo lo que permite ataques de inyeccion SQL.
    cursor.execute(
        "INSERT INTO categorias (nombre, estado) VALUES (?, 1);",
        (nombre,)
    )

    conexion.commit()
    nuevo_id = cursor.lastrowid  # id autogenerado de la fila insertada
    conexion.close()

    return nuevo_id


if __name__ == "__main__":
    # Prueba rapida y aislada de este modelo, sin pasar por la
    # interfaz grafica. Sirve para confirmar que el modelo
    # funciona antes de conectarlo con la vista.
    from database.conexion import inicializar_base_datos
    inicializar_base_datos()

    print("Categorias antes de insertar:", listar_categorias())

    id_nueva = crear_categoria("Bebidas")
    print(f"Categoria creada con id {id_nueva}")

    print("Categorias despues de insertar:", listar_categorias())
