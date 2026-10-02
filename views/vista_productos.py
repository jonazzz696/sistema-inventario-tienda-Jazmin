
import tkinter as tk
from tkinter import ttk, messagebox

from controllers import controlador_productos, controlador_categorias
from helpers.formato import centavos_a_texto


class VistaProductos(tk.Frame):
    def __init__(self, contenedor):
        super().__init__(contenedor, bg="white")
        self._crear_widgets()
        self._cargar_productos()

    def _crear_widgets(self):
        titulo = tk.Label(
            self, text="Productos", font=("Arial", 18, "bold"), bg="white"
        )
        titulo.pack(anchor="w", padx=20, pady=(20, 10))

        frame_botones = tk.Frame(self, bg="white")
        frame_botones.pack(anchor="w", padx=20, pady=(0, 10))

        tk.Button(
            frame_botones, text="Nuevo producto", command=self._abrir_formulario_nuevo
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            frame_botones, text="Editar seleccionado", command=self._abrir_formulario_editar
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            frame_botones, text="Activar/Desactivar", command=self._alternar_estado_seleccionado
        ).pack(side="left")

        columnas = ("id", "codigo", "nombre", "categoria", "precio_venta",
                    "existencia", "estado")
        self.tabla = ttk.Treeview(
            self, columns=columnas, show="headings", height=15
        )

        encabezados = {
            "id": "ID", "codigo": "Codigo", "nombre": "Producto",
            "categoria": "Categoria", "precio_venta": "Precio venta",
            "existencia": "Existencia", "estado": "Estado",
        }
        anchos = {
            "id": 40, "codigo": 80, "nombre": 180, "categoria": 120,
            "precio_venta": 100, "existencia": 90, "estado": 80,
        }
        for columna in columnas:
            self.tabla.heading(columna, text=encabezados[columna])
            self.tabla.column(columna, width=anchos[columna], anchor="center")

        self.tabla.column("nombre", anchor="w")
        self.tabla.column("categoria", anchor="w")

        self.tabla.pack(padx=20, pady=10, fill="both", expand=True)

        self._id_producto_seleccionado = None
        self.tabla.bind("<<TreeviewSelect>>", self._al_seleccionar_fila)

    def _al_seleccionar_fila(self, evento):
        
        seleccion = self.tabla.selection()
        if seleccion:
            valores = self.tabla.item(seleccion[0], "values")
            self._id_producto_seleccionado = int(valores[0])
        else:
            self._id_producto_seleccionado = None

    def _cargar_productos(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        productos = controlador_productos.obtener_lista_productos()

        for p in productos:
            estado_texto = "Activo" if p["estado"] == 1 else "Inactivo"
            self.tabla.insert("", "end", values=(
                p["id_producto"],
                p["codigo"],
                p["nombre"],
                p["nombre_categoria"],
                centavos_a_texto(p["precio_venta"]),
                p["existencia"],
                estado_texto,
            ))

    def _abrir_formulario_nuevo(self):
        FormularioProducto(self, producto_existente=None, al_guardar=self._cargar_productos)

    def _abrir_formulario_editar(self):
        if self._id_producto_seleccionado is None:
            messagebox.showwarning("Sin seleccion", "Selecciona un producto de la tabla primero.")
            return

        datos = controlador_productos.obtener_producto_por_id(self._id_producto_seleccionado)
        FormularioProducto(self, producto_existente=datos, al_guardar=self._cargar_productos)

    def _alternar_estado_seleccionado(self):
        if self._id_producto_seleccionado is None:
            messagebox.showwarning("Sin seleccion", "Selecciona un producto de la tabla primero.")
            return

        datos = controlador_productos.obtener_producto_por_id(self._id_producto_seleccionado)
        confirmacion = messagebox.askyesno(
            "Confirmar",
            f"Deseas cambiar el estado de '{datos['nombre']}'?"
        )
        if not confirmacion:
            return

        exito, mensaje = controlador_productos.alternar_estado_producto(
            datos["id_producto"], datos["estado"]
        )
        if exito:
            messagebox.showinfo("Exito", mensaje)
            self._cargar_productos()
        else:
            messagebox.showerror("Error", mensaje)


class FormularioProducto(tk.Toplevel):

    def __init__(self, padre, producto_existente, al_guardar):
        super().__init__(padre)

        self.producto_existente = producto_existente
        self.al_guardar = al_guardar
        self.es_edicion = producto_existente is not None

        self.title("Editar producto" if self.es_edicion else "Nuevo producto")
        self.geometry("420x620")
        self.minsize(420, 560)
        
        self.resizable(True, True)

        self.grab_set()

        self._crear_widgets()

        if self.es_edicion:
            self._precargar_datos()

    def _crear_widgets(self):
        contenedor = tk.Frame(self, padx=20, pady=15)
        contenedor.pack(fill="both", expand=True)

        self.entrada_codigo = self._agregar_campo(contenedor, "Codigo:")
        self.entrada_nombre = self._agregar_campo(contenedor, "Nombre:")
        self.entrada_descripcion = self._agregar_campo(contenedor, "Descripcion:")

        tk.Label(contenedor, text="Categoria:").pack(anchor="w", pady=(8, 0))
        categorias = controlador_categorias.obtener_lista_categorias()
        
        self._categorias = {c["nombre"]: c["id_categoria"] for c in categorias}

        self.combo_categoria = ttk.Combobox(
            contenedor, values=list(self._categorias.keys()), state="readonly"
        )
        self.combo_categoria.pack(fill="x")

        self.entrada_precio_compra = self._agregar_campo(contenedor, "Precio de compra:")
        self.entrada_precio_venta = self._agregar_campo(contenedor, "Precio de venta:")

        if not self.es_edicion:
        
            self.entrada_existencia = self._agregar_campo(contenedor, "Existencia inicial:")
        else:
            self.entrada_existencia = None

        self.entrada_stock_minimo = self._agregar_campo(contenedor, "Stock minimo:")
        self.entrada_unidad = self._agregar_campo(contenedor, "Unidad de medida:")

        boton_guardar = tk.Button(
            contenedor, text="Guardar", command=self._al_guardar_clic
        )
        boton_guardar.pack(fill="x", pady=(15, 0))

    def _agregar_campo(self, contenedor, etiqueta_texto):
        
        tk.Label(contenedor, text=etiqueta_texto).pack(anchor="w", pady=(8, 0))
        entrada = tk.Entry(contenedor)
        entrada.pack(fill="x")
        return entrada

    def _precargar_datos(self):
        
        p = self.producto_existente

        self.entrada_codigo.insert(0, p["codigo"])
        self.entrada_nombre.insert(0, p["nombre"])
        self.entrada_descripcion.insert(0, p["descripcion"] or "")

        categorias = controlador_categorias.obtener_lista_categorias()
        for c in categorias:
            if c["id_categoria"] == p["id_categoria"]:
                self.combo_categoria.set(c["nombre"])
                break

        self.entrada_precio_compra.insert(0, f"{p['precio_compra'] / 100:.2f}")
        self.entrada_precio_venta.insert(0, f"{p['precio_venta'] / 100:.2f}")
        self.entrada_stock_minimo.insert(0, str(p["stock_minimo"]))
        self.entrada_unidad.insert(0, p["unidad_medida"])

    def _al_guardar_clic(self):
        codigo = self.entrada_codigo.get()
        nombre = self.entrada_nombre.get()
        descripcion = self.entrada_descripcion.get()
        nombre_categoria = self.combo_categoria.get()
        precio_compra_texto = self.entrada_precio_compra.get()
        precio_venta_texto = self.entrada_precio_venta.get()
        stock_minimo_texto = self.entrada_stock_minimo.get()
        unidad = self.entrada_unidad.get()

        if not nombre_categoria:
            messagebox.showerror("Error", "Debes seleccionar una categoria.")
            return

        id_categoria = self._categorias[nombre_categoria]

        if self.es_edicion:
            exito, mensaje = controlador_productos.modificar_producto(
                self.producto_existente["id_producto"],
                codigo, nombre, descripcion, id_categoria,
                precio_compra_texto, precio_venta_texto,
                stock_minimo_texto, unidad
            )
        else:
            existencia_texto = self.entrada_existencia.get()
            exito, mensaje = controlador_productos.registrar_producto(
                codigo, nombre, descripcion, id_categoria,
                precio_compra_texto, precio_venta_texto,
                existencia_texto, stock_minimo_texto, unidad
            )

        if exito:
            messagebox.showinfo("Exito", mensaje)
            self.al_guardar()  
            self.destroy()     
        else:
            messagebox.showerror("Error", mensaje)
