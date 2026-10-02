
import tkinter as tk
from tkinter import ttk, messagebox

from controllers import controlador_categorias


class VistaCategorias(tk.Frame):

    def __init__(self, contenedor):
        super().__init__(contenedor, bg="white")

        self._crear_widgets()
        self._cargar_categorias()

    def _crear_widgets(self):


        titulo = tk.Label(
            self, text="Categorias", font=("Arial", 18, "bold"), bg="white"
        )
        titulo.pack(anchor="w", padx=20, pady=(20, 10))

        frame_formulario = tk.Frame(self, bg="white")
        frame_formulario.pack(anchor="w", padx=20, pady=10)

        tk.Label(
            frame_formulario, text="Nombre:", bg="white"
        ).pack(side="left")

        self.entrada_nombre = tk.Entry(frame_formulario, width=30)
        self.entrada_nombre.pack(side="left", padx=10)

        boton_registrar = tk.Button(
            frame_formulario,
            text="Registrar categoria",
            command=self._al_registrar,
        )
        boton_registrar.pack(side="left")

        columnas = ("id", "nombre", "estado")
        self.tabla = ttk.Treeview(
            self, columns=columnas, show="headings", height=12
        )
        self.tabla.heading("id", text="ID")
        self.tabla.heading("nombre", text="Nombre")
        self.tabla.heading("estado", text="Estado")

        self.tabla.column("id", width=50, anchor="center")
        self.tabla.column("nombre", width=250)
        self.tabla.column("estado", width=100, anchor="center")

        self.tabla.pack(padx=20, pady=10, fill="both", expand=True)

    def _cargar_categorias(self):
        
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        categorias = controlador_categorias.obtener_lista_categorias()

        for cat in categorias:
            estado_texto = "Activo" if cat["estado"] == 1 else "Inactivo"
            self.tabla.insert(
                "", "end", values=(cat["id_categoria"], cat["nombre"], estado_texto)
            )

    def _al_registrar(self):
        
        nombre = self.entrada_nombre.get()

        exito, mensaje = controlador_categorias.registrar_categoria(nombre)

        if exito:
            messagebox.showinfo("Exito", mensaje)
            self.entrada_nombre.delete(0, tk.END)  # limpia la caja de texto
            self._cargar_categorias()  # refresca la tabla
        else:
            messagebox.showerror("Error", mensaje)
