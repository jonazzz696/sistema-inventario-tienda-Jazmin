
import tkinter as tk
from tkinter import ttk

from views.vista_categorias import VistaCategorias
from views.vista_productos import VistaProductos
from views.vista_inventario import VistaInventario
from views.vista_clientes import VistaClientes
from views.vista_ventas import VistaVentas
from views.vista_creditos import VistaCreditos
from helpers import sesion


class VentanaPrincipal(tk.Tk):

    def __init__(self):
    
        super().__init__()

        self.title("Sistema de Gestion - Tienda Jazmin")
        self.geometry("1000x600")   
        self.minsize(800, 500)      
        self._crear_layout_base()

    def _crear_layout_base(self):
        
        self.frame_menu = tk.Frame(self, bg="#2c3e50", width=200)
        self.frame_menu.pack(side="left", fill="y")
        

        etiqueta_menu = tk.Label(
            self.frame_menu,
            text="Tienda Jazmin",
            bg="#2c3e50",
            fg="white",
            font=("Arial", 14, "bold"),
            pady=20,
        )
        etiqueta_menu.pack()

        usuario_actual = sesion.obtener_usuario_actual()
        texto_usuario = f"{usuario_actual['nombre']} ({usuario_actual['rol']})"
        etiqueta_usuario = tk.Label(
            self.frame_menu,
            text=texto_usuario,
            bg="#2c3e50",
            fg="#bdc3c7",
            font=("Arial", 9),
        )
        etiqueta_usuario.pack(pady=(0, 15))

        boton_productos = tk.Button(
            self.frame_menu,
            text="Productos",
            command=self._mostrar_productos,
            bg="#34495e",
            fg="white",
            relief="flat",
            anchor="w",
            padx=15,
        )
        boton_productos.pack(fill="x", pady=2)

        boton_inventario = tk.Button(
            self.frame_menu,
            text="Inventario",
            command=self._mostrar_inventario,
            bg="#34495e",
            fg="white",
            relief="flat",
            anchor="w",
            padx=15,
        )
        boton_inventario.pack(fill="x", pady=2)

        boton_clientes = tk.Button(
            self.frame_menu,
            text="Clientes",
            command=self._mostrar_clientes,
            bg="#34495e",
            fg="white",
            relief="flat",
            anchor="w",
            padx=15,
        )
        boton_clientes.pack(fill="x", pady=2)

        boton_ventas = tk.Button(
            self.frame_menu,
            text="Ventas",
            command=self._mostrar_ventas,
            bg="#34495e",
            fg="white",
            relief="flat",
            anchor="w",
            padx=15,
        )
        boton_ventas.pack(fill="x", pady=2)

        boton_creditos = tk.Button(
            self.frame_menu,
            text="Creditos",
            command=self._mostrar_creditos,
            bg="#34495e",
            fg="white",
            relief="flat",
            anchor="w",
            padx=15,
        )
        boton_creditos.pack(fill="x", pady=2)

        boton_categorias = tk.Button(
            self.frame_menu,
            text="Categorias",
            command=self._mostrar_categorias,
            bg="#34495e",
            fg="white",
            relief="flat",
            anchor="w",
            padx=15,
        )
        boton_categorias.pack(fill="x", pady=2)

        self.frame_contenido = tk.Frame(self, bg="white")
        self.frame_contenido.pack(side="right", fill="both", expand=True)

        self.frame_actual = None
        self._mostrar_bienvenida()

        boton_salir = tk.Button(
            self.frame_menu,
            text="Cerrar sesion",
            command=self._al_cerrar_sesion,
            bg="#c0392b",
            fg="white",
            relief="flat",
        )
        boton_salir.pack(side="bottom", fill="x", pady=10, padx=10)

    def _al_cerrar_sesion(self):
        from views.vista_login import VistaLogin

        sesion.cerrar_sesion()
        self.destroy()  # cierra la ventana principal

        login = VistaLogin(on_login_exitoso=lambda: VentanaPrincipal().mainloop())
        login.mainloop()

    def _limpiar_contenido(self):
        if self.frame_actual is not None:
            self.frame_actual.destroy()

    def _mostrar_bienvenida(self):
        
        self._limpiar_contenido()

        frame = tk.Frame(self.frame_contenido, bg="white")
        frame.pack(fill="both", expand=True)

        etiqueta_bienvenida = tk.Label(
            frame,
            text="Bienvenido a Tienda Jazmin\n\n(Selecciona un modulo del menu)",
            font=("Arial", 16),
            bg="white",
        )
        etiqueta_bienvenida.pack(expand=True)

        self.frame_actual = frame

    def _mostrar_categorias(self):
        self._limpiar_contenido()

        self.frame_actual = VistaCategorias(self.frame_contenido)
        self.frame_actual.pack(fill="both", expand=True)

    def _mostrar_productos(self):
        
        self._limpiar_contenido()

        self.frame_actual = VistaProductos(self.frame_contenido)
        self.frame_actual.pack(fill="both", expand=True)

    def _mostrar_inventario(self):
        
        self._limpiar_contenido()

        self.frame_actual = VistaInventario(self.frame_contenido)
        self.frame_actual.pack(fill="both", expand=True)

    def _mostrar_clientes(self):
        
        self._limpiar_contenido()

        self.frame_actual = VistaClientes(self.frame_contenido)
        self.frame_actual.pack(fill="both", expand=True)

    def _mostrar_ventas(self):
       
        self._limpiar_contenido()

        self.frame_actual = VistaVentas(self.frame_contenido)
        self.frame_actual.pack(fill="both", expand=True)

    def _mostrar_creditos(self):
        
        self._limpiar_contenido()

        self.frame_actual = VistaCreditos(self.frame_contenido)
        self.frame_actual.pack(fill="both", expand=True)


if __name__ == "__main__":
    
    app = VentanaPrincipal()
    app.mainloop()
