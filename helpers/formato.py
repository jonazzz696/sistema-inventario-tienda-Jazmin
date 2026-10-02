
def centavos_a_texto(centavos):
    """Convierte 1750 -> '$17.50' para mostrar en pantalla."""
    return f"${centavos / 100:.2f}"


def texto_a_centavos(texto):
   
    texto = texto.strip().replace("$", "").replace(",", "")

    try:
        valor = float(texto)
    except ValueError:
        raise ValueError(f"'{texto}' no es un numero valido.")

    if valor < 0:
        raise ValueError("El precio no puede ser negativo.")

    return int(round(valor * 100))
