"""
Modelo de Reportes (NUEVO). Solo consultas de LECTURA.

Todas las funciones reciben el rango [desde, hasta) como texto
'YYYY-MM-DD HH:MM:SS' y filtran en SQL, asi nunca se carga la base
completa aunque tenga muchos anos de datos.

Reglas para no contar dos veces la misma operacion:
  - Cada venta tambien deja una fila 'salida' en movimientos_inventario
    (con id_venta). Por eso las "salidas manuales" son las salidas SIN
    id_venta, y las ventas se leen de ventas/detalle_ventas.
  - Las ventas con estado = 0 (anuladas) no se cuentan.
"""

from database.conexion import obtener_conexion

_VENTA_VALIDA = "v.estado = 1 AND v.fecha >= ? AND v.fecha < ?"


def _consultar(sql, parametros=()):
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute(sql, parametros)
        return [dict(fila) for fila in cursor.fetchall()]
    finally:
        conexion.close()


# ----------------------------------------------------------------------
# Ventas
# ----------------------------------------------------------------------

def resumen_ventas(desde, hasta):
    """Cantidad de ventas, ingresos, unidades vendidas y totales al credito."""
    fila = _consultar(
        f"""
        SELECT
            COUNT(*)                                                        AS ventas,
            COALESCE(SUM(v.total), 0)                                       AS ingresos,
            COALESCE(SUM(CASE WHEN v.tipo_pago = 'credito' THEN 1 ELSE 0 END), 0)       AS ventas_credito,
            COALESCE(SUM(CASE WHEN v.tipo_pago = 'credito' THEN v.total ELSE 0 END), 0) AS monto_credito,
            COUNT(DISTINCT v.id_cliente)                                    AS clientes
        FROM ventas v
        WHERE {_VENTA_VALIDA};
        """,
        (desde, hasta),
    )[0]
    unidades = _consultar(
        f"""
        SELECT COALESCE(SUM(d.cantidad), 0) AS unidades
        FROM detalle_ventas d
        JOIN ventas v ON v.id_venta = d.id_venta
        WHERE {_VENTA_VALIDA};
        """,
        (desde, hasta),
    )[0]["unidades"]
    fila["unidades"] = unidades
    return fila


def ventas_por_metodo(desde, hasta):
    return _consultar(
        f"""
        SELECT v.tipo_pago, COUNT(*) AS ventas, COALESCE(SUM(v.total), 0) AS monto
        FROM ventas v
        WHERE {_VENTA_VALIDA}
        GROUP BY v.tipo_pago;
        """,
        (desde, hasta),
    )


def serie_ventas(desde, hasta, formato_grupo):
    """Monto vendido (total y de contado) y cantidad de ventas por hora/dia/mes."""
    return _consultar(
        f"""
        SELECT strftime(?, v.fecha) AS grupo,
               COUNT(*)             AS ventas,
               COALESCE(SUM(v.total), 0) AS monto,
               COALESCE(SUM(CASE WHEN v.tipo_pago <> 'credito' THEN v.total ELSE 0 END), 0) AS monto_contado
        FROM ventas v
        WHERE {_VENTA_VALIDA}
        GROUP BY grupo;
        """,
        (formato_grupo, desde, hasta),
    )


def productos_mas_vendidos(desde, hasta, limite=10):
    return _consultar(
        f"""
        SELECT p.id_producto, p.codigo, p.nombre,
               SUM(d.cantidad) AS unidades,
               SUM(d.subtotal) AS ingresos,
               COUNT(DISTINCT d.id_venta) AS ventas
        FROM detalle_ventas d
        JOIN ventas v    ON v.id_venta = d.id_venta
        JOIN productos p ON p.id_producto = d.id_producto
        WHERE {_VENTA_VALIDA}
        GROUP BY p.id_producto
        ORDER BY unidades DESC, ingresos DESC
        LIMIT ?;
        """,
        (desde, hasta, limite),
    )


# ----------------------------------------------------------------------
# Movimientos de inventario
# ----------------------------------------------------------------------

