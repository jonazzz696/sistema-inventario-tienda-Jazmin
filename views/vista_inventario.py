
import tkinter as tk
from tkinter import ttk, messagebox

from controllers import controlador_inventario, controlador_productos


class VistaInventario(tk.Frame):
    def __init__(self, contenedor):
        super().__init__(contenedor, bg="white")
        self._crear_widgets()
        self._cargar_historial()
        self._cargar_stock_bajo()

    def _crear_widgets(self):
        titulo = tk.Label(
            self, text="Inventario", font=("Arial", 18, "bold"), bg="white"
        )
        titulo.pack(anchor="w", padx=20, pady=(20, 10))

        # --- Formulario de movimiento manual ---
        frame_formulario = tk.LabelFrame(
            self, text="Registrar movimiento manual", bg="white", padx=15, pady=10
        )
        frame_formulario.pack(fill="x", padx=20, pady=(0, 15))

        fila1 = tk.Frame(frame_formulario, bg="white")
        fila1.pack(fill="x", pady=5)

        tk.Label(fila1, text="Producto:", bg="white").pack(side="left")
        productos = controlador_productos.obtener_lista_productos()
        self._productos_por_nombre = {
            f"{p['codigo']} - {p['nombre']}": p["id_producto"] for p in productos
        }
        self.combo_producto = ttk.Combobox(
            fila1, values=list(self._productos_por_nombre.keys()),
            state="readonly", width=35
        )
        self.combo_producto.pack(side="left", padx=10)

        tk.Label(fila1, text="Tipo:", bg="white").pack(side="left", padx=(15, 0))
        self.combo_tipo = ttk.Combobox(
            fila1, values=["entrada", "salida"], state="readonly", width=10
        )
        self.combo_tipo.set("entrada")
        self.combo_tipo.pack(side="left", padx=10)

        fila2 = tk.Frame(frame_formulario, bg="white")
        fila2.pack(fill="x", pady=5)

        tk.Label(fila2, text="Cantidad:", bg="white").pack(side="left")
        self.entrada_cantidad = tk.Entry(fila2, width=10)
        self.entrada_cantidad.pack(side="left", padx=10)

        tk.Label(fila2, text="Motivo (opcional):", bg="white").pack(side="left", padx=(15, 0))
        self.entrada_motivo = tk.Entry(fila2, width=35)
        self.entrada_motivo.pack(side="left", padx=10)

        tk.Button(
            frame_formulario, text="Registrar movimiento",
            command=self._al_registrar_movimiento
        ).pack(anchor="w", pady=(10, 0))

        # --- Alerta de stock bajo ---
        frame_alerta = tk.LabelFrame(
            self, text="Productos con stock bajo", bg="white", padx=15, pady=10
        )
        frame_alerta.pack(fill="x", padx=20, pady=(0, 15))

        columnas_alerta = ("codigo", "nombre", "existencia", "stock_minimo")
        self.tabla_alerta = ttk.Treeview(
            frame_alerta, columns=columnas_alerta, show="headings", height=4
        )
        for col, texto in zip(columnas_alerta, ["Codigo", "Producto", "Existencia", "Stock minimo"]):
            self.tabla_alerta.heading(col, text=texto)
            self.tabla_alerta.column(col, width=140, anchor="center")
        self.tabla_alerta.tag_configure("bajo", background="#fdecea")
        self.tabla_alerta.pack(fill="x")

        # --- Historial de movimientos ---
        titulo_historial = tk.Label(
            self, text="Historial de movimientos (mas recientes primero)",
            font=("Arial", 11, "bold"), bg="white"
        )
        titulo_historial.pack(anchor="w", padx=20)

        columnas_historial = ("fecha", "producto", "tipo", "cantidad",
                               "existencia_nueva", "descripcion")
        self.tabla_historial = ttk.Treeview(
            self, columns=columnas_historial, show="headings", height=8
        )
        encabezados = {
            "fecha": "Fecha", "producto": "Producto", "tipo": "Tipo",
            "cantidad": "Cantidad", "existencia_nueva": "Existencia resultante",
            "descripcion": "Motivo",
        }
        for col in columnas_historial:
            self.tabla_historial.heading(col, text=encabezados[col])
            self.tabla_historial.column(col, width=130, anchor="center")
        self.tabla_historial.column("producto", width=180, anchor="w")
        self.tabla_historial.column("descripcion", width=200, anchor="w")

        self.tabla_historial.pack(padx=20, pady=(5, 20), fill="both", expand=True)

    def _al_registrar_movimiento(self):
        nombre_producto = self.combo_producto.get()
        tipo = self.combo_tipo.get()
        cantidad_texto = self.entrada_cantidad.get()
        motivo = self.entrada_motivo.get()

        if not nombre_producto:
            messagebox.showwarning("Falta informacion", "Selecciona un producto.")
            return

        id_producto = self._productos_por_nombre[nombre_producto]

        exito, mensaje = controlador_inventario.registrar_movimiento_manual(
            id_producto, tipo, cantidad_texto, motivo
        )

        if exito:
            messagebox.showinfo("Exito", mensaje)
            self.entrada_cantidad.delete(0, tk.END)
            self.entrada_motivo.delete(0, tk.END)
            self._cargar_historial()
            self._cargar_stock_bajo()
        else:
            messagebox.showerror("Error", mensaje)

    def _cargar_historial(self):
        for fila in self.tabla_historial.get_children():
            self.tabla_historial.delete(fila)

        movimientos = controlador_inventario.obtener_historial()

        for m in movimientos:
            self.tabla_historial.insert("", "end", values=(
                m["fecha"],
                f"{m['codigo']} - {m['nombre_producto']}",
                m["tipo"],
                m["cantidad"],
                m["existencia_nueva"],
                m["descripcion"] or "",
            ))

    def _cargar_stock_bajo(self):
        for fila in self.tabla_alerta.get_children():
            self.tabla_alerta.delete(fila)

        productos_bajos = controlador_inventario.obtener_productos_stock_bajo()

        if not productos_bajos:
            self.tabla_alerta.insert("", "end", values=(
                "", "No hay productos con stock bajo por ahora.", "", ""
            ))
            return

        for p in productos_bajos:
            self.tabla_alerta.insert("", "end", tags=("bajo",), values=(
                p["codigo"], p["nombre"], p["existencia"], p["stock_minimo"]
            ))
