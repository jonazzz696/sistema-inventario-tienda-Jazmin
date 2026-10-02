"""
Redaccion automatica del resumen del periodo.

Todo el texto se arma con los numeros del reporte; no hay frases fijas
con datos escritos a mano. Si el periodo no tiene operaciones, se dice
exactamente eso.
"""

from reportes.formato import dinero, lista_natural, plural


def redactar(reporte):
    periodo = reporte["periodo"]
    ind = reporte["indicadores"]
    partes = []

    if ind["operaciones"] == 0:
        partes.append(f"No hay operaciones registradas durante {periodo.frase}.")
    else:
        detalle = []
        if ind["ventas"]:
            texto = f"{plural(ind['ventas'], 'venta', 'ventas')} por {dinero(ind['monto_ventas'])}"
            if ind["ventas_credito"]:
                texto += (f" ({dinero(ind['monto_contado'])} al contado y "
                          f"{dinero(ind['monto_credito'])} al crédito)")
            detalle.append(texto)
        if ind["cobros"]:
            detalle.append(f"{plural(ind['cobros'], 'cobro', 'cobros')} de créditos por {dinero(ind['monto_cobros'])}")
        if ind["entradas_mov"]:
            detalle.append(
                f"{plural(ind['entradas_mov'], 'entrada', 'entradas')} de mercadería "
                f"({plural(ind['entradas'], 'unidad', 'unidades')})")
        if ind["salidas_mov"]:
            detalle.append(
                f"{plural(ind['salidas_mov'], 'salida manual', 'salidas manuales')} "
                f"({plural(ind['salidas'], 'unidad', 'unidades')})")
        if ind["ajustes_mov"]:
            detalle.append(plural(ind["ajustes_mov"], "ajuste", "ajustes"))

        inicio = f"Durante {periodo.frase} se registraron {plural(ind['operaciones'], 'operación', 'operaciones')}"
        partes.append(f"{inicio}: {lista_natural(detalle)}." if detalle else f"{inicio}.")

        if ind["ventas"]:
            partes.append(
                f"Se vendieron {plural(ind['unidades_vendidas'], 'unidad', 'unidades')} "
                f"con un ticket promedio de {dinero(ind['ticket_promedio'])}.")

        top = reporte["mas_vendidos"]
        if top:
            primero = top[0]
            partes.append(
                f"El producto más vendido fue {primero['nombre']} con "
                f"{plural(primero['unidades'], 'unidad', 'unidades')}.")

        movimiento = reporte["mayor_movimiento"][:3]
        if len(movimiento) > 1:
            nombres = [m["nombre"] for m in movimiento]
            partes.append(f"Los productos con mayor movimiento fueron {lista_natural(nombres)}.")
        elif movimiento:
            partes.append(f"El producto con mayor movimiento fue {movimiento[0]['nombre']}.")

        if ind["dinero_recibido"] or ind["ventas_credito"]:
            texto = f"El dinero realmente recibido fue {dinero(ind['dinero_recibido'])}"
            if ind["monto_cobros"] and ind["monto_contado"]:
                texto += " (ventas al contado más cobros de créditos)"
            elif ind["monto_cobros"]:
                texto += " (cobros de créditos)"
            texto += "."
            if ind["monto_credito"]:
                texto += (f" Las ventas a crédito generaron {dinero(ind['monto_credito'])} de saldo "
                          "por cobrar, que se contará como ingreso cuando los clientes paguen.")
            partes.append(texto)

        ant = reporte["anterior"]
        if ant["dinero_recibido"] > 0 and (ind["ventas"] or ind["cobros"]):
            cambio = (ind["dinero_recibido"] - ant["dinero_recibido"]) / ant["dinero_recibido"] * 100
            if abs(cambio) >= 0.5:
                verbo = "subió" if cambio > 0 else "bajó"
                partes.append(
                    f"Frente al período anterior, el dinero recibido {verbo} un {abs(cambio):.0f}% "
                    f"(de {dinero(ant['dinero_recibido'])} a {dinero(ind['dinero_recibido'])}).")
            else:
                partes.append("El dinero recibido se mantuvo igual al período anterior.")

    bajos = ind["stock_bajo"]
    if bajos:
        partes.append(
            f"Actualmente hay {plural(bajos, 'producto', 'productos')} con existencia "
            f"igual o menor a su stock mínimo.")
    else:
        partes.append("Actualmente ningún producto está por debajo de su stock mínimo.")

    return " ".join(partes)
