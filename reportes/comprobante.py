"""
Comprobante (estado de cuenta) de un credito en PDF.

Usa las mismas piezas de diseno que el reporte (reportes/pdf.py):
encabezado, pie con numeracion, tablas y colores.
"""

from datetime import datetime
from functools import partial

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from reportes.formato import ETIQUETA_PAGO, dinero, entero, fecha_hora
from reportes.pdf import (
    ANCHO_UTIL, AVISO, BORDE, EXITO, FONDO_ALT, MARGEN_X, PELIGRO, PRIMARIO, PRIMARIO_SUAVE,
    _CanvasNumerado, _estilos, _p, _tabla,
)

_ESTADOS = {"pendiente": ("PENDIENTE", PELIGRO), "parcial": ("PARCIAL", AVISO), "pagado": ("PAGADO", EXITO)}


def generar_comprobante(credito, ruta):
    e = _estilos()
    ahora = datetime.now()
    meta = {
        "titulo_reporte": "Comprobante de crédito",
        "periodo": credito["numero_venta"],
        "pie": f"Generado el {ahora.strftime('%d/%m/%Y')} a las {ahora.strftime('%H:%M')}",
    }
    doc = SimpleDocTemplate(
        ruta, pagesize=A4, leftMargin=MARGEN_X, rightMargin=MARGEN_X,
        topMargin=2.6 * cm, bottomMargin=2.0 * cm,
        title=f"Crédito {credito['numero_venta']}", author="Tienda Jazmín",
    )
    h = []
    texto_estado, color_estado = _ESTADOS[credito["estado_credito"]]

    h.append(_p(f"Estado de crédito {credito['numero_venta']}", e["titulo"]))
    h.append(Paragraph(f"Estado: <font color='{color_estado.hexval().replace('0x', '#')}'><b>{texto_estado}</b></font>",
                       e["subtitulo"]))
    h.append(Spacer(1, 10))

    datos = [
        [_p("Cliente", e["kpi_etiqueta"]), _p(credito["nombre_completo"], e["celda"]),
         _p("Fecha de la venta", e["kpi_etiqueta"]), _p(fecha_hora(credito["fecha"]), e["celda"])],
        [_p("Teléfono", e["kpi_etiqueta"]), _p(credito.get("telefono") or "-", e["celda"]),
         _p("Atendió", e["kpi_etiqueta"]), _p(credito.get("vendedor") or "-", e["celda"])],
    ]
    if credito.get("dui"):
        datos.append([_p("DUI", e["kpi_etiqueta"]), _p(credito["dui"], e["celda"]), "", ""])
    t = Table(datos, colWidths=[3.0 * cm, ANCHO_UTIL / 2 - 3.0 * cm, 3.4 * cm, ANCHO_UTIL / 2 - 3.4 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), FONDO_ALT), ("BOX", (0, 0), (-1, -1), 0.6, BORDE),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    h.append(t)

    # Montos
    celdas = [[_p("Total del crédito", e["kpi_etiqueta"]), _p("Pagado", e["kpi_etiqueta"]),
               _p("Saldo pendiente", e["kpi_etiqueta"])],
              [_p(dinero(credito["total"]), e["kpi_valor"]), _p(dinero(credito["pagado"]), e["kpi_valor"]),
               _p(dinero(credito["saldo"]), e["kpi_valor"])]]
    montos = Table(celdas, colWidths=[ANCHO_UTIL / 3] * 3)
    montos.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, BORDE), ("INNERGRID", (0, 0), (-1, -1), 0, BORDE),
        ("LINEAFTER", (0, 0), (1, -1), 0.6, BORDE),
        ("BACKGROUND", (2, 0), (2, -1), PRIMARIO_SUAVE),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    h.append(Spacer(1, 12))
    h.append(montos)

    # Historial de pagos
    historial = credito["historial"]
    h.append(_p("Historial de pagos", e["seccion"]))
    if historial:
        filas = [[str(i + 1), fecha_hora(pg["fecha"]), ETIQUETA_PAGO.get(pg["metodo_pago"], pg["metodo_pago"] or "Otro"),
                  dinero(pg["monto"]), dinero(pg["saldo_despues"]), pg.get("observacion") or ""]
                 for i, pg in enumerate(historial)]
        filas.append(["", "Total pagado", "", dinero(credito["pagado"]), dinero(credito["saldo"]), ""])
        h.append(_tabla(["#", "Fecha", "Método", "Monto", "Saldo después", "Observación"], filas,
                        [0.9 * cm, 3.3 * cm, 2.3 * cm, 2.6 * cm, 2.9 * cm, ANCHO_UTIL - 12.0 * cm],
                        derecha=(3, 4), estilos=e,
                        resaltar=lambda i: PRIMARIO_SUAVE if i == len(filas) - 1 else None))
    else:
        h.append(_p("Aún no se han registrado pagos para este crédito.", e["vacio"]))

    # Productos
    productos = credito["productos"]
    filas = [[f"{p['codigo']} - {p['nombre']}", entero(p["cantidad"]), dinero(p["precio_unitario"]),
              dinero(p["subtotal"])] for p in productos]
    filas.append(["Total de la venta", "", "", dinero(credito["total"])])
    h.append(KeepTogether([
        _p("Productos de la venta", e["seccion"]),
        _tabla(["Producto", "Cantidad", "Precio", "Subtotal"], filas,
               [ANCHO_UTIL - 8.2 * cm, 2.2 * cm, 2.8 * cm, 3.2 * cm], derecha=(1, 2, 3), estilos=e,
               resaltar=lambda i: PRIMARIO_SUAVE if i == len(filas) - 1 else None),
    ]))

    h.append(Spacer(1, 16))
    if credito["estado_credito"] == "pagado":
        cierre = "Este crédito se encuentra pagado por completo."
    else:
        cierre = (f"Saldo pendiente a la fecha de emisión: {dinero(credito['saldo'])}. "
                  "Este documento refleja los pagos registrados en el sistema hasta ese momento.")
    h.append(_p(cierre, e["nota"]))

    doc.build(h, canvasmaker=partial(_CanvasNumerado, meta=meta))
    return ruta
