"""
Controlador de Reportes (NUEVO).

Arma el reporte completo de un periodo a partir de models/reportes.py
y de funciones que ya existian (productos activos, stock bajo, saldo
pendiente). La pantalla y el PDF usan EXACTAMENTE el mismo diccionario,
asi lo que se ve y lo que se imprime siempre coinciden.
"""

from datetime import datetime
import traceback

from helpers import sesion
from models import credito, estadisticas, movimiento_inventario, reportes as consultas
from reportes import resumen
from reportes.formato import ORDEN_PAGO
from reportes.periodos import crear_periodo


def _por_clase(filas):
    datos = {f["clase"]: f for f in filas}
    def valor(clase, campo):
        return datos.get(clase, {}).get(campo, 0) or 0
    return valor


def construir_reporte(periodo):
    """Consulta la base y devuelve el diccionario del reporte (puede lanzar excepciones)."""
    desde, hasta = periodo.desde_sql, periodo.hasta_sql

    ventas = consultas.resumen_ventas(desde, hasta)
    movimientos = _por_clase(consultas.resumen_movimientos(desde, hasta))
    stock_bajo = [dict(f) for f in movimiento_inventario.listar_productos_stock_bajo()]

    cobros = credito.resumen_cobros(desde, hasta)

    anterior_periodo = periodo.anterior()
    anterior = consultas.resumen_ventas(anterior_periodo.desde_sql, anterior_periodo.hasta_sql)
    cobros_anterior = credito.resumen_cobros(anterior_periodo.desde_sql, anterior_periodo.hasta_sql)

    # VENTAS = valor de lo vendido. DINERO RECIBIDO = ventas al contado + cobros
    # de creditos. Una venta a credito no es dinero recibido hasta que se paga.
    contado = ventas["ingresos"] - ventas["monto_credito"]
    indicadores = {
        "productos_activos": estadisticas.contar_productos_activos(),
        "ventas": ventas["ventas"],
        "monto_ventas": ventas["ingresos"],
        "unidades_vendidas": ventas["unidades"],
        "ticket_promedio": (ventas["ingresos"] // ventas["ventas"]) if ventas["ventas"] else 0,
        "ventas_contado": ventas["ventas"] - ventas["ventas_credito"],
        "monto_contado": contado,
        "ventas_credito": ventas["ventas_credito"],
        "monto_credito": ventas["monto_credito"],
        "cobros": cobros["pagos"],
        "monto_cobros": cobros["monto"],
        "dinero_recibido": contado + cobros["monto"],
        "entradas": movimientos("entrada", "unidades"),
        "entradas_mov": movimientos("entrada", "movimientos"),
        "salidas": movimientos("salida", "unidades"),
        "salidas_mov": movimientos("salida", "movimientos"),
        "salidas_por_venta": movimientos("venta", "unidades"),
        "ajustes_mov": movimientos("ajuste", "movimientos"),
        "stock_bajo": len(stock_bajo),
    }
    # Operaciones = ventas + entradas + salidas manuales + ajustes
    # (las salidas por venta ya estan contadas dentro de cada venta).
    # Un cobro de credito tambien es una operacion (no es una venta nueva).
    indicadores["operaciones"] = (indicadores["ventas"] + indicadores["entradas_mov"]
                                  + indicadores["salidas_mov"] + indicadores["ajustes_mov"]
                                  + indicadores["cobros"])

    # --- Series de tiempo con todos los grupos (incluidos los vacios) ---
    grupos = periodo.grupos()
    serie_v = {f["grupo"]: f for f in consultas.serie_ventas(desde, hasta, periodo.formato_grupo_sql)}
    serie_m = {f["grupo"]: f for f in consultas.serie_movimientos(desde, hasta, periodo.formato_grupo_sql)}
    serie_c = {f["grupo"]: f["monto"] for f in credito.serie_cobros(desde, hasta, periodo.formato_grupo_sql)}
    series = {
        "etiquetas": [etiqueta for _, etiqueta in grupos],
        "ventas_monto": [serie_v.get(clave, {}).get("monto", 0) for clave, _ in grupos],
        "ventas_cantidad": [serie_v.get(clave, {}).get("ventas", 0) for clave, _ in grupos],
        "recibido": [serie_v.get(clave, {}).get("monto_contado", 0) + serie_c.get(clave, 0)
                     for clave, _ in grupos],
        "entradas": [serie_m.get(clave, {}).get("entradas", 0) for clave, _ in grupos],
        "salidas": [serie_m.get(clave, {}).get("salidas", 0) for clave, _ in grupos],
        "unidad": periodo.unidad_grupo,
    }

    metodos_db = {f["tipo_pago"]: f for f in consultas.ventas_por_metodo(desde, hasta)}
    metodos = [
        {"tipo_pago": clave,
         "ventas": metodos_db.get(clave, {}).get("ventas", 0),
         "monto": metodos_db.get(clave, {}).get("monto", 0)}
        for clave in ORDEN_PAGO
    ]

    detalle = consultas.detalle_operaciones(desde, hasta)
    total_detalle = consultas.contar_operaciones_detalle(desde, hasta)

    usuario = sesion.obtener_usuario_actual() or {}
    reporte = {
        "periodo": periodo,
        "generado": datetime.now(),
        "generado_por": usuario.get("nombre", ""),
        "indicadores": indicadores,
        "anterior": {
            "ventas": anterior["ventas"],
            "monto_ventas": anterior["ingresos"],
            "dinero_recibido": anterior["ingresos"] - anterior["monto_credito"] + cobros_anterior["monto"],
        },
        "series": series,
        "metodos": metodos,
        "mas_vendidos": consultas.productos_mas_vendidos(desde, hasta, 10),
        "mayor_movimiento": consultas.productos_mayor_movimiento(desde, hasta, 10),
        "stock_bajo": stock_bajo,
        "credito": _resumen_credito(desde, hasta, ventas),
        "detalle": detalle,
        "detalle_total": total_detalle,
    }
    reporte["vacio"] = indicadores["operaciones"] == 0
    reporte["resumen"] = resumen.redactar(reporte)
    return reporte


def _resumen_credito(desde, hasta, ventas):
    """Creditos otorgados en el periodo (con su estado de hoy) y cobros recibidos en el periodo."""
    creditos = credito.listar_creditos()
    del_periodo = [c for c in creditos if desde <= c["fecha"] < hasta]
    todos_activos = [c for c in creditos if c["estado_credito"] != "pagado"]
    return {
        "ventas": ventas["ventas_credito"],
        "monto": ventas["monto_credito"],
        "otorgados": len(del_periodo),
        "estados": {e: sum(1 for c in del_periodo if c["estado_credito"] == e)
                    for e in ("pendiente", "parcial", "pagado")},
        "saldo_de_otorgados": sum(c["saldo"] for c in del_periodo),
        "cobros": credito.resumen_cobros(desde, hasta),
        "cobros_por_metodo": credito.cobros_por_metodo(desde, hasta),
        "pagos": credito.listar_pagos_periodo(desde, hasta),
        "activos_hoy": len(todos_activos),
        "pendiente_actual": {"total": sum(c["saldo"] for c in todos_activos),
                             "clientes": len({c["id_cliente"] for c in todos_activos})},
    }


def generar_reporte(tipo, fecha):
    """
    Devuelve (exito, mensaje, reporte). Nunca deja pasar errores tecnicos
    a la pantalla: si algo falla se devuelve un mensaje entendible.
    """
    try:
        periodo = crear_periodo(tipo, fecha)
        return True, "", construir_reporte(periodo)
    except Exception as error:
        traceback.print_exc()
        return False, f"No se pudo consultar la información del período ({error}).", None


def exportar_pdf(reporte, ruta):
    """Genera el PDF del reporte ya consultado. Devuelve (exito, mensaje)."""
    try:
        from reportes.pdf import generar_pdf
    except ModuleNotFoundError as error:
        if not (error.name or "").startswith("reportlab"):
            raise
        return False, ("Falta la biblioteca ReportLab para crear PDF. "
                       "Instálala con:  uv pip install --python .venv reportlab")
    try:
        generar_pdf(reporte, ruta)
        return True, f"Reporte guardado en {ruta}"
    except PermissionError:
        return False, ("No se pudo guardar el archivo. Si ese PDF está abierto en otro "
                       "programa, ciérralo o elige otro nombre.")
    except Exception as error:
        traceback.print_exc()
        return False, f"No se pudo generar el PDF ({error})."
