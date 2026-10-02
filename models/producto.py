"""
Modelo de Productos.
"""

from database.conexion import obtener_conexion


def listar_productos(solo_activos=False):
    """
    Devuelve todos los productos, incluyendo el NOMBRE de su
    categoria (no solo el id_categoria numerico), usando un
    JOIN.

    Un JOIN une filas de dos tablas relacionadas. Aqui,
    "productos.id_categoria = categorias.id_categoria" le dice
    a SQLite: "por cada producto, busca la fila de categorias
    que tenga el mismo id, y pegame su columna nombre". Sin el
    JOIN, solo tendriamos el numero de categoria (ej. 3), que
    no le sirve de nada a la persona viendo la pantalla.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    consulta = """
        SELECT
            p.id_producto, p.codigo, p.nombre, p.descripcion,
            p.id_categoria, c.nombre AS nombre_categoria,
            p.precio_compra, p.precio_venta, p.existencia,
            p.stock_minimo, p.unidad_medida, p.estado
        FROM productos p
        JOIN categorias c ON p.id_categoria = c.id_categoria
    """
    # "p" y "c" son alias (apodos) para productos y categorias,
    # para no tener que escribir el nombre completo de la tabla
    # cada vez que referenciamos una columna.

    if solo_activos:
        consulta += " WHERE p.estado = 1"

    consulta += " ORDER BY p.nombre;"

    cursor.execute(consulta)
    filas = cursor.fetchall()
    conexion.close()

    return filas


def obtener_producto(id_producto):
    """Devuelve un solo producto por su id, o None si no existe."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT * FROM productos WHERE id_producto = ?;", (id_producto,)
    )
    fila = cursor.fetchone()
    conexion.close()
    return fila


def _validar_datos_producto(codigo, nombre, precio_compra, precio_venta,
                             existencia, stock_minimo):
    """
    Validaciones de negocio compartidas entre crear y actualizar.
    Un guion bajo al inicio del nombre indica "funcion de uso
    interno de este archivo", igual que vimos con los metodos
    privados de VentanaPrincipal en la Etapa 3.
    """
    if not codigo.strip():
        raise ValueError("El codigo del producto no puede estar vacio.")
    if not nombre.strip():
        raise ValueError("El nombre del producto no puede estar vacio.")
    if precio_compra < 0 or precio_venta < 0:
        raise ValueError("Los precios no pueden ser negativos.")
    if existencia < 0:
        raise ValueError("La existencia no puede ser negativa.")
    if stock_minimo < 0:
        raise ValueError("El stock minimo no puede ser negativo.")


def crear_producto(codigo, nombre, descripcion, id_categoria,
                    precio_compra, precio_venta, existencia,
                    stock_minimo, unidad_medida):
    """
    Inserta un nuevo producto. Los precios y la existencia
    llegan aqui ya convertidos a centavos/enteros (esa
    conversion la hace el controlador con helpers/formato.py,
    no este modelo).
    """
    _validar_datos_producto(
        codigo, nombre, precio_compra, precio_venta, existencia, stock_minimo
    )

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO productos
                (codigo, nombre, descripcion, id_categoria,
                 precio_compra, precio_venta, existencia,
                 stock_minimo, unidad_medida, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1);
            """,
            (codigo.strip(), nombre.strip(), descripcion.strip(), id_categoria,
             precio_compra, precio_venta, existencia, stock_minimo,
             unidad_medida.strip())
        )
        conexion.commit()
        nuevo_id = cursor.lastrowid
    except Exception as error:
        conexion.close()
        # UNIQUE en la columna codigo (ver schema.sql) salta aqui
        # si ya existe un producto con ese mismo codigo.
        if "UNIQUE" in str(error):
            raise ValueError(f"Ya existe un producto con el codigo '{codigo}'.")
        raise

    conexion.close()
    return nuevo_id


def actualizar_producto(id_producto, codigo, nombre, descripcion, id_categoria,
                         precio_compra, precio_venta, stock_minimo, unidad_medida):
    """
    Actualiza los datos generales de un producto.

    NOTA IMPORTANTE: esta funcion NO modifica 'existencia'.
    La cantidad disponible de un producto solo debe cambiar a
    traves de una venta (descuenta) o una compra (aumenta) -
    eso lo vamos a construir en las etapas de Ventas e
    Inventario, y ahi vamos a usar movimientos_inventario para
    dejar rastro de cada cambio, tal como diseñamos en la
    Etapa 2. Si dejaramos que este formulario tocara la
    existencia libremente, perderiamos esa trazabilidad.
    """
    _validar_datos_producto(
        codigo, nombre, precio_compra, precio_venta, 0, stock_minimo
    )
    # Pasamos existencia=0 solo para que la validacion de "no
    # negativo" no falle - esta funcion no toca ese campo.

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            """
            UPDATE productos
            SET codigo = ?, nombre = ?, descripcion = ?, id_categoria = ?,
                precio_compra = ?, precio_venta = ?, stock_minimo = ?,
                unidad_medida = ?
            WHERE id_producto = ?;
            """,
            (codigo.strip(), nombre.strip(), descripcion.strip(), id_categoria,
             precio_compra, precio_venta, stock_minimo, unidad_medida.strip(),
             id_producto)
        )
        conexion.commit()
    except Exception as error:
        conexion.close()
        if "UNIQUE" in str(error):
            raise ValueError(f"Ya existe un producto con el codigo '{codigo}'.")
        raise

    conexion.close()


def cambiar_estado_producto(id_producto, nuevo_estado):
    """
    Activa (1) o desactiva (0) un producto. Como se explico en
    el analisis (Etapa 1), NO borramos productos fisicamente de
    la base de datos si ya tienen ventas asociadas, porque eso
    rompe la relacion con detalle_ventas y perderiamos el
    historial. En su lugar, se desactivan: dejan de aparecer
    para nuevas ventas, pero el historial sigue intacto.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "UPDATE productos SET estado = ? WHERE id_producto = ?;",
        (nuevo_estado, id_producto)
    )
    conexion.commit()
    conexion.close()
