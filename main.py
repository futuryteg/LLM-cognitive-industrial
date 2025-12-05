from reconocimiento import IniciarReconocimiento
from chatGPT import ConsultaChatGPT, InicializarCHATGPT
from sintesis import hablar_simple
import threading
from EyS import Inicializar
import variablesG
from IG import ClassIG as IG
import queue
import random

# Define app_controller como una variable global
Cola = queue.Queue()

#! ----------------------------------------------------------------
#! ---------------------- Funciones visibles ----------------------
#! ----------------------------------------------------------------

def ProcesadoDeOrdenes(Orden, subir_usuario, subir_bot):
    """Función para procesar las órdenes del usuario y realizar la consulta al modelo"""
    
    subir_usuario(Orden)
    
    variablesG.EventoVoz.wait()
    variablesG.EventoVoz.clear()
    
    Consulta = ConsultaChatGPT(Orden)
    subir_bot(Consulta)
    
    # Usar la función simple en lugar de TextaVoz
    
    threading.Thread(target=hablar_simple, args=(Consulta,), daemon=True).start()
    
    variablesG.EventoVoz.set()


class AppController:
    def __init__(self):
        variablesG.Var = True
        self.chat_app = IG(on_close=self.on_close)
        self.id = random.randint(0, 1000)

    def on_close(self):
        variablesG.Var = False
        self.chat_app.ventana.destroy()

    def run(self):
        variablesG.EventoVoz.set()
        variablesG.EventoOPCUA.set()
        variablesG.EventoHablar.set()
        
        Inicializar()
        InicializarCHATGPT()
        IniciarReconocimiento()
        
        self.chat_app.run()
    
    def ejecutar_procesado(self, mensaje):
        ProcesadoDeOrdenes(mensaje, self.chat_app.subir_usuario, self.chat_app.subir_bot)

def procesarMensaje_fuera(mensaje : str):
    variablesG.Interfaz.ejecutar_procesado(mensaje)
    

#* ----------------------------------------------------------------
#* ---------------------- Funcion main ----------------------------
#* ----------------------------------------------------------------

if __name__ == "__main__":
    variablesG.Interfaz = AppController()
    variablesG.Interfaz.run()
    
