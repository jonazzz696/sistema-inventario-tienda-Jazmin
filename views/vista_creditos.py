
import tkinter as tk
from tkinter import ttk, messagebox

from controllers import controlador_creditos
from helpers.formato import centavos_a_texto


class VistaCreditos(tk.Frame):
    def __init__(self, contenedor):
        super().__init__(contenedor, bg="white")
        self._crear_widgets()
        self._cargar_saldos()

    def _crear_widgets(self):
        titulo = tk.Label(
            self, text="Creditos - Saldos de clientes", font=("Arial", 18, "bold"), bg="white"
        )
        titulo.pack(anchor="w", padx=20, pady=(20, 10))

        tk.Button(
            self, text="Ver historial del cliente seleccionado",
            command=self._abrir_historial
        ).pack(anchor="w", padx=20, pady=(0, 10))

        columnas = ("id", "nombre", "telefono", "limite", "saldo")
        self.tabla = ttk.Treeview(self, columns=columnas, show="headings", height=15)

        encabezados = {
            "id": "ID", "nombre": "Cliente", "telefono": "Telefono",
            "limite": "Limite de credito", "saldo": "Saldo pendiente",
        }
        for col in columnas:
            self.tabla.heading(col, text=encabezados[col])
            self.tabla.column(col, width=140, anchor="center")
        self.tabla.column("nombre", width=200, anchor="w")

        self.tabla.tag_configure("con_deuda", background="#fdecea")

        self.tabla.pack(padx=20, pady=10, fill="both", expand=True)

        self._id_cliente_seleccionado = None
        self.tabla.bind("<<TreeviewSelect>>", self._al_seleccionar_fila)

    def _al_seleccionar_fila(self, evento):
        seleccion = self.tabla.selection()
        if seleccion:
            valores = self.tabla.item(seleccion[0], "values")
            self._id_cliente_seleccionado = int(valores[0])
        else:
            self._id_cliente_seleccionado = None

    def _cargar_saldos(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        clientes = controlador_creditos.obtener_clientes_con_saldo()

        for c in clientes:
            limite_texto = (
                centavos_a_texto(c["limite_credito"])
                if c["limite_credito"] is not None else "Sin limite"
            )
            etiquetas = ("con_deuda",) if c["saldo"] > 0 else ()
            self.tabla.insert("", "end", tags=etiquetas, values=(
                c["id_cliente"], c["nombre_completo"], c["telefono"],
                limite_texto, centavos_a_texto(c["saldo"]),
            ))

    def _abrir_historial(self):
        if self._id_cliente_seleccionado is None:
            messagebox.showwarning("Sin seleccion", "Selecciona un cliente de la tabla primero.")
            return

        VentanaHistorialCliente(self, self._id_cliente_seleccionado)


class VentanaHistorialCliente(tk.Toplevel):

    def __init__(self, padre, id_cliente):
        super().__init__(padre)

        self.title("Historial de credito")
        self.geometry("650x450")
        self.resizable(True, True)

        columnas = ("fecha", "tipo", "monto", "saldo_anterior", "saldo_nuevo", "descripcion")
        tabla = ttk.Treeview(self, columns=columnas, show="headings")
        encabezados = {
            "fecha": "Fecha", "tipo": "Tipo", "monto": "Monto",
            "saldo_anterior": "Saldo anterior", "saldo_nuevo": "Saldo nuevo",
            "descripcion": "Descripcion",
        }
        for col in columnas:
            tabla.heading(col, text=encabezados[col])
            tabla.column(col, width=100, anchor="center")
        tabla.column("descripcion", width=160, anchor="w")
        tabla.pack(padx=15, pady=15, fill="both", expand=True)

        movimientos = controlador_creditos.obtener_historial_cliente(id_cliente)

        for m in movimientos:
            tabla.insert("", "end", values=(
                m["fecha"], m["tipo"].capitalize(),
                centavos_a_texto(m["monto"]),
                centavos_a_texto(m["saldo_anterior"]),
                centavos_a_texto(m["saldo_nuevo"]),
                m["descripcion"] or "",
            ))
