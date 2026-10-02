"""
Generacion del reporte en PDF con ReportLab.

Recibe el mismo diccionario que muestra la pantalla de Reportes
(controlador_reportes.construir_reporte), asi el PDF y la pantalla
siempre coinciden.

Caracteristicas:
  - Encabezado y pie en todas las paginas, con "Pagina X de Y".
  - Tablas que continuan en la pagina siguiente repitiendo su encabezado.
  - Graficos vectoriales (se ven nitidos al imprimir o hacer zoom).
  - Usa Segoe UI o Arial si existen (Windows); si no, Helvetica.
"""

import math
import os
from functools import partial

from reportlab.graphics.charts.barcharts import HorizontalBarChart, VerticalBarChart
from reportlab.graphics.charts.doughnut import Doughnut
from reportlab.graphics.shapes import Drawing, Ellipse, Circle, Group, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from reportes.formato import (
    ETIQUETA_OPERACION, ETIQUETA_PAGO, dinero, entero, fecha_hora_corta, plural, variacion,
)

# ----------------------------------------------------------------------
# Colores (mismos tonos que la interfaz, ui/theme.py)
# ----------------------------------------------------------------------
PRIMARIO = colors.HexColor("#12695F")
PRIMARIO_SUAVE = colors.HexColor("#E2F0ED")
TEXTO = colors.HexColor("#1B2624")
TEXTO_SUAVE = colors.HexColor("#5E6B68")
TEXTO_TENUE = colors.HexColor("#95A09D")
BORDE = colors.HexColor("#DFE5E3")
FONDO_ALT = colors.HexColor("#F7F9F8")
EXITO = colors.HexColor("#2B7A4B")
INFO = colors.HexColor("#2E68AE")
AVISO = colors.HexColor("#A86A12")
PELIGRO = colors.HexColor("#BE3A2E")
AVISO_SUAVE = colors.HexColor("#FDF7EC")
VENTAS_CLARO = colors.HexColor("#8FC7BE")   # ventas (claro) vs. dinero recibido (PRIMARIO)

COLORES_PAGO = {
    "efectivo": colors.HexColor("#12695F"),
    "tarjeta": colors.HexColor("#2E68AE"),
    "otro": colors.HexColor("#95A09D"),
    "credito": colors.HexColor("#A86A12"),
}

MAX_FILAS_DETALLE = 500
MARGEN_X = 1.8 * cm
ANCHO_UTIL = A4[0] - 2 * MARGEN_X


# ----------------------------------------------------------------------
# Tipografia
# ----------------------------------------------------------------------

