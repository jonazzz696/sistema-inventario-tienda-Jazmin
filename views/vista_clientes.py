
import tkinter as tk
from tkinter import ttk, messagebox

from controllers import controlador_clientes
from helpers.formato import centavos_a_texto


class VistaClientes(tk.Frame):
    def __init__(self, contenedor):
        super().__init__(contenedor, bg="white")
        self._crear_widgets()
        self._cargar_clientes()

    def _crear_widgets(self):
        titulo = tk.Label(
            self, text="Clientes", font=("Arial", 18, "bold"), bg="white"
        )
        titulo.pack(anchor="w", padx=20, pady=(20, 10))

        frame_botones = tk.Frame(self, bg="white")
        frame_botones.pack(anchor="w", padx=20, pady=(0, 10))

        tk.Button(
            frame_botones, text="Nuevo cliente", command=self._abrir_formulario_nuevo
        ).pack(side="left", padx=(0, 10))
        tk.Button(
            frame_botones, text="Editar seleccionado", command=self._abrir_formulario_editar
        ).pack(side="left", padx=(0, 10))
        tk.Button(
            frame_botones, text="Activar/Desactivar", command=self._alternar_estado_seleccionado
        ).pack(side="left")

        columnas = ("id", "nombre", "telefono", "limite_credito", "estado")
        self.tabla = ttk.Treeview(self, columns=columnas, show="headings", height=15)

        encabezados = {
            "id": "ID", "nombre": "Nombre", "telefono": "Telefono",
            "limite_credito": "Limite de credito", "estado": "Estado",
        }
        anchos = {"id": 40, "nombre": 220, "telefono": 120, "limite_credito": 140, "estado": 80}
        for col in columnas:
            self.tabla.heading(col, text=encabezados[col])
            self.tabla.column(col, width=anchos[col], anchor="center")
        self.tabla.column("nombre", anchor="w")

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

    def _cargar_clientes(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        clientes = controlador_clientes.obtener_lista_clientes()

        for c in clientes:
            estado_texto = "Activo" if c["estado"] == 1 else "Inactivo"
            limite_texto = (
                centavos_a_texto(c["limite_credito"])
                if c["limite_credito"] is not None else "Sin limite"
            )
            self.tabla.insert("", "end", values=(
                c["id_cliente"], c["nombre_completo"], c["telefono"],
                limite_texto, estado_texto,
            ))

    def _abrir_formulario_nuevo(self):
        FormularioCliente(self, cliente_existente=None, al_guardar=self._cargar_clientes)

    def _abrir_formulario_editar(self):
        if self._id_cliente_seleccionado is None:
            messagebox.showwarning("Sin seleccion", "Selecciona un cliente de la tabla primero.")
            return
        datos = controlador_clientes.obtener_cliente_por_id(self._id_cliente_seleccionado)
        FormularioCliente(self, cliente_existente=datos, al_guardar=self._cargar_clientes)

    def _alternar_estado_seleccionado(self):
        if self._id_cliente_seleccionado is None:
            messagebox.showwarning("Sin seleccion", "Selecciona un cliente de la tabla primero.")
            return

        datos = controlador_clientes.obtener_cliente_por_id(self._id_cliente_seleccionado)
        confirmacion = messagebox.askyesno(
            "Confirmar", f"Deseas cambiar el estado de '{datos['nombre_completo']}'?"
        )
        if not confirmacion:
            return

        exito, mensaje = controlador_clientes.alternar_estado_cliente(
            datos["id_cliente"], datos["estado"]
        )
        if exito:
            messagebox.showinfo("Exito", mensaje)
            self._cargar_clientes()
        else:
            messagebox.showerror("Error", mensaje)


class FormularioCliente(tk.Toplevel):
    def __init__(self, padre, cliente_existente, al_guardar):
        super().__init__(padre)

        self.cliente_existente = cliente_existente
        self.al_guardar = al_guardar
        self.es_edicion = cliente_existente is not None

        self.title("Editar cliente" if self.es_edicion else "Nuevo cliente")
        self.geometry("420x520")
        self.minsize(420, 480)
        self.resizable(True, True)
        self.grab_set()

        self._crear_widgets()

        if self.es_edicion:
            self._precargar_datos()

    def _crear_widgets(self):
        contenedor = tk.Frame(self, padx=20, pady=15)
        contenedor.pack(fill="both", expand=True)

        self.entrada_nombre = self._agregar_campo(contenedor, "Nombre completo: *")
        self.entrada_telefono = self._agregar_campo(contenedor, "Telefono: *")
        self.entrada_dui = self._agregar_campo(contenedor, "DUI (opcional):")
        self.entrada_direccion = self._agregar_campo(contenedor, "Direccion (opcional):")
        self.entrada_correo = self._agregar_campo(contenedor, "Correo (opcional):")
        self.entrada_limite = self._agregar_campo(
            contenedor, "Limite de credito (opcional, dejar en blanco = sin limite):"
        )

        tk.Label(
            contenedor, text="* Campos obligatorios", fg="#7f8c8d", font=("Arial", 8)
        ).pack(anchor="w", pady=(5, 0))

        tk.Button(
            contenedor, text="Guardar", command=self._al_guardar_clic
        ).pack(fill="x", pady=(15, 0))

    def _agregar_campo(self, contenedor, etiqueta_texto):
        tk.Label(contenedor, text=etiqueta_texto).pack(anchor="w", pady=(8, 0))
        entrada = tk.Entry(contenedor)
        entrada.pack(fill="x")
        return entrada

    def _precargar_datos(self):
        c = self.cliente_existente
        self.entrada_nombre.insert(0, c["nombre_completo"])
        self.entrada_telefono.insert(0, c["telefono"])
        self.entrada_dui.insert(0, c["dui"] or "")
        self.entrada_direccion.insert(0, c["direccion"] or "")
        self.entrada_correo.insert(0, c["correo"] or "")
        if c["limite_credito"] is not None:
            self.entrada_limite.insert(0, f"{c['limite_credito'] / 100:.2f}")

    def _al_guardar_clic(self):
        nombre = self.entrada_nombre.get()
        telefono = self.entrada_telefono.get()
        dui = self.entrada_dui.get()
        direccion = self.entrada_direccion.get()
        correo = self.entrada_correo.get()
        limite = self.entrada_limite.get()

        if self.es_edicion:
            exito, mensaje = controlador_clientes.modificar_cliente(
                self.cliente_existente["id_cliente"],
                nombre, telefono, dui, direccion, correo, limite
            )
        else:
            exito, mensaje = controlador_clientes.registrar_cliente(
                nombre, telefono, dui, direccion, correo, limite
            )

        if exito:
            messagebox.showinfo("Exito", mensaje)
            self.al_guardar()
            self.destroy()
        else:
            messagebox.showerror("Error", mensaje)
