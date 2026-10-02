
import tkinter as tk
from tkinter import messagebox

from controllers import controlador_login


class VistaLogin(tk.Tk):

    def __init__(self, on_login_exitoso):
        super().__init__()

        self.on_login_exitoso = on_login_exitoso

        self.title("Iniciar sesion - Tienda Jazmin")
        self.geometry("350x250")
        self.resizable(False, False)  

        self._crear_widgets()

    def _crear_widgets(self):
        contenedor = tk.Frame(self, padx=30, pady=30)
        contenedor.pack(expand=True, fill="both")

        titulo = tk.Label(
            contenedor, text="Tienda Jazmin", font=("Arial", 16, "bold")
        )
        titulo.pack(pady=(0, 20))

        tk.Label(contenedor, text="Usuario:").pack(anchor="w")
        self.entrada_usuario = tk.Entry(contenedor)
        self.entrada_usuario.pack(fill="x", pady=(0, 10))
        self.entrada_usuario.focus() 

        tk.Label(contenedor, text="Contrasena:").pack(anchor="w")
        self.entrada_password = tk.Entry(contenedor, show="*")
        
        self.entrada_password.pack(fill="x", pady=(0, 20))

        boton_entrar = tk.Button(
            contenedor, text="Iniciar sesion", command=self._al_iniciar_sesion
        )
        boton_entrar.pack(fill="x")

        self.bind("<Return>", lambda evento: self._al_iniciar_sesion())

    def _al_iniciar_sesion(self):
        nombre_usuario = self.entrada_usuario.get()
        password = self.entrada_password.get()

        exito, mensaje = controlador_login.iniciar_sesion(nombre_usuario, password)

        if exito:
            self.destroy()
            
            self.on_login_exitoso()
        else:
            messagebox.showerror("Error de inicio de sesion", mensaje)
            self.entrada_password.delete(0, tk.END)  