def _registrar_fuentes():
    """Devuelve (normal, negrita). Prueba fuentes del sistema con soporte completo de acentos."""
    carpetas = [os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts"),
                "/usr/share/fonts/truetype/dejavu", "/Library/Fonts"]
    candidatas = [("segoeui.ttf", "segoeuib.ttf", "SegoeUI"),
                  ("arial.ttf", "arialbd.ttf", "Arial"),
                  ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans")]
    for normal, negrita, nombre in candidatas:
        for carpeta in carpetas:
            ruta_n, ruta_b = os.path.join(carpeta, normal), os.path.join(carpeta, negrita)
            if os.path.exists(ruta_n) and os.path.exists(ruta_b):
                try:
                    if nombre not in pdfmetrics.getRegisteredFontNames():
                        pdfmetrics.registerFont(TTFont(nombre, ruta_n))
                        pdfmetrics.registerFont(TTFont(nombre + "-Bold", ruta_b))
                        # Para que <b> dentro de un parrafo use la variante negrita.
                        pdfmetrics.registerFontFamily(nombre, normal=nombre, bold=nombre + "-Bold",
                                           italic=nombre, boldItalic=nombre + "-Bold")
                    return nombre, nombre + "-Bold"
                except Exception:
                    continue
    return "Helvetica", "Helvetica-Bold"


FUENTE, FUENTE_B = _registrar_fuentes()


def _estilos():
    return {
        "titulo": ParagraphStyle("titulo", fontName=FUENTE_B, fontSize=20, leading=25,
                                 textColor=TEXTO, spaceAfter=4),
        "subtitulo": ParagraphStyle("subtitulo", fontName=FUENTE, fontSize=11, leading=15,
                                    textColor=TEXTO_SUAVE),
        "seccion": ParagraphStyle("seccion", fontName=FUENTE_B, fontSize=13.5, leading=18,
                                  textColor=PRIMARIO, spaceBefore=16, spaceAfter=8),
        "cuerpo": ParagraphStyle("cuerpo", fontName=FUENTE, fontSize=10, leading=15, textColor=TEXTO),
        "nota": ParagraphStyle("nota", fontName=FUENTE, fontSize=8.5, leading=12, textColor=TEXTO_SUAVE),
        "celda": ParagraphStyle("celda", fontName=FUENTE, fontSize=8.8, leading=11.5, textColor=TEXTO),
        "celda_der": ParagraphStyle("celda_der", fontName=FUENTE, fontSize=8.8, leading=11.5,
                                    textColor=TEXTO, alignment=TA_RIGHT),
        "encabezado": ParagraphStyle("encabezado", fontName=FUENTE_B, fontSize=8.5, leading=11,
                                     textColor=colors.white),
        "encabezado_der": ParagraphStyle("encabezado_der", fontName=FUENTE_B, fontSize=8.5, leading=11,
                                         textColor=colors.white, alignment=TA_RIGHT),
        "kpi_etiqueta": ParagraphStyle("kpi_etiqueta", fontName=FUENTE, fontSize=8.5, leading=11,
                                       textColor=TEXTO_SUAVE),
        "kpi_valor": ParagraphStyle("kpi_valor", fontName=FUENTE_B, fontSize=15, leading=19, textColor=TEXTO),
        "kpi_detalle": ParagraphStyle("kpi_detalle", fontName=FUENTE, fontSize=7.8, leading=10,
                                      textColor=TEXTO_SUAVE),
        "vacio": ParagraphStyle("vacio", fontName=FUENTE, fontSize=9.5, leading=13, textColor=TEXTO_SUAVE,
                                alignment=TA_LEFT),
    }


def _p(texto, estilo):
    """Paragraph con el texto escapado (evita que un '&' o '<' en un nombre rompa el PDF)."""
    texto = "" if texto is None else str(texto)
    texto = texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(texto, estilo)


# ----------------------------------------------------------------------
# Encabezado, pie y numeracion de paginas
# ----------------------------------------------------------------------

def _dibujar_logo(c, x, y, tam):
    """Flor de cinco petalos (misma marca que la aplicacion)."""
    grupo = Group()
    r = tam / 2
    for angulo in (0, 72, 144, 216, 288):
        petalo = Ellipse(0, r * 0.47, r * 0.28, r * 0.43, fillColor=PRIMARIO, strokeColor=None)
        g = Group(petalo)
        g.rotate(angulo)
        grupo.add(g)
    grupo.add(Circle(0, 0, r * 0.2, fillColor=colors.white, strokeColor=None))
    grupo.translate(r, r)
    dibujo = Drawing(tam, tam)
    dibujo.add(grupo)
    dibujo.drawOn(c, x, y)


class _CanvasNumerado(canvas.Canvas):
    """Canvas que conoce el total de paginas para escribir 'Pagina X de Y'."""

    def __init__(self, *args, meta=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._paginas = []
        self._meta = meta or {}

    def showPage(self):
        self._paginas.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._paginas)
        for estado in self._paginas:
            self.__dict__.update(estado)
            self._decorar(total)
            super().showPage()
        super().save()

    def _decorar(self, total):
        ancho, alto = A4
        m = self._meta
        # --- Encabezado ---
        y = alto - 1.45 * cm
        _dibujar_logo(self, MARGEN_X, y - 0.2 * cm, 0.75 * cm)
        self.setFillColor(TEXTO)
        self.setFont(FUENTE_B, 10.5)
        self.drawString(MARGEN_X + 0.95 * cm, y + 0.18 * cm, "Tienda Jazmín")
        self.setFont(FUENTE, 8)
        self.setFillColor(TEXTO_SUAVE)
        self.drawString(MARGEN_X + 0.95 * cm, y - 0.2 * cm, "Sistema de inventario")
        self.setFont(FUENTE, 8.5)
        self.drawRightString(ancho - MARGEN_X, y + 0.18 * cm, m.get("titulo_reporte", ""))
        self.drawRightString(ancho - MARGEN_X, y - 0.2 * cm, m.get("periodo", ""))
        self.setStrokeColor(PRIMARIO)
        self.setLineWidth(1.2)
        self.line(MARGEN_X, y - 0.45 * cm, ancho - MARGEN_X, y - 0.45 * cm)

        # --- Pie ---
        self.setStrokeColor(BORDE)
        self.setLineWidth(0.6)
        self.line(MARGEN_X, 1.45 * cm, ancho - MARGEN_X, 1.45 * cm)
        self.setFont(FUENTE, 8)
        self.setFillColor(TEXTO_SUAVE)
        self.drawString(MARGEN_X, 1.0 * cm, m.get("pie", ""))
        self.drawRightString(ancho - MARGEN_X, 1.0 * cm, f"Página {self._pageNumber} de {total}")


# ----------------------------------------------------------------------
# Tablas
# ----------------------------------------------------------------------

def _tabla(encabezados, filas, anchos, derecha=(), resaltar=None, estilos=None):
    """
    Tabla con encabezado verde que se repite en cada pagina.
    derecha: indices de columnas alineadas a la derecha (numeros).
    resaltar: funcion indice_fila -> color de fondo o None.
    """
    e = estilos
    datos = [[_p(t, e["encabezado_der"] if i in derecha else e["encabezado"])
              for i, t in enumerate(encabezados)]]
    for fila in filas:
        datos.append([_p(v, e["celda_der"] if i in derecha else e["celda"]) for i, v in enumerate(fila)])

    tabla = Table(datos, colWidths=anchos, repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARIO),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, BORDE),
        ("BOX", (0, 0), (-1, -1), 0.6, BORDE),
    ]
    for i in range(1, len(datos)):
        fondo = resaltar(i - 1) if resaltar else None
        if fondo is not None:
            estilo.append(("BACKGROUND", (0, i), (-1, i), fondo))
        elif i % 2 == 0:
            estilo.append(("BACKGROUND", (0, i), (-1, i), FONDO_ALT))
    tabla.setStyle(TableStyle(estilo))
    return tabla