def resumen_movimientos(desde, hasta):
    """
    Movimientos y unidades por clase: 'entrada', 'salida' (manual),
    'venta' (salida generada por una venta) y 'ajuste'.
    """
    return _consultar(
        """
        SELECT CASE
                   WHEN m.tipo = 'salida' AND m.id_venta IS NOT NULL THEN 'venta'
                   ELSE m.tipo
               END AS clase,
               COUNT(*)                       AS movimientos,
               COALESCE(SUM(m.cantidad), 0)   AS unidades
        FROM movimientos_inventario m
        WHERE m.fecha >= ? AND m.fecha < ?
        GROUP BY clase;
        """,
        (desde, hasta),
    )


def serie_movimientos(desde, hasta, formato_grupo):
    """Unidades que entraron y salieron (salidas incluye ventas) por grupo de tiempo."""
    return _consultar(
        """
        SELECT strftime(?, m.fecha) AS grupo,
               COALESCE(SUM(CASE WHEN m.tipo = 'entrada' THEN m.cantidad ELSE 0 END), 0) AS entradas,
               COALESCE(SUM(CASE WHEN m.tipo = 'salida'  THEN m.cantidad ELSE 0 END), 0) AS salidas
        FROM movimientos_inventario m
        WHERE m.fecha >= ? AND m.fecha < ?
        GROUP BY grupo;
        """,
        (formato_grupo, desde, hasta),
    )


def productos_mayor_movimiento(desde, hasta, limite=10):
    return _consultar(
        """
        SELECT p.id_producto, p.codigo, p.nombre, p.existencia,
               COALESCE(SUM(CASE WHEN m.tipo = 'entrada' THEN m.cantidad ELSE 0 END), 0) AS entradas,
               COALESCE(SUM(CASE WHEN m.tipo = 'salida'  THEN m.cantidad ELSE 0 END), 0) AS salidas,
               COALESCE(SUM(m.cantidad), 0) AS total,
               COUNT(*) AS movimientos
        FROM movimientos_inventario m
        JOIN productos p ON p.id_producto = m.id_producto
        WHERE m.fecha >= ? AND m.fecha < ?
        GROUP BY p.id_producto
        ORDER BY total DESC, movimientos DESC
        LIMIT ?;
        """,
        (desde, hasta, limite),
    )


def detalle_operaciones(desde, hasta, limite=5000):
    """
    Todas las operaciones de inventario del periodo, mas recientes primero.
    'operacion' distingue Venta / Entrada / Salida / Ajuste.
    """
    return _consultar(
        """
        SELECT m.id_movimiento, m.fecha,
               CASE
                   WHEN m.tipo = 'salida' AND m.id_venta IS NOT NULL THEN 'venta'
                   ELSE m.tipo
               END AS operacion,
               p.codigo, p.nombre AS producto,
               m.cantidad, m.existencia_anterior, m.existencia_nueva,
               v.numero_venta, v.tipo_pago,
               m.descripcion
        FROM movimientos_inventario m
        JOIN productos p   ON p.id_producto = m.id_producto
        LEFT JOIN ventas v ON v.id_venta = m.id_venta
        WHERE m.fecha >= ? AND m.fecha < ?
        ORDER BY m.fecha DESC, m.id_movimiento DESC
        LIMIT ?;
        """,
        (desde, hasta, limite),
    )


def contar_operaciones_detalle(desde, hasta):
    return _consultar(
        "SELECT COUNT(*) AS total FROM movimientos_inventario m WHERE m.fecha >= ? AND m.fecha < ?;",
        (desde, hasta),
    )[0]["total"]


# ----------------------------------------------------------------------
# Credito
# ----------------------------------------------------------------------

def abonos_periodo(desde, hasta):
    """Abonos recibidos en el periodo (movimientos 'abono' de cuenta de cliente)."""
    return _consultar(
        """
        SELECT COUNT(*) AS abonos, COALESCE(SUM(monto), 0) AS monto
        FROM movimientos_cuenta_cliente
        WHERE tipo = 'abono' AND fecha >= ? AND fecha < ?;
        """,
        (desde, hasta),
    )[0]
