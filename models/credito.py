"""
Modelo de Creditos (cuentas por cobrar).

Un CREDITO es una venta con tipo_pago = 'credito' (tabla ventas). No se
crea una tabla aparte: el numero del credito es el numero de la venta y
el total es el total de la venta.

Los PAGOS de un credito se guardan en la tabla 'pagos' (ya existia en el
schema) con id_venta apuntando a la venta que abonan. Cada pago tambien
deja un 'abono' en movimientos_cuenta_cliente, para que el saldo del
cliente (y su limite de credito) sigan calculandose igual que antes.

Pagado, saldo y estado NUNCA se guardan: se calculan desde los pagos.
Asi el estado siempre esta al dia y no puede contradecir el historial.
    PENDIENTE  pagado = 0
    PARCIAL    0 < pagado < total
    PAGADO     pagado >= total
"""

from datetime import datetime

from database.conexion import obtener_conexion
from helpers.formato import centavos_a_texto
from models import movimiento_cuenta_cliente

METODOS_COBRO = ("efectivo", "tarjeta", "otro")

_SUBCONSULTA_PAGOS = """
    SELECT id_venta, SUM(monto) AS pagado, COUNT(*) AS pagos, MAX(fecha) AS ultimo_pago
    FROM pagos
    WHERE id_venta IS NOT NULL
    GROUP BY id_venta
"""


def estado_credito(total, pagado):
    if pagado <= 0:
        return "pendiente"
    if pagado >= total:
        return "pagado"
    return "parcial"


def _completar(fila):
    fila = dict(fila)
    fila["pagado"] = fila.get("pagado") or 0
    fila["pagos"] = fila.get("pagos") or 0
    fila["saldo"] = max(0, fila["total"] - fila["pagado"])
    fila["estado_credito"] = estado_credito(fila["total"], fila["pagado"])
    return fila


def listar_creditos():
    """Todos los creditos (ventas a credito no anuladas), mas recientes primero."""
    conexion = obtener_conexion()
    try:
        filas = conexion.execute(
            f"""
            SELECT v.id_venta, v.numero_venta, v.fecha, v.total,
                   v.id_cliente, c.nombre_completo, c.telefono, c.estado AS estado_cliente,
                   p.pagado, p.pagos, p.ultimo_pago
            FROM ventas v
            JOIN clientes c ON c.id_cliente = v.id_cliente
            LEFT JOIN ({_SUBCONSULTA_PAGOS}) p ON p.id_venta = v.id_venta
            WHERE v.tipo_pago = 'credito' AND v.estado = 1
            ORDER BY v.fecha DESC, v.id_venta DESC;
            """
        ).fetchall()
    finally:
        conexion.close()
    return [_completar(f) for f in filas]


def obtener_credito(id_venta):
    """Un credito con su cliente, productos y pagos. None si no existe o no es a credito."""
    conexion = obtener_conexion()
    try:
        fila = conexion.execute(
            f"""
            SELECT v.id_venta, v.numero_venta, v.fecha, v.total,
                   v.id_cliente, c.nombre_completo, c.telefono, c.dui, c.direccion,
                   u.nombre AS vendedor,
                   p.pagado, p.pagos, p.ultimo_pago
            FROM ventas v
            JOIN clientes c ON c.id_cliente = v.id_cliente
            JOIN usuarios u ON u.id_usuario = v.id_usuario
            LEFT JOIN ({_SUBCONSULTA_PAGOS}) p ON p.id_venta = v.id_venta
            WHERE v.id_venta = ? AND v.tipo_pago = 'credito' AND v.estado = 1;
            """,
            (id_venta,),
        ).fetchone()
        if fila is None:
            return None
        credito = _completar(fila)
        credito["productos"] = [dict(f) for f in conexion.execute(
            """
            SELECT p.codigo, p.nombre, d.cantidad, d.precio_unitario, d.subtotal
            FROM detalle_ventas d
            JOIN productos p ON p.id_producto = d.id_producto
            WHERE d.id_venta = ?
            ORDER BY d.id_detalle;
            """,
            (id_venta,),
        ).fetchall()]
        credito["historial"] = [dict(f) for f in conexion.execute(
            """
            SELECT pg.id_pago, pg.fecha, pg.monto, pg.metodo_pago, pg.observacion,
                   u.nombre AS usuario
            FROM pagos pg
            JOIN usuarios u ON u.id_usuario = pg.id_usuario
            WHERE pg.id_venta = ?
            ORDER BY pg.fecha, pg.id_pago;
            """,
            (id_venta,),
        ).fetchall()]
    finally:
        conexion.close()

    # Saldo despues de cada pago (para el historial y el comprobante).
    acumulado = 0
    for pago in credito["historial"]:
        acumulado += pago["monto"]
        pago["pagado_acumulado"] = acumulado
        pago["saldo_despues"] = max(0, credito["total"] - acumulado)
    return credito