def _indicadores(reporte, e):
    ind = reporte["indicadores"]
    ant = reporte["anterior"]
    tarjetas = [
        ("Ventas totales", dinero(ind["monto_ventas"]), plural(ind["ventas"], "venta", "ventas")),
        ("Ventas al contado", dinero(ind["monto_contado"]), plural(ind["ventas_contado"], "venta", "ventas")),
        ("Ventas a crédito", dinero(ind["monto_credito"]), plural(ind["ventas_credito"], "venta", "ventas")),
        ("Cobros de créditos", dinero(ind["monto_cobros"]), plural(ind["cobros"], "pago", "pagos")),
        ("Dinero recibido", dinero(ind["dinero_recibido"]),
         variacion(ind["dinero_recibido"], ant["dinero_recibido"]).replace("sin ventas", "sin ingresos")),
        ("Entradas (unidades)", entero(ind["entradas"]), plural(ind["entradas_mov"], "movimiento", "movimientos")),
        ("Salidas manuales (unidades)", entero(ind["salidas"]),
         plural(ind["salidas_mov"], "movimiento", "movimientos") + ", sin contar ventas"),
        ("Stock bajo", entero(ind["stock_bajo"]),
         f"de {entero(ind['productos_activos'])} productos activos (situación actual)"),
    ]
    celdas = []
    for etiqueta, valor, detalle in tarjetas:
        celdas.append([_p(etiqueta, e["kpi_etiqueta"]), _p(valor, e["kpi_valor"]), _p(detalle, e["kpi_detalle"])])

    ancho = ANCHO_UTIL / 4
    filas = []
    for i in range(0, 8, 4):
        filas.append([Table([[c[0]], [c[1]], [c[2]]], colWidths=[ancho - 0.5 * cm],
                            style=[("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                   ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)])
                      for c in celdas[i:i + 4]])
    tabla = Table(filas, colWidths=[ancho] * 4)
    tabla.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, BORDE),
        ("INNERGRID", (0, 0), (-1, -1), 0.6, BORDE),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BACKGROUND", (0, 1), (0, 1), PRIMARIO_SUAVE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return tabla


# ----------------------------------------------------------------------
# Graficos
# ----------------------------------------------------------------------

def _paso_bonito(maximo, divisiones=4):
    if maximo <= 0:
        return 1
    bruto = maximo / divisiones
    magnitud = 10 ** math.floor(math.log10(bruto))
    for factor in (1, 2, 2.5, 5, 10):
        if bruto <= factor * magnitud:
            return factor * magnitud
    return 10 * magnitud


def _etiquetas_espaciadas(etiquetas, maximo=16):
    if len(etiquetas) <= maximo:
        return list(etiquetas)
    salto = math.ceil(len(etiquetas) / maximo)
    return [t if i % salto == 0 else "" for i, t in enumerate(etiquetas)]


def _vacio(texto, ancho, alto=2.2 * cm):
    d = Drawing(ancho, alto)
    d.add(Rect(0, 0, ancho, alto, fillColor=FONDO_ALT, strokeColor=BORDE, strokeWidth=0.6, rx=6, ry=6))
    d.add(String(ancho / 2, alto / 2 - 3, texto, fontName=FUENTE, fontSize=9,
                 fillColor=TEXTO_SUAVE, textAnchor="middle"))
    return d


def _grafico_barras(etiquetas, series, colores_series, ancho, alto, formato=None, leyenda=None):
    maximo = max((max(s) for s in series if s), default=0)
    if maximo <= 0:
        return None
    d = Drawing(ancho, alto)
    alto_leyenda = 16 if leyenda else 0
    bc = VerticalBarChart()
    bc.x, bc.y = 46, 26
    bc.width, bc.height = ancho - 56, alto - 36 - alto_leyenda
    bc.data = [list(s) for s in series]
    bc.strokeColor = None
    paso = _paso_bonito(maximo)
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = paso * math.ceil(maximo / paso)
    bc.valueAxis.valueStep = paso
    bc.valueAxis.visibleGrid = True
    bc.valueAxis.gridStrokeColor = BORDE
    bc.valueAxis.gridStrokeWidth = 0.5
    bc.valueAxis.strokeColor = None
    bc.valueAxis.labels.fontName = FUENTE
    bc.valueAxis.labels.fontSize = 7
    bc.valueAxis.labels.fillColor = TEXTO_SUAVE
    if formato:
        bc.valueAxis.labelTextFormat = formato
    bc.categoryAxis.categoryNames = _etiquetas_espaciadas(etiquetas)
    bc.categoryAxis.labels.fontName = FUENTE
    bc.categoryAxis.labels.fontSize = 7
    bc.categoryAxis.labels.fillColor = TEXTO_SUAVE
    bc.categoryAxis.labels.dy = -4
    bc.categoryAxis.strokeColor = BORDE
    bc.categoryAxis.tickDown = 0
    bc.groupSpacing = 3 if len(etiquetas) > 20 else 6
    bc.barSpacing = 1
    for i, color in enumerate(colores_series):
        bc.bars[i].fillColor = color
        bc.bars[i].strokeColor = None
    d.add(bc)
    if leyenda:
        x = bc.x
        for (texto, color) in leyenda:
            d.add(Rect(x, alto - 11, 9, 9, fillColor=color, strokeColor=None, rx=2, ry=2))
            d.add(String(x + 13, alto - 9.5, texto, fontName=FUENTE, fontSize=8, fillColor=TEXTO))
            x += 13 + pdfmetrics.stringWidth(texto, FUENTE, 8) + 18
    return d


def _grafico_horizontal(nombres, valores, ancho, color=PRIMARIO, formato=None):
    if not valores or max(valores) <= 0:
        return None
    filas = len(valores)
    alto = 24 + filas * 20
    d = Drawing(ancho, alto)
    margen_nombres = min(150, ancho * 0.38)
    hb = HorizontalBarChart()
    hb.x, hb.y = margen_nombres, 14
    hb.width, hb.height = ancho - margen_nombres - 40, alto - 22
    hb.data = [list(reversed(valores))]
    hb.categoryAxis.categoryNames = [n if len(n) <= 30 else n[:29] + "…" for n in reversed(nombres)]
    hb.categoryAxis.labels.fontName = FUENTE
    hb.categoryAxis.labels.fontSize = 8
    hb.categoryAxis.labels.fillColor = TEXTO
    hb.categoryAxis.labels.dx = -4
    hb.categoryAxis.strokeColor = BORDE
    hb.categoryAxis.tickLeft = 0
    hb.valueAxis.valueMin = 0
    paso = _paso_bonito(max(valores))
    hb.valueAxis.valueMax = paso * math.ceil(max(valores) / paso)
    hb.valueAxis.valueStep = paso
    hb.valueAxis.labels.fontName = FUENTE
    hb.valueAxis.labels.fontSize = 7
    hb.valueAxis.labels.fillColor = TEXTO_SUAVE
    hb.valueAxis.visibleGrid = True
    hb.valueAxis.gridStrokeColor = BORDE
    hb.valueAxis.strokeColor = None
    if formato:
        hb.valueAxis.labelTextFormat = formato
    hb.bars[0].fillColor = color
    hb.bars[0].strokeColor = None
    hb.barLabelFormat = "%d"
    hb.barLabels.fontName = FUENTE
    hb.barLabels.fontSize = 7.5
    hb.barLabels.fillColor = TEXTO_SUAVE
    hb.barLabels.boxAnchor = "w"
    hb.barLabels.dx = 3
    d.add(hb)
    return d


def _grafico_dona(metodos, ancho, alto):
    partes = [m for m in metodos if m["monto"] > 0]
    total = sum(m["monto"] for m in partes)
    if total <= 0:
        return None
    d = Drawing(ancho, alto)
    diametro = min(alto - 10, ancho * 0.45)
    dona = Doughnut()
    dona.x, dona.y = 4, (alto - diametro) / 2
    dona.width = dona.height = diametro
    dona.data = [m["monto"] for m in partes]
    dona.labels = None
    dona.innerRadiusFraction = 0.58
    dona.strokeColor = colors.white
    dona.strokeWidth = 1.5
    for i, m in enumerate(partes):
        dona.slices[i].fillColor = COLORES_PAGO.get(m["tipo_pago"], TEXTO_TENUE)
        dona.slices[i].strokeColor = colors.white
    d.add(dona)
    x = diametro + 20
    y = alto / 2 + (len(partes) * 26) / 2 - 14
    for m in partes:
        color = COLORES_PAGO.get(m["tipo_pago"], TEXTO_TENUE)
        porcentaje = m["monto"] / total * 100
        d.add(Rect(x, y, 9, 9, fillColor=color, strokeColor=None, rx=2, ry=2))
        d.add(String(x + 14, y + 1, f"{ETIQUETA_PAGO.get(m['tipo_pago'], m['tipo_pago'])}  {porcentaje:.0f}%",
                     fontName=FUENTE_B, fontSize=8.5, fillColor=TEXTO))
        d.add(String(x + 14, y - 10, f"{dinero(m['monto'])} en {plural(m['ventas'], 'venta', 'ventas')}",
                     fontName=FUENTE, fontSize=7.5, fillColor=TEXTO_SUAVE))
        y -= 26
    return d


def _formato_dinero_eje(valor):
    centavos = valor
    if centavos >= 100_000_00:
        return f"${centavos / 100_000:.0f}k"
    return f"${centavos / 100:,.0f}"


# ----------------------------------------------------------------------
# Documento
# ----------------------------------------------------------------------

def generar_pdf(reporte, ruta):
    e = _estilos()
    periodo = reporte["periodo"]
    ind = reporte["indicadores"]
    generado = reporte["generado"]
    fecha_gen = generado.strftime("%d/%m/%Y")
    hora_gen = generado.strftime("%H:%M")

    meta = {
        "titulo_reporte": f"Reporte {periodo.etiqueta_tipo.lower()}",
        "periodo": periodo.titulo,
        "pie": f"Generado el {fecha_gen} a las {hora_gen}"
               + (f" por {reporte['generado_por']}" if reporte.get("generado_por") else ""),
    }

    doc = SimpleDocTemplate(
        ruta, pagesize=A4,
        leftMargin=MARGEN_X, rightMargin=MARGEN_X, topMargin=2.6 * cm, bottomMargin=2.0 * cm,
        title=f"Reporte de inventario - {periodo.titulo}",
        author="Tienda Jazmín", subject="Reporte de inventario y operaciones",
    )

    h = []  # historia (contenido del documento)

    # --- Portada / datos del reporte ---
    h.append(_p("Reporte de inventario y operaciones", e["titulo"]))
    h.append(_p(periodo.titulo, e["subtitulo"]))
    h.append(Spacer(1, 10))
    datos = Table(
        [[_p("Tipo de período", e["kpi_etiqueta"]), _p(periodo.etiqueta_tipo, e["celda"]),
          _p("Rango analizado", e["kpi_etiqueta"]), _p(periodo.rango_texto, e["celda"])],
         [_p("Fecha de generación", e["kpi_etiqueta"]), _p(f"{fecha_gen} {hora_gen}", e["celda"]),
          _p("Generado por", e["kpi_etiqueta"]), _p(reporte.get("generado_por") or "-", e["celda"])]],
        colWidths=[3.3 * cm, ANCHO_UTIL / 2 - 3.3 * cm, 3.1 * cm, ANCHO_UTIL / 2 - 3.1 * cm],
    )
    datos.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), FONDO_ALT),
        ("BOX", (0, 0), (-1, -1), 0.6, BORDE),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    h.append(datos)

    # --- Indicadores ---
    h.append(_p("Resumen de indicadores", e["seccion"]))
    h.append(_indicadores(reporte, e))

    # --- Resumen textual ---
    caja = Table([[_p(reporte["resumen"], e["cuerpo"])]], colWidths=[ANCHO_UTIL])
    caja.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PRIMARIO_SUAVE),
        ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    h.append(KeepTogether([_p("Resumen del período", e["seccion"]), caja]))

    series = reporte["series"]

    # --- Grafico de ventas ---
    grafico = _grafico_barras(series["etiquetas"], [series["ventas_monto"], series["recibido"]],
                              [VENTAS_CLARO, PRIMARIO], ANCHO_UTIL, 6.6 * cm, formato=_formato_dinero_eje,
                              leyenda=[("Ventas", VENTAS_CLARO), ("Dinero recibido", PRIMARIO)])
    h.append(KeepTogether([
        _p("Ventas y dinero recibido", e["seccion"]),
        _p(f"Por {series['unidad']}. Dinero recibido = ventas al contado + cobros de créditos; "
           "una venta a crédito cuenta como recibida solo cuando el cliente paga.", e["nota"]),
        Spacer(1, 6),
        grafico or _vacio("No hay ventas ni cobros registrados en este período.", ANCHO_UTIL),
    ]))

    # --- Entradas vs salidas + metodos de pago ---
    mitad = ANCHO_UTIL / 2 - 0.3 * cm
    g_mov = _grafico_barras(series["etiquetas"], [series["entradas"], series["salidas"]],
                            [EXITO, INFO], mitad, 5.6 * cm,
                            leyenda=[("Entradas", EXITO), ("Salidas (incluye ventas)", INFO)])
    g_pago = _grafico_dona(reporte["metodos"], mitad, 5.6 * cm)
    fila_graficos = Table(
        [[_p("Entradas vs. salidas (unidades)", e["kpi_etiqueta"]), _p("Ventas por método de pago", e["kpi_etiqueta"])],
         [g_mov or _vacio("Sin movimientos de inventario.", mitad),
          g_pago or _vacio("Sin ventas en el período.", mitad)]],
        colWidths=[ANCHO_UTIL / 2, ANCHO_UTIL / 2],
    )
    fila_graficos.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
    ]))
    h.append(KeepTogether([_p("Movimiento de inventario y formas de pago", e["seccion"]), fila_graficos]))

    # --- Productos mas vendidos ---
    top = reporte["mas_vendidos"]
    bloque = [_p("Productos más vendidos", e["seccion"])]
    if top:
        g_top = _grafico_horizontal([t["nombre"] for t in top], [t["unidades"] for t in top], ANCHO_UTIL)
        if g_top:
            bloque += [g_top, Spacer(1, 8)]
        total_ingresos = ind["monto_ventas"] or 1
        filas = [[str(i + 1), t["codigo"], t["nombre"], entero(t["unidades"]), dinero(t["ingresos"]),
                  f"{t['ingresos'] / total_ingresos * 100:.1f}%"] for i, t in enumerate(top)]
        bloque.append(_tabla(["#", "Código", "Producto", "Unidades", "Vendido", "% del total"], filas,
                             [1.0 * cm, 2.4 * cm, ANCHO_UTIL - 10.6 * cm, 2.2 * cm, 2.6 * cm, 2.4 * cm],
                             derecha=(3, 4, 5), estilos=e))
    else:
        bloque.append(_p("No hubo ventas en este período.", e["vacio"]))
    h.append(KeepTogether(bloque[:3]) if len(bloque) > 3 else KeepTogether(bloque))
    h.extend(bloque[3:])

    # --- Ventas y cobros ---
    cred = reporte["credito"]
    filas_vc = [
        ["Ventas al contado", entero(ind["ventas_contado"]), dinero(ind["monto_contado"])],
        ["Ventas a crédito", entero(ind["ventas_credito"]), dinero(ind["monto_credito"])],
        ["Ventas totales", entero(ind["ventas"]), dinero(ind["monto_ventas"])],
        ["Cobros de créditos", entero(ind["cobros"]), dinero(ind["monto_cobros"])],
        ["Dinero recibido (contado + cobros)", "", dinero(ind["dinero_recibido"])],
        ["Saldo generado por ventas a crédito", "", dinero(ind["monto_credito"])],
    ]
    t_vc = _tabla(["Concepto", "Cantidad", "Monto"], filas_vc,
                  [ANCHO_UTIL - 7 * cm, 3 * cm, 4 * cm], derecha=(1, 2), estilos=e,
                  resaltar=lambda i: PRIMARIO_SUAVE if i in (2, 4) else None)
    lineas = (
        f"Unidades vendidas: <b>{entero(ind['unidades_vendidas'])}</b>. "
        f"Ticket promedio: <b>{dinero(ind['ticket_promedio'])}</b>. "
    )
    if cred["otorgados"]:
        est = cred["estados"]
        lineas += (
            f"De los <b>{entero(cred['otorgados'])}</b> créditos otorgados en el período, hoy "
            f"{plural(est['pendiente'], 'está pendiente', 'están pendientes')}, "
            f"{plural(est['parcial'], 'tiene pago parcial', 'tienen pago parcial')} y "
            f"{plural(est['pagado'], 'está pagado', 'están pagados')} "
            f"(saldo por cobrar de esos créditos: <b>{dinero(cred['saldo_de_otorgados'])}</b>). "
        )
    lineas += (f"Saldo pendiente total hoy: <b>{dinero(cred['pendiente_actual']['total'])}</b> en "
               f"{plural(cred['activos_hoy'], 'crédito activo', 'créditos activos')}.")
    h.append(KeepTogether([_p("Ventas y cobros", e["seccion"]), t_vc, Spacer(1, 8), Paragraph(lineas, e["cuerpo"])]))

    total_metodos = sum(m["monto"] for m in reporte["metodos"]) or 1
    filas_metodo = [[ETIQUETA_PAGO[m["tipo_pago"]], entero(m["ventas"]), dinero(m["monto"]),
                     f"{m['monto'] / total_metodos * 100:.1f}%"] for m in reporte["metodos"]]
    h.append(KeepTogether([
        _p("Ventas por método de pago", e["seccion"]),
        _tabla(["Método de pago", "Ventas", "Monto vendido", "% del total"], filas_metodo,
               [ANCHO_UTIL - 9 * cm, 2.6 * cm, 3.6 * cm, 2.8 * cm], derecha=(1, 2, 3), estilos=e),
    ]))

    pagos = cred["pagos"]
    if pagos:
        h.append(_p("Cobros de créditos del período", e["seccion"]))
        filas = [[fecha_hora_corta(pg["fecha"]), pg["numero_venta"], pg["nombre_completo"],
                  ETIQUETA_PAGO.get(pg["metodo_pago"], pg["metodo_pago"] or "Otro"), dinero(pg["monto"])]
                 for pg in pagos[:MAX_FILAS_DETALLE]]
        h.append(_tabla(["Fecha", "Crédito", "Cliente", "Método", "Monto"], filas,
                        [3.1 * cm, 2.6 * cm, ANCHO_UTIL - 11.2 * cm, 2.4 * cm, 3.1 * cm],
                        derecha=(4,), estilos=e))

    # --- Entradas y salidas ---
    filas_mov = [
        ["Entradas de mercadería", entero(ind["entradas_mov"]), entero(ind["entradas"])],
        ["Salidas manuales", entero(ind["salidas_mov"]), entero(ind["salidas"])],
        ["Salidas por ventas", "-", entero(ind["salidas_por_venta"])],
    ]
    if ind["ajustes_mov"]:
        filas_mov.append(["Ajustes", entero(ind["ajustes_mov"]), "-"])
    h.append(KeepTogether([
        _p("Resumen de entradas y salidas", e["seccion"]),
        _tabla(["Tipo", "Movimientos", "Unidades"], filas_mov,
               [ANCHO_UTIL - 7 * cm, 3.5 * cm, 3.5 * cm], derecha=(1, 2), estilos=e),
    ]))

    # --- Mayor movimiento ---
    mov = reporte["mayor_movimiento"]
    if mov:
        filas = [[m["codigo"], m["nombre"], entero(m["entradas"]), entero(m["salidas"]), entero(m["total"]),
                  entero(m["existencia"])] for m in mov]
        h.append(_p("Productos con mayor movimiento", e["seccion"]))
        h.append(_tabla(["Código", "Producto", "Entradas", "Salidas", "Total", "Existencia hoy"], filas,
                        [2.2 * cm, ANCHO_UTIL - 12.2 * cm, 2.3 * cm, 2.2 * cm, 2.0 * cm, 3.5 * cm],
                        derecha=(2, 3, 4, 5), estilos=e))
    else:
        h.append(KeepTogether([_p("Productos con mayor movimiento", e["seccion"]),
                               _p("No hubo movimientos de inventario en este período.", e["vacio"])]))

    # --- Stock bajo ---
    bajos = reporte["stock_bajo"]
    h.append(_p("Productos con stock bajo", e["seccion"]))
    h.append(_p("Situación actual del inventario (no depende del período elegido): "
                "existencia igual o menor al stock mínimo de cada producto.", e["nota"]))
    h.append(Spacer(1, 6))
    if bajos:
        filas = [[b["codigo"], b["nombre"], entero(b["existencia"]), entero(b["stock_minimo"])] for b in bajos]
        h.append(_tabla(["Código", "Producto", "Existencia", "Stock mínimo"], filas,
                        [2.6 * cm, ANCHO_UTIL - 9 * cm, 3.0 * cm, 3.4 * cm], derecha=(2, 3), estilos=e,
                        resaltar=lambda i: AVISO_SUAVE))
    else:
        h.append(_p("Ningún producto está por debajo de su stock mínimo.", e["vacio"]))

    # --- Detalle de operaciones ---
    detalle = reporte["detalle"]
    h.append(_p("Detalle de operaciones", e["seccion"]))
    if detalle:
        mostradas = detalle[:MAX_FILAS_DETALLE]
        total = reporte["detalle_total"]
        if total > len(mostradas):
            h.append(_p(f"Se muestran los {entero(len(mostradas))} movimientos más recientes de "
                        f"{entero(total)} registrados en el período.", e["nota"]))
            h.append(Spacer(1, 6))
        filas = []
        for d in mostradas:
            referencia = d["numero_venta"] or d["descripcion"] or ""
            filas.append([fecha_hora_corta(d["fecha"]), ETIQUETA_OPERACION.get(d["operacion"], d["operacion"]),
                          f"{d['codigo']} - {d['producto']}", entero(d["cantidad"]),
                          entero(d["existencia_nueva"]), referencia])
        h.append(_tabla(["Fecha", "Operación", "Producto", "Cantidad", "Existencia", "Referencia"], filas,
                        [3.1 * cm, 2.3 * cm, ANCHO_UTIL - 12.7 * cm, 2.0 * cm, 2.3 * cm, 3.0 * cm],
                        derecha=(3, 4), estilos=e))
    else:
        h.append(_p("No hay operaciones registradas durante el período seleccionado.", e["vacio"]))

    doc.build(h, canvasmaker=partial(_CanvasNumerado, meta=meta))
    return ruta
