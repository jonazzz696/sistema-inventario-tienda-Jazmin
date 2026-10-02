"""
Calculo de periodos para los reportes.

Un Periodo es un rango [inicio, fin) de fechas: incluye el dia de
inicio y excluye el de fin. Asi las consultas usan
    fecha >= inicio AND fecha < fin
sobre el texto 'YYYY-MM-DD HH:MM:SS' que guarda SQLite, y pueden
aprovechar los indices por fecha.
"""

from dataclasses import dataclass
from datetime import date, timedelta

TIPOS = ("diario", "semanal", "mensual", "anual")
ETIQUETAS = {"diario": "Diario", "semanal": "Semanal", "mensual": "Mensual", "anual": "Anual"}

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MESES_CORTOS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
DIAS_CORTOS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


def _dmy(d):
    return d.strftime("%d/%m/%Y")


def _sumar_meses(d, meses):
    total = d.year * 12 + (d.month - 1) + meses
    return date(total // 12, total % 12 + 1, 1)


@dataclass(frozen=True)
class Periodo:
    tipo: str
    inicio: date          # incluido
    fin: date             # excluido

    # --- Rango para SQL ---

    @property
    def desde_sql(self):
        return f"{self.inicio.isoformat()} 00:00:00"

    @property
    def hasta_sql(self):
        return f"{self.fin.isoformat()} 00:00:00"

    @property
    def ultimo_dia(self):
        return self.fin - timedelta(days=1)

    # --- Textos ---

    @property
    def etiqueta_tipo(self):
        return ETIQUETAS[self.tipo]

    @property
    def titulo(self):
        """Nombre corto para encabezados: 'Septiembre 2026', 'Año 2026'..."""
        if self.tipo == "diario":
            return f"{self.inicio.day} de {MESES[self.inicio.month - 1]} de {self.inicio.year}"
        if self.tipo == "semanal":
            return f"Semana del {_dmy(self.inicio)} al {_dmy(self.ultimo_dia)}"
        if self.tipo == "mensual":
            return f"{MESES[self.inicio.month - 1].capitalize()} {self.inicio.year}"
        return f"Año {self.inicio.year}"

    @property
    def rango_texto(self):
        if self.tipo == "diario":
            return _dmy(self.inicio)
        return f"Del {_dmy(self.inicio)} al {_dmy(self.ultimo_dia)}"

    @property
    def frase(self):
        """Para redactar: 'Durante <frase> se registraron...'."""
        if self.tipo == "diario":
            return f"el {self.inicio.day} de {MESES[self.inicio.month - 1]} de {self.inicio.year}"
        if self.tipo == "semanal":
            a, b = self.inicio, self.ultimo_dia
            if a.month == b.month:
                return f"la semana del {a.day} al {b.day} de {MESES[b.month - 1]} de {b.year}"
            if a.year == b.year:
                return (f"la semana del {a.day} de {MESES[a.month - 1]} al "
                        f"{b.day} de {MESES[b.month - 1]} de {b.year}")
            return f"la semana del {_dmy(a)} al {_dmy(b)}"
        if self.tipo == "mensual":
            return f"{MESES[self.inicio.month - 1]} de {self.inicio.year}"
        return f"el año {self.inicio.year}"

    @property
    def nombre_archivo(self):
        base = f"Reporte_Inventario_{self.etiqueta_tipo}_"
        if self.tipo == "diario":
            return base + f"{self.inicio.isoformat()}.pdf"
        if self.tipo == "semanal":
            return base + f"{self.inicio.isoformat()}_al_{self.ultimo_dia.isoformat()}.pdf"
        if self.tipo == "mensual":
            return base + f"{self.inicio.strftime('%Y-%m')}.pdf"
        return base + f"{self.inicio.year}.pdf"

    # --- Agrupacion para graficos ---

    @property
    def formato_grupo_sql(self):
        """Formato de strftime() de SQLite para agrupar dentro del periodo."""
        return {"diario": "%H", "semanal": "%Y-%m-%d", "mensual": "%Y-%m-%d", "anual": "%Y-%m"}[self.tipo]

    @property
    def unidad_grupo(self):
        return {"diario": "hora", "semanal": "día", "mensual": "día", "anual": "mes"}[self.tipo]

    def grupos(self):
        """Lista completa de (clave, etiqueta) del eje X, incluso los vacios."""
        if self.tipo == "diario":
            return [(f"{h:02d}", f"{h:02d}h") for h in range(24)]
        if self.tipo in ("semanal", "mensual"):
            salida = []
            d = self.inicio
            while d < self.fin:
                etiqueta = f"{DIAS_CORTOS[d.weekday()]} {d.day}" if self.tipo == "semanal" else str(d.day)
                salida.append((d.isoformat(), etiqueta))
                d += timedelta(days=1)
            return salida
        return [(f"{self.inicio.year}-{m:02d}", MESES_CORTOS[m - 1]) for m in range(1, 13)]

    # --- Navegacion ---

    def anterior(self):
        return desplazar(self, -1)

    def siguiente(self):
        return desplazar(self, 1)


def crear_periodo(tipo, fecha):
    """Periodo del tipo indicado que contiene la fecha dada."""
    if tipo not in TIPOS:
        raise ValueError(f"Tipo de periodo no valido: {tipo}")
    if tipo == "diario":
        return Periodo(tipo, fecha, fecha + timedelta(days=1))
    if tipo == "semanal":
        lunes = fecha - timedelta(days=fecha.weekday())
        return Periodo(tipo, lunes, lunes + timedelta(days=7))
    if tipo == "mensual":
        inicio = date(fecha.year, fecha.month, 1)
        return Periodo(tipo, inicio, _sumar_meses(inicio, 1))
    return Periodo(tipo, date(fecha.year, 1, 1), date(fecha.year + 1, 1, 1))


def desplazar(periodo, pasos):
    """Periodo del mismo tipo, 'pasos' periodos antes (negativo) o despues."""
    if periodo.tipo == "diario":
        return crear_periodo("diario", periodo.inicio + timedelta(days=pasos))
    if periodo.tipo == "semanal":
        return crear_periodo("semanal", periodo.inicio + timedelta(days=7 * pasos))
    if periodo.tipo == "mensual":
        return crear_periodo("mensual", _sumar_meses(periodo.inicio, pasos))
    return crear_periodo("anual", date(periodo.inicio.year + pasos, 1, 1))
