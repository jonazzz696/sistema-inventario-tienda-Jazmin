
from models import cliente, movimiento_cuenta_cliente


def obtener_clientes_con_saldo():
    
    clientes = cliente.listar_clientes(solo_activos=True)

    resultado = []
    for c in clientes:
        saldo = movimiento_cuenta_cliente.obtener_saldo_cliente(c["id_cliente"])
        resultado.append({
            "id_cliente": c["id_cliente"],
            "nombre_completo": c["nombre_completo"],
            "telefono": c["telefono"],
            "limite_credito": c["limite_credito"],
            "saldo": saldo,
        })

    return resultado


def obtener_historial_cliente(id_cliente):
    return movimiento_cuenta_cliente.listar_movimientos_cliente(id_cliente)


# ======================================================================
# Cuentas por cobrar (creditos por venta y sus pagos)
# ======================================================================

from datetime import date, datetime
import traceback

from helpers import sesion
from helpers.formato import centavos_a_texto, texto_a_centavos
from models import credito
from reportes.periodos import crear_periodo


def obtener_creditos():
    return credito.listar_creditos()


def obtener_credito(id_venta):
    return credito.obtener_credito(id_venta)


def resumen_creditos(creditos=None):
    """Numeros del dashboard de Creditos, calculados desde la base."""
    creditos = creditos if creditos is not None else credito.listar_creditos()
    activos = [c for c in creditos if c["estado_credito"] != "pagado"]
    mayor = max(activos, key=lambda c: c["saldo"], default=None)

    # Cliente con mayor saldo (sumando todos sus creditos activos).
    por_cliente = {}
    for c in activos:
        por_cliente.setdefault(c["id_cliente"], [c["nombre_completo"], 0])[1] += c["saldo"]
    cliente_mayor = max(por_cliente.values(), key=lambda x: x[1], default=None)

    mes = crear_periodo("mensual", date.today())
    cobros_mes = credito.resumen_cobros(mes.desde_sql, mes.hasta_sql)
    return {
        "activos": len(activos),
        "por_cobrar": sum(c["saldo"] for c in activos),
        "pendientes": sum(1 for c in creditos if c["estado_credito"] == "pendiente"),
        "parciales": sum(1 for c in creditos if c["estado_credito"] == "parcial"),
        "pagados": sum(1 for c in creditos if c["estado_credito"] == "pagado"),
        "cobrado_mes": cobros_mes["monto"],
        "pagos_mes": cobros_mes["pagos"],
        "mes": mes.titulo,
        "total_cobrado": sum(c["pagado"] for c in creditos),
        "credito_mayor": mayor,
        "cliente_mayor": cliente_mayor,
    }


def registrar_pago(id_venta, monto_texto, metodo_pago, fecha_pago=None, observacion=""):
    """
    Registra un pago a un credito. Devuelve (exito, mensaje, resultado).

    fecha_pago: date elegida en el formulario (None = hoy). Si es hoy se
    guarda la hora actual; si es un dia anterior, se guarda ese dia a la
    misma hora actual, para conservar el orden dentro del dia.
    """
    usuario = sesion.obtener_usuario_actual()
    if usuario is None:
        return False, "No hay una sesión activa.", None

    texto = (monto_texto or "").strip()
    if not texto:
        return False, "Escribe el monto del pago.", None
    if texto.startswith("-"):
        return False, "El monto del pago no puede ser negativo.", None
    try:
        monto = texto_a_centavos(texto)
    except ValueError:
        return False, "El monto del pago debe ser un número válido (por ejemplo 25.50).", None
    if monto <= 0:
        return False, "El monto del pago debe ser mayor que $0.00.", None

    hoy = date.today()
    fecha_pago = fecha_pago or hoy
    if fecha_pago > hoy:
        return False, "La fecha del pago no puede ser posterior a hoy.", None
    momento = datetime.combine(fecha_pago, datetime.now().time().replace(microsecond=0))

    try:
        resultado = credito.registrar_pago(
            id_venta, monto, metodo_pago, usuario["id_usuario"], momento, observacion)
    except ValueError as error:
        return False, str(error), None
    except Exception as error:
        traceback.print_exc()
        return False, f"No se pudo registrar el pago ({error}). No se guardó ningún cambio.", None

    if resultado["estado"] == "pagado":
        mensaje = (f"Pago de {centavos_a_texto(monto)} registrado. "
                   f"El crédito {resultado['numero_venta']} quedó pagado por completo.")
    else:
        mensaje = (f"Pago de {centavos_a_texto(monto)} registrado. "
                   f"Saldo pendiente: {centavos_a_texto(resultado['saldo'])}.")
    return True, mensaje, resultado


def exportar_comprobante(datos_credito, ruta):
    """PDF con el estado del credito y su historial. Devuelve (exito, mensaje)."""
    try:
        from reportes.comprobante import generar_comprobante
    except ModuleNotFoundError as error:
        if not (error.name or "").startswith("reportlab"):
            raise
        return False, ("Falta la biblioteca ReportLab para crear PDF. "
                       "Instálala con:  uv pip install --python .venv reportlab")
    try:
        generar_comprobante(datos_credito, ruta)
        return True, f"Comprobante guardado en {ruta}"
    except PermissionError:
        return False, ("No se pudo guardar el archivo. Si ese PDF está abierto en otro "
                       "programa, ciérralo o elige otro nombre.")
    except Exception as error:
        traceback.print_exc()
        return False, f"No se pudo generar el comprobante ({error})."
