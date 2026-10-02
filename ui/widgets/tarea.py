"""
Ejecucion en segundo plano con QThread.

Evita que la ventana se congele mientras se consulta un periodo largo o
se genera un PDF. La funcion corre en otro hilo y el resultado vuelve
al hilo de la interfaz mediante la senal 'terminado'.

Importante: conectar 'terminado' a un METODO de un widget (no a una
lambda) para que Qt lo ejecute en el hilo de la interfaz.
"""

import traceback

from PySide6.QtCore import QThread, Signal


class Tarea(QThread):
    terminado = Signal(object, object)   # (etiqueta, resultado o Exception)

    def __init__(self, etiqueta, funcion, *args, parent=None):
        super().__init__(parent)
        self.etiqueta = etiqueta
        self._funcion = funcion
        self._args = args

    def run(self):
        try:
            resultado = self._funcion(*self._args)
        except Exception as error:  # nunca dejar que un error mate el hilo en silencio
            traceback.print_exc()
            resultado = error
        self.terminado.emit(self.etiqueta, resultado)
