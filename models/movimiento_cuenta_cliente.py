"""
Modelo de Movimientos de Cuenta de Cliente.

Este archivo tiene DOS tipos de funciones, y es importante que
distingas cual es cual:

1. Funciones que reciben un "cursor" ya abierto como parametro
   (ej. _calcular_saldo, registrar_cargo). Estas NO abren ni
   cierran su propia conexion - estan pensadas para usarse
   DENTRO de una transaccion mas grande que ya esta en curso
   (como la de una venta al credito). Quien las llama es
   responsable de hacer commit/rollback/close.

2. Funciones normales que abren y cierran su propia conexion
   (ej. obtener_saldo_cliente, listar_movimientos_cliente).
   Estas se usan para consultas independientes, como mostrar
   el saldo de un cliente en una pantalla que no esta en medio
   de ninguna otra operacion.

Esta separacion es la misma idea que ya viste en la Etapa 10
con las ventas: nunca mezclamos una funcion que abre su propia
conexion dentro de una transaccion que ya esta en curso en OTRA
conexion, porque eso rompe la atomicidad.
"""

from database.conexion import obtener_conexion


def calcular_saldo_con_cursor(cursor, id_cliente):
    """
    Calcula el saldo pendiente de un cliente SUMANDO todo su
    historial de cargos y abonos - nunca leemos un campo
    'saldo' guardado directamente, lo reconstruimos siempre a
    partir de los movimientos. Esto es lo que garantiza que el
    saldo sea siempre coherente con su historial completo.

    Nota sobre el nombre: a diferencia de otras funciones
    "internas" del proyecto (que llevan un guion bajo al
    inicio), esta SI se llama desde otros archivos de models/
    (ver models/venta.py) porque necesita ejecutarse dentro de
    la MISMA transaccion que una venta al credito. Por eso no
    lleva guion bajo: es "interna al paquete models", no
    "interna a este archivo".
    """
    cursor.execute(
        """
        SELECT COALESCE(SUM(
            CASE WHEN tipo = 'cargo' THEN monto ELSE -monto END
        ), 0) AS saldo
        FROM movimientos_cuenta_cliente
        WHERE id_cliente = ?;
        """,
        (id_cliente,)
    )
    return cursor.fetchone()["saldo"]
    # COALESCE(..., 0) es necesario porque SUM() sobre CERO filas
    # (un cliente que nunca ha tenido movimientos) devuelve NULL
    # en SQL, no 0 - y NULL causaria errores mas adelante si
    # intentamos sumarle o compararlo con un numero.


def registrar_cargo(cursor, id_cliente, id_venta, monto, descripcion):
    """
    Inserta un movimiento tipo 'cargo' (aumenta la deuda),
    usando el CURSOR que le pasaron - no abre conexion propia.
    Pensada para llamarse desde dentro de la transaccion de
    una venta al credito (ver models/venta.py).

    Devuelve el saldo_nuevo resultante.
    """
    saldo_anterior = calcular_saldo_con_cursor(cursor, id_cliente)
    saldo_nuevo = saldo_anterior + monto

    cursor.execute(
        """
        INSERT INTO movimientos_cuenta_cliente
            (id_cliente, tipo, id_venta, monto, saldo_anterior, saldo_nuevo, descripcion)
        VALUES (?, 'cargo', ?, ?, ?, ?, ?);
        """,
        (id_cliente, id_venta, monto, saldo_anterior, saldo_nuevo, descripcion)
    )

    return saldo_nuevo


def obtener_saldo_cliente(id_cliente):
    """
    Version "independiente" de _calcular_saldo: abre su propia
    conexion. Se usa para mostrar el saldo en pantallas que no
    estan en medio de otra transaccion (ej. el listado de
    creditos).
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    saldo = calcular_saldo_con_cursor(cursor, id_cliente)
    conexion.close()
    return saldo


def listar_movimientos_cliente(id_cliente, limite=100):
    """Historial completo de cargos y abonos de un cliente, mas recientes primero."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT id_movimiento, tipo, id_venta, id_pago, monto,
               saldo_anterior, saldo_nuevo, fecha, descripcion
        FROM movimientos_cuenta_cliente
        WHERE id_cliente = ?
        ORDER BY fecha DESC, id_movimiento DESC
        LIMIT ?;
        """,
        (id_cliente, limite)
    )
    filas = cursor.fetchall()
    conexion.close()
    return filas
