"""
Modelo de Estadisticas (NUEVO - agregado junto con la interfaz PySide6).

Solo contiene consultas de LECTURA para los indicadores de la
pantalla de Inicio. No escribe nada en la base de datos ni cambia
tablas, columnas o consultas existentes.

Se agrego como archivo aparte (en lugar de modificar producto.py o
venta.py) para no tocar codigo que ya funciona.
"""

from database.conexion import obtener_conexion


def contar_productos_activos():
    """Cantidad de productos con estado = 1."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM productos WHERE estado = 1;")
    total = cursor.fetchone()["total"]
    conexion.close()
    return total


def resumen_ventas_del_dia():
    """
    Cantidad y monto total (en centavos) de las ventas NO anuladas
    registradas hoy, usando la fecha local igual que el schema
    (datetime('now', 'localtime')).
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT COUNT(*) AS cantidad, COALESCE(SUM(total), 0) AS total,
               COALESCE(SUM(CASE WHEN tipo_pago <> 'credito' THEN total ELSE 0 END), 0) AS contado
        FROM ventas
        WHERE estado = 1
          AND date(fecha) = date('now', 'localtime');
        """
    )
    fila = cursor.fetchone()
    # Pagos de creditos recibidos hoy (tabla pagos, columna id_venta de la migracion).
    cursor.execute(
        """
        SELECT COALESCE(SUM(monto), 0) AS cobros FROM pagos
        WHERE id_venta IS NOT NULL AND date(fecha) = date('now', 'localtime');
        """
    )
    cobros = cursor.fetchone()["cobros"]
    # Saldo que TODAVIA falta cobrar de las ventas a credito hechas hoy
    # (total de esas ventas menos lo que ya se ha pagado de ellas).
    cursor.execute(
        """
        SELECT COALESCE(SUM(v.total - COALESCE(p.pagado, 0)), 0) AS pendiente
        FROM ventas v
        LEFT JOIN (SELECT id_venta, SUM(monto) AS pagado FROM pagos
                   WHERE id_venta IS NOT NULL GROUP BY id_venta) p ON p.id_venta = v.id_venta
        WHERE v.estado = 1 AND v.tipo_pago = 'credito'
          AND date(v.fecha) = date('now', 'localtime');
        """
    )
    credito_pendiente = cursor.fetchone()["pendiente"]
    conexion.close()
    return {"cantidad": fila["cantidad"], "total": fila["total"],
            "contado": fila["contado"], "credito": fila["total"] - fila["contado"],
            "credito_pendiente": credito_pendiente,
            "cobros": cobros, "recibido": fila["contado"] + cobros}


def resumen_credito_pendiente():
    """
    Suma de los saldos pendientes (en centavos) de los clientes
    activos que deben algo, y cuantos clientes son.

    El saldo se calcula igual que en movimiento_cuenta_cliente
    (cargos menos abonos), nunca desde un campo guardado.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT COUNT(*) AS clientes, COALESCE(SUM(saldo), 0) AS total
        FROM (
            SELECT m.id_cliente,
                   SUM(CASE WHEN m.tipo = 'cargo' THEN m.monto ELSE -m.monto END) AS saldo
            FROM movimientos_cuenta_cliente m
            JOIN clientes c ON c.id_cliente = m.id_cliente
            WHERE c.estado = 1
            GROUP BY m.id_cliente
            HAVING saldo > 0
        );
        """
    )
    fila = cursor.fetchone()
    conexion.close()
    return {"clientes": fila["clientes"], "total": fila["total"]}
