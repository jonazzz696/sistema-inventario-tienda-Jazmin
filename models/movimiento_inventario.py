"""
Modelo de Movimientos de Inventario.

Este modulo es el primero donde usamos una TRANSACCION real,
asi que te explico el concepto con calma.

QUE ES UNA TRANSACCION Y POR QUE IMPORTA AQUI:

Registrar un movimiento de inventario en realidad son DOS
operaciones separadas en la base de datos:
  1. Actualizar el campo 'existencia' en la tabla productos.
  2. Insertar una fila nueva en movimientos_inventario, dejando
     el rastro de ese cambio.

Si estas dos operaciones no estan "amarradas" entre si, podria
pasar esto: la operacion 1 se ejecuta bien (la existencia se
actualiza), pero justo despues el programa falla por cualquier
razon (se va la luz, un bug, el disco se llena) ANTES de que la
operacion 2 se ejecute. Resultado: la existencia del producto
cambio, pero no queda ningun registro de por que cambio. Eso es
exactamente lo que NO queremos, porque rompe la trazabilidad
que disenamos desde la Etapa 2.

Una transaccion resuelve esto tratando varias operaciones como
un solo bloque indivisible ("todo o nada"): si algo falla a la
mitad, se hace ROLLBACK (se deshacen TODOS los cambios de ese
bloque, como si nunca hubiera pasado nada). Si todo sale bien,
se hace COMMIT (los cambios se guardan de forma permanente,
todos juntos).

En Python con sqlite3, no hace falta escribir "BEGIN"
explicitamente: la libreria abre una transaccion automaticamente
en cuanto ejecutas el primer INSERT/UPDATE/DELETE despues de un
commit. Nuestro trabajo es solo: envolver las operaciones
relacionadas en un try/except, hacer conexion.commit() si todo
sale bien, y conexion.rollback() si algo falla.
"""

from database.conexion import obtener_conexion


def registrar_movimiento(id_producto, tipo, cantidad, descripcion=None,
                          id_venta=None, id_compra=None):
    """
    Registra un movimiento de inventario y actualiza la
    existencia del producto correspondiente, todo dentro de
    una sola transaccion.

    tipo: 'entrada' (aumenta existencia) o 'salida' (la disminuye).
    cantidad: debe ser un entero positivo.
    descripcion: motivo del movimiento (opcional, mas util en
                 movimientos manuales que en ventas/compras,
                 donde el id_venta/id_compra ya explica el origen).
    id_venta / id_compra: se llenan automaticamente cuando este
                 movimiento viene de una venta o compra real
                 (lo vamos a usar en las etapas de Ventas y
                 Compras). Para movimientos manuales, ambos
                 quedan en None.

    Devuelve la nueva existencia del producto.
    Lanza ValueError si los datos no son validos (producto
    inexistente, cantidad invalida, o salida mayor a la
    existencia disponible).
    """
    if tipo not in ("entrada", "salida"):
        raise ValueError("El tipo de movimiento debe ser 'entrada' o 'salida'.")

    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor a cero.")

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        # Paso 1: leer la existencia actual del producto.
        cursor.execute(
            "SELECT existencia FROM productos WHERE id_producto = ?;",
            (id_producto,)
        )
        fila = cursor.fetchone()

        if fila is None:
            raise ValueError("El producto no existe.")

        existencia_anterior = fila["existencia"]

        # Paso 2: calcular la nueva existencia segun el tipo.
        if tipo == "entrada":
            existencia_nueva = existencia_anterior + cantidad
        else:  # 'salida'
            if cantidad > existencia_anterior:
                raise ValueError(
                    f"No hay suficiente existencia. Disponible: {existencia_anterior}, "
                    f"se intento retirar: {cantidad}."
                )
            existencia_nueva = existencia_anterior - cantidad

        # Paso 3: actualizar productos.existencia.
        cursor.execute(
            "UPDATE productos SET existencia = ? WHERE id_producto = ?;",
            (existencia_nueva, id_producto)
        )

        # Paso 4: insertar el registro del movimiento, dejando
        # el rastro de este cambio.
        cursor.execute(
            """
            INSERT INTO movimientos_inventario
                (id_producto, tipo, cantidad, existencia_anterior,
                 existencia_nueva, id_venta, id_compra, descripcion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (id_producto, tipo, cantidad, existencia_anterior,
             existencia_nueva, id_venta, id_compra, descripcion)
        )

        # Si llegamos hasta aqui sin errores, confirmamos AMBOS
        # cambios de forma permanente y junta.
        conexion.commit()

    except Exception:
        # Si CUALQUIER cosa fallo arriba (el ValueError que
        # nosotros lanzamos, o un error inesperado de SQLite),
        # deshacemos cualquier cambio a medio hacer. Gracias a
        # esto, nunca queda la existencia actualizada sin su
        # movimiento correspondiente, ni viceversa.
        conexion.rollback()
        raise  # volvemos a lanzar el error para que el controlador lo maneje

    finally:
        # finally se ejecuta SIEMPRE, haya habido error o no.
        # Cerramos la conexion en ambos casos.
        conexion.close()

    return existencia_nueva


def listar_movimientos(id_producto=None, limite=100):
    """
    Devuelve el historial de movimientos, mas recientes primero.
    Si se pasa id_producto, filtra solo los de ese producto.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    consulta = """
        SELECT
            m.id_movimiento, m.tipo, m.cantidad,
            m.existencia_anterior, m.existencia_nueva,
            m.descripcion, m.fecha,
            p.nombre AS nombre_producto, p.codigo
        FROM movimientos_inventario m
        JOIN productos p ON m.id_producto = p.id_producto
    """
    parametros = ()

    if id_producto is not None:
        consulta += " WHERE m.id_producto = ?"
        parametros = (id_producto,)

    consulta += " ORDER BY m.fecha DESC, m.id_movimiento DESC LIMIT ?;"
    parametros = parametros + (limite,)

    cursor.execute(consulta, parametros)
    filas = cursor.fetchall()
    conexion.close()

    return filas


def listar_productos_stock_bajo():
    """
    Devuelve los productos activos cuya existencia ya llego a
    su stock minimo o menos. Se usa para la alerta de inventario
    bajo.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT id_producto, codigo, nombre, existencia, stock_minimo
        FROM productos
        WHERE estado = 1 AND existencia <= stock_minimo
        ORDER BY existencia ASC;
        """
    )
    filas = cursor.fetchall()
    conexion.close()

    return filas
