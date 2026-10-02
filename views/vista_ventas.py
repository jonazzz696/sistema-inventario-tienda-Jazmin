
import tkinter as tk
from tkinter import ttk, messagebox

from controllers import controlador_ventas, controlador_clientes
from helpers.formato import centavos_a_texto


class VistaVentas(tk.Frame):
    def __init__(self, contenedor):
        super().__init__(contenedor, bg="white")

        self._carrito = []
        
        self._productos_disponibles = {}

        self._crear_widgets()
        self._cargar_productos_disponibles()
        self._cargar_ventas_recientes()

    def _crear_widgets(self):
        titulo = tk.Label(
            self, text="Ventas", font=("Arial", 18, "bold"), bg="white"
        )
        titulo.pack(anchor="w", padx=20, pady=(20, 10))

        frame_agregar = tk.Frame(self, bg="white")
        frame_agregar.pack(anchor="w", padx=20, pady=(0, 10))

        tk.Label(frame_agregar, text="Producto:", bg="white").pack(side="left")
        self.combo_producto = ttk.Combobox(frame_agregar, state="readonly", width=35)
        self.combo_producto.pack(side="left", padx=10)

        tk.Label(frame_agregar, text="Cantidad:", bg="white").pack(side="left", padx=(10, 0))
        self.entrada_cantidad = tk.Entry(frame_agregar, width=8)
        self.entrada_cantidad.pack(side="left", padx=10)

        tk.Button(
            frame_agregar, text="Agregar al carrito", command=self._al_agregar_al_carrito
        ).pack(side="left")

        tk.Label(
            self, text="Carrito de venta actual", font=("Arial", 11, "bold"), bg="white"
        ).pack(anchor="w", padx=20)

        columnas_carrito = ("producto", "cantidad", "precio_unitario", "subtotal")
        self.tabla_carrito = ttk.Treeview(
            self, columns=columnas_carrito, show="headings", height=6
        )
        for col, texto in zip(columnas_carrito, ["Producto", "Cantidad", "Precio unitario", "Subtotal"]):
            self.tabla_carrito.heading(col, text=texto)
            self.tabla_carrito.column(col, width=150, anchor="center")
        self.tabla_carrito.column("producto", width=220, anchor="w")
        self.tabla_carrito.pack(padx=20, pady=5, fill="x")

        tk.Button(
            self, text="Quitar linea seleccionada", command=self._al_quitar_del_carrito
        ).pack(anchor="w", padx=20, pady=(0, 5))

        self.etiqueta_total = tk.Label(
            self, text="Total: $0.00", font=("Arial", 13, "bold"), bg="white"
        )
        self.etiqueta_total.pack(anchor="e", padx=20)

        # --- Datos de la venta (metodo de pago, cliente) ---
        frame_venta = tk.Frame(self, bg="white")
        frame_venta.pack(anchor="w", padx=20, pady=10)

        tk.Label(frame_venta, text="Metodo de pago:", bg="white").pack(side="left")
        self.combo_pago = ttk.Combobox(
            frame_venta, values=["efectivo", "tarjeta", "otro", "credito"],
            state="readonly", width=12
        )
        self.combo_pago.set("efectivo")
        self.combo_pago.pack(side="left", padx=10)

        tk.Label(frame_venta, text="Cliente (opcional):", bg="white").pack(side="left", padx=(15, 0))
        self.combo_cliente = ttk.Combobox(frame_venta, state="readonly", width=25)
        self.combo_cliente.pack(side="left", padx=10)

        tk.Button(
            self, text="Registrar venta", command=self._al_registrar_venta,
            bg="#27ae60", fg="white", font=("Arial", 10, "bold")
        ).pack(anchor="w", padx=20, pady=(5, 15))

        tk.Label(
            self, text="Ventas recientes", font=("Arial", 11, "bold"), bg="white"
        ).pack(anchor="w", padx=20)

        columnas_recientes = ("numero", "fecha", "cliente", "tipo_pago", "total")
        self.tabla_recientes = ttk.Treeview(
            self, columns=columnas_recientes, show="headings", height=6
        )
        for col, texto in zip(columnas_recientes, ["No. venta", "Fecha", "Cliente", "Metodo de pago", "Total"]):
            self.tabla_recientes.heading(col, text=texto)
            self.tabla_recientes.column(col, width=140, anchor="center")
        self.tabla_recientes.pack(padx=20, pady=(5, 20), fill="both", expand=True)

    def _cargar_productos_disponibles(self):
        productos = controlador_ventas.obtener_productos_para_venta()
        self._productos_disponibles = {}
        opciones = []

        for p in productos:
            etiqueta = f"{p['codigo']} - {p['nombre']} ({centavos_a_texto(p['precio_venta'])}) [existencia: {p['existencia']}]"
            opciones.append(etiqueta)
            self._productos_disponibles[etiqueta] = p

        self.combo_producto["values"] = opciones

        clientes = controlador_clientes.obtener_lista_clientes()
        self._clientes_activos = {
            c["nombre_completo"]: c["id_cliente"] for c in clientes if c["estado"] == 1
        }
        self.combo_cliente["values"] = ["(Sin cliente)"] + list(self._clientes_activos.keys())
        self.combo_cliente.set("(Sin cliente)")

    def _al_agregar_al_carrito(self):
        etiqueta_producto = self.combo_producto.get()
        cantidad_texto = self.entrada_cantidad.get()

        if not etiqueta_producto:
            messagebox.showwarning("Falta informacion", "Selecciona un producto.")
            return

        try:
            cantidad = int(cantidad_texto)
        except ValueError:
            messagebox.showerror("Error", "La cantidad debe ser un numero entero.")
            return

        if cantidad <= 0:
            messagebox.showerror("Error", "La cantidad debe ser mayor a cero.")
            return

        producto_info = self._productos_disponibles[etiqueta_producto]

        cantidad_ya_en_carrito = sum(
            linea["cantidad"] for linea in self._carrito
            if linea["id_producto"] == producto_info["id_producto"]
        )
        if cantidad_ya_en_carrito + cantidad > producto_info["existencia"]:
            messagebox.showerror(
                "Sin existencia suficiente",
                f"Solo hay {producto_info['existencia']} unidades disponibles de "
                f"'{producto_info['nombre']}' (ya tienes {cantidad_ya_en_carrito} en el carrito)."
            )
            return

        subtotal = producto_info["precio_venta"] * cantidad

        self._carrito.append({
            "id_producto": producto_info["id_producto"],
            "nombre": producto_info["nombre"],
            "cantidad": cantidad,
            "precio_unitario": producto_info["precio_venta"],
            "subtotal": subtotal,
        })

        self.entrada_cantidad.delete(0, tk.END)
        self._refrescar_tabla_carrito()

    def _al_quitar_del_carrito(self):
        seleccion = self.tabla_carrito.selection()
        if not seleccion:
            messagebox.showwarning("Sin seleccion", "Selecciona una linea del carrito primero.")
            return

        indice = self.tabla_carrito.index(seleccion[0])
        del self._carrito[indice]
        self._refrescar_tabla_carrito()

    def _refrescar_tabla_carrito(self):
        for fila in self.tabla_carrito.get_children():
            self.tabla_carrito.delete(fila)

        total = 0
        for linea in self._carrito:
            self.tabla_carrito.insert("", "end", values=(
                linea["nombre"], linea["cantidad"],
                centavos_a_texto(linea["precio_unitario"]),
                centavos_a_texto(linea["subtotal"]),
            ))
            total += linea["subtotal"]

        self.etiqueta_total.config(text=f"Total: {centavos_a_texto(total)}")

    def _al_registrar_venta(self):
        if not self._carrito:
            messagebox.showwarning("Carrito vacio", "Agrega al menos un producto antes de registrar la venta.")
            return

        tipo_pago = self.combo_pago.get()

        nombre_cliente = self.combo_cliente.get()
        id_cliente = self._clientes_activos.get(nombre_cliente)  # None si es "(Sin cliente)"

        if tipo_pago == "credito" and id_cliente is None:
            messagebox.showerror(
                "Falta el cliente",
                "Debes seleccionar un cliente para registrar una venta al credito."
            )
            return

        items = [
            {"id_producto": linea["id_producto"], "cantidad": linea["cantidad"]}
            for linea in self._carrito
        ]

        exito, mensaje, resultado = controlador_ventas.registrar_venta(
            tipo_pago, id_cliente, items
        )

        if exito:
            messagebox.showinfo("Venta registrada", mensaje)
            self._carrito = []
            self._refrescar_tabla_carrito()
            self._cargar_productos_disponibles() 
            self._cargar_ventas_recientes()
        else:
            messagebox.showerror("Error al registrar la venta", mensaje)

    def _cargar_ventas_recientes(self):
        for fila in self.tabla_recientes.get_children():
            self.tabla_recientes.delete(fila)

        ventas = controlador_ventas.obtener_ventas_recientes()

        for v in ventas:
            cliente_texto = v["nombre_cliente"] or "(Sin cliente)"
            self.tabla_recientes.insert("", "end", values=(
                v["numero_venta"], v["fecha"], cliente_texto,
                v["tipo_pago"], centavos_a_texto(v["total"]),
            ))
