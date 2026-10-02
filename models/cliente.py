"""
Modelo de Clientes.
"""

from database.conexion import obtener_conexion


def listar_clientes(solo_activos=False):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    consulta = "SELECT * FROM clientes"
    if solo_activos:
        consulta += " WHERE estado = 1"
    consulta += " ORDER BY nombre_completo;"

    cursor.execute(consulta)
    filas = cursor.fetchall()
    conexion.close()
    return filas


def obtener_cliente(id_cliente):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM clientes WHERE id_cliente = ?;", (id_cliente,))
    fila = cursor.fetchone()
    conexion.close()
    return fila


def _validar_datos_cliente(nombre_completo, telefono):
    """
    Solo nombre y telefono son obligatorios, tal como se acordo
    en el analisis inicial (Etapa 1): para una tienda pequena,
    pedir DUI, direccion o correo de forma obligatoria agrega
    friccion innecesaria al registrar un cliente rapido en el
    mostrador.
    """
    if not nombre_completo.strip():
        raise ValueError("El nombre del cliente no puede estar vacio.")
    if not telefono.strip():
        raise ValueError("El telefono del cliente no puede estar vacio.")


def crear_cliente(nombre_completo, telefono, dui, direccion, correo, limite_credito):
    """
    limite_credito llega ya convertido a centavos (o None si se
    dejo en blanco) - esa conversion la hace el controlador,
    igual que con los precios de productos.
    """
    _validar_datos_cliente(nombre_completo, telefono)

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        INSERT INTO clientes
            (nombre_completo, telefono, dui, direccion, correo,
             limite_credito, estado)
        VALUES (?, ?, ?, ?, ?, ?, 1);
        """,
        (nombre_completo.strip(), telefono.strip(),
         dui.strip() or None, direccion.strip() or None,
         correo.strip() or None, limite_credito)
    )
    conexion.commit()
    nuevo_id = cursor.lastrowid
    conexion.close()
    return nuevo_id


def actualizar_cliente(id_cliente, nombre_completo, telefono, dui, direccion,
                        correo, limite_credito):
    _validar_datos_cliente(nombre_completo, telefono)

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        UPDATE clientes
        SET nombre_completo = ?, telefono = ?, dui = ?, direccion = ?,
            correo = ?, limite_credito = ?
        WHERE id_cliente = ?;
        """,
        (nombre_completo.strip(), telefono.strip(),
         dui.strip() or None, direccion.strip() or None,
         correo.strip() or None, limite_credito, id_cliente)
    )
    conexion.commit()
    conexion.close()


def cambiar_estado_cliente(id_cliente, nuevo_estado):
    """
    Igual que con productos: no se borra un cliente fisicamente
    (rompe la relacion con ventas y pagos ya registrados), se
    desactiva.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "UPDATE clientes SET estado = ? WHERE id_cliente = ?;",
        (nuevo_estado, id_cliente)
    )
    conexion.commit()
    conexion.close()