def registrar_pago(id_venta, monto, metodo_pago, id_usuario, fecha=None, observacion=None):
    """
    Registra un pago a un credito, todo en UNA transaccion:
      1. valida el credito y el monto (no cero, no negativo, no mayor al saldo),
      2. inserta el pago en 'pagos' (asociado a la venta),
      3. inserta el 'abono' en movimientos_cuenta_cliente (saldo del cliente).
    Si algo falla, no queda nada a medias (rollback).

    NO crea otra venta ni toca el inventario: los productos se descontaron
    cuando se hizo la venta original.

    monto: centavos (int). fecha: datetime o None (= ahora).
    Devuelve un dict con total, pagado, saldo y estado despues del pago.
    """
    if metodo_pago not in METODOS_COBRO:
        raise ValueError("Elige un método de pago válido (efectivo, tarjeta u otro).")
    if not isinstance(monto, int) or monto <= 0:
        raise ValueError("El monto del pago debe ser mayor que $0.00.")

    fecha = fecha or datetime.now()
    fecha_texto = fecha.strftime("%Y-%m-%d %H:%M:%S")

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        # Reserva la base para escribir desde ya: el saldo que se lee abajo no
        # puede cambiar (p. ej. otro pago desde otra PC) antes de guardar este.
        cursor.execute("BEGIN IMMEDIATE;")
        cursor.execute(
            """
            SELECT v.id_venta, v.numero_venta, v.total, v.id_cliente, v.fecha, v.tipo_pago, v.estado
            FROM ventas v WHERE v.id_venta = ?;
            """,
            (id_venta,),
        )
        venta = cursor.fetchone()
        if venta is None:
            raise ValueError("El crédito no existe.")
        if venta["tipo_pago"] != "credito" or venta["estado"] != 1:
            raise ValueError("Esa venta no es un crédito activo.")
        if fecha_texto[:10] < venta["fecha"][:10]:
            raise ValueError("La fecha del pago no puede ser anterior a la fecha de la venta.")

        cursor.execute("SELECT COALESCE(SUM(monto), 0) AS pagado FROM pagos WHERE id_venta = ?;", (id_venta,))
        pagado_antes = cursor.fetchone()["pagado"]
        saldo_credito = venta["total"] - pagado_antes

        if saldo_credito <= 0:
            raise ValueError("Este crédito ya está pagado por completo.")
        if monto > saldo_credito:
            raise ValueError(
                f"El pago no puede ser superior al saldo pendiente de {centavos_a_texto(saldo_credito)}.")

        saldo_cliente_antes = movimiento_cuenta_cliente.calcular_saldo_con_cursor(cursor, venta["id_cliente"])
        saldo_cliente_despues = saldo_cliente_antes - monto

        cursor.execute(
            """
            INSERT INTO pagos
                (id_cliente, fecha, monto, id_usuario, observacion,
                 saldo_anterior, saldo_nuevo, id_venta, metodo_pago)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (venta["id_cliente"], fecha_texto, monto, id_usuario, (observacion or "").strip() or None,
             saldo_cliente_antes, saldo_cliente_despues, id_venta, metodo_pago),
        )
        id_pago = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO movimientos_cuenta_cliente
                (id_cliente, tipo, id_pago, monto, saldo_anterior, saldo_nuevo, fecha, descripcion)
            VALUES (?, 'abono', ?, ?, ?, ?, ?, ?);
            """,
            (venta["id_cliente"], id_pago, monto, saldo_cliente_antes, saldo_cliente_despues,
             fecha_texto, f"Pago a crédito {venta['numero_venta']}"),
        )
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()

    pagado = pagado_antes + monto
    return {
        "id_pago": id_pago,
        "numero_venta": venta["numero_venta"],
        "total": venta["total"],
        "pagado": pagado,
        "saldo": venta["total"] - pagado,
        "estado": estado_credito(venta["total"], pagado),
    }


# ----------------------------------------------------------------------
# Cobros por periodo (para reportes y el inicio)
# ----------------------------------------------------------------------

def resumen_cobros(desde, hasta):
    """Cantidad y monto de pagos de credito recibidos en [desde, hasta)."""
    conexion = obtener_conexion()
    try:
        fila = conexion.execute(
            """
            SELECT COUNT(*) AS pagos, COALESCE(SUM(monto), 0) AS monto
            FROM pagos
            WHERE id_venta IS NOT NULL AND fecha >= ? AND fecha < ?;
            """,
            (desde, hasta),
        ).fetchone()
        return dict(fila)
    finally:
        conexion.close()


def cobros_por_metodo(desde, hasta):
    conexion = obtener_conexion()
    try:
        return [dict(f) for f in conexion.execute(
            """
            SELECT COALESCE(metodo_pago, 'otro') AS metodo_pago, COUNT(*) AS pagos,
                   COALESCE(SUM(monto), 0) AS monto
            FROM pagos
            WHERE id_venta IS NOT NULL AND fecha >= ? AND fecha < ?
            GROUP BY COALESCE(metodo_pago, 'otro');
            """,
            (desde, hasta),
        ).fetchall()]
    finally:
        conexion.close()


def serie_cobros(desde, hasta, formato_grupo):
    conexion = obtener_conexion()
    try:
        return [dict(f) for f in conexion.execute(
            """
            SELECT strftime(?, fecha) AS grupo, COALESCE(SUM(monto), 0) AS monto
            FROM pagos
            WHERE id_venta IS NOT NULL AND fecha >= ? AND fecha < ?
            GROUP BY grupo;
            """,
            (formato_grupo, desde, hasta),
        ).fetchall()]
    finally:
        conexion.close()


def listar_pagos_periodo(desde, hasta):
    """Pagos de credito recibidos en el periodo, con su venta y cliente."""
    conexion = obtener_conexion()
    try:
        return [dict(f) for f in conexion.execute(
            """
            SELECT pg.fecha, pg.monto, pg.metodo_pago, v.numero_venta, c.nombre_completo
            FROM pagos pg
            JOIN ventas v   ON v.id_venta = pg.id_venta
            JOIN clientes c ON c.id_cliente = pg.id_cliente
            WHERE pg.id_venta IS NOT NULL AND pg.fecha >= ? AND pg.fecha < ?
            ORDER BY pg.fecha DESC, pg.id_pago DESC;
            """,
            (desde, hasta),
        ).fetchall()]
    finally:
        conexion.close()
