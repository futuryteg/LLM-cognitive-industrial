from threading import Event
from threading import Thread
from json_Hilos import ExtraerDatosConfig, GuardarEnArchivo
import variablesG
import time as t
from localC import ExtraerVariables as ExtraerVariablesLocal
from globalC import ExtraerVariables as ExtraerVariablesGlobal
from apiC import ExtraerVariables as ExtraerVariablesAPI
from localC import GenerarDatos as GenerarVariablesLocal
from globalC import GenerarDatos as GenerarVariablesGlobal
from apiC import GenerarDatos as GenerarVariablesAPI

#! ----------------------------------------------------------------
#! ---------------------- Funciones internas ----------------------
#! ----------------------------------------------------------------

def sleep_interruptible(seconds):
    end_time = t.time() + seconds
    while t.time() < end_time:
        if not variablesG.Var:
            break
        t.sleep(0.1)  # duerme en segmentos de 0.1 segundos
        
def Guardar(valores: dict) -> None:
    """Funcion para guardar los datos en la variable global DatosLeidos"""
    
    variablesG.EventoOPCUA.wait()
    variablesG.EventoOPCUA.clear()
    
    variablesG.DatosLeidos = valores
    
    variablesG.EventoOPCUA.set()
    
    GuardarEnArchivo(valores)

def GuardarDatos() -> None:
    """Funcion para guardar los datos cada 5 segundos desde un hilo
    
    CAMBIO IMPORTANTE: Ahora combina datos de múltiples fuentes
    - LOCAL (OPC UA): Sensores en tiempo real
    - GLOBAL (MQTT): Datos de planta distribuidos
    - API (REST): Datos empresariales ERP/MES
    """
    print("Guardando datos cada 5 segundos - activado")
    
    while variablesG.Var:
        # Diccionario combinado de todas las fuentes
        datos_combinados = {}
        
        # Nivel 1: LOCAL (OPC UA)
        if variablesG.nivel_local:
            datos_combinados['LOCAL'] = ExtraerVariablesLocal()
        
        # Nivel 2: GLOBAL (MQTT)
        if variablesG.nivel_global:
            datos_combinados['GLOBAL'] = ExtraerVariablesGlobal()
        
        # Nivel 3: API (REST)
        if variablesG.nivel_api:
            datos_combinados['API'] = ExtraerVariablesAPI()
        
        # Guardar datos combinados
        if datos_combinados:
            Guardar(datos_combinados)
            
        sleep_interruptible(5)
        
    print("Guardando datos cada 5 segundos - desactivado")
        
def GenerarDatos() -> None:
    """Funcion para generar los datos dependiendo de los modos seleccionados
    
    CAMBIO IMPORTANTE: Ahora se pueden activar múltiples niveles simultáneamente
    """
    threads = []
    
    # Nivel 1: LOCAL (OPC UA)
    if variablesG.nivel_local:
        print("🔧 Iniciando nivel LOCAL (OPC UA)...")
        thread_local = Thread(target=GenerarVariablesLocal, name="Thread-LOCAL")
        thread_local.start()
        threads.append(thread_local)
    
    # Nivel 2: GLOBAL (MQTT)
    if variablesG.nivel_global:
        print("🌐 Iniciando nivel GLOBAL (MQTT)...")
        thread_global = Thread(target=GenerarVariablesGlobal, name="Thread-GLOBAL")
        thread_global.start()
        threads.append(thread_global)
    
    # Nivel 3: API (REST)
    if variablesG.nivel_api:
        print("📡 Iniciando nivel API (REST)...")
        thread_api = Thread(target=GenerarVariablesAPI, name="Thread-API")
        thread_api.start()
        threads.append(thread_api)
    
    # Mantener threads activos
    for thread in threads:
        thread.join()
        
def Leer() -> dict:
    """Funcion para leer los datos guardados en la variable global DatosLeidos"""
    variablesG.EventoOPCUA.wait()
    return variablesG.DatosLeidos

def AsignarModo() -> None:
    """Funcion para asignar los modos de lectura de datos
    
    CAMBIO IMPORTANTE: Ahora soporta múltiples niveles simultáneos
    Antes: Solo LOCAL (1) o GLOBAL (2), pero no ambos
    Ahora: LOCAL + GLOBAL + API pueden estar activos al mismo tiempo
    """
    
    datos = ExtraerDatosConfig()
    
    # Verificar cada nivel por separado
    variablesG.nivel_local = datos.get('LOCAL', {}).get('ESTADO', False)
    variablesG.nivel_global = datos.get('GLOBAL', {}).get('ESTADO', False)
    variablesG.nivel_api = datos.get('API', {}).get('ESTADO', False)
    
    # Calcular global_local para compatibilidad con código antiguo
    # 1 = solo LOCAL, 2 = solo GLOBAL, 3+ = múltiples niveles
    GL = 0
    if variablesG.nivel_local:
        GL += 1
    if variablesG.nivel_global:
        GL += 2
    if variablesG.nivel_api:
        GL += 4
    
    variablesG.global_local = GL
    
    # Mostrar configuración
    print("\n📊 Configuración de niveles:")
    print(f"   LOCAL (OPC UA):  {'✓' if variablesG.nivel_local else '✗'}")
    print(f"   GLOBAL (MQTT):   {'✓' if variablesG.nivel_global else '✗'}")
    print(f"   API (REST):      {'✓' if variablesG.nivel_api else '✗'}")
    
    if GL == 0:
        print("\n⚠ Advertencia: Ningún nivel activo")
    
#! ----------------------------------------------------------------
#! ---------------------- Funciones visibles ----------------------
#! ----------------------------------------------------------------
    
def Inicializar() -> None:
    """Funcion para inicializar el sistema de lectura de datos y creación de hilos"""
    
    AsignarModo()
    Thread(target=GenerarDatos, name="Thread-Generador").start()    
    Thread(target=GuardarDatos, name="Thread-Guardador").start()
    

def Prompt() -> str:
    """Funcion para obtener el prompt de ChatGPT
    
    CAMBIO IMPORTANTE: Ahora combina prompts de múltiples niveles activos
    """
    datos = ExtraerDatosConfig()
    prompt_base = datos['CHATGPT']['PROMPT']
    
    # Lista de prompts según niveles activos
    prompts_activos = [prompt_base]
    
    if variablesG.nivel_local:
        if 'PROMPT' in datos.get('LOCAL', {}):
            prompts_activos.append(datos['LOCAL']['PROMPT'])
    
    if variablesG.nivel_global:
        if 'PROMPT' in datos.get('GLOBAL', {}):
            prompts_activos.append(datos['GLOBAL']['PROMPT'])
    
    if variablesG.nivel_api:
        if 'PROMPT' in datos.get('API', {}):
            prompts_activos.append(datos['API']['PROMPT'])
    
    # Combinar todos los prompts
    return " ".join(prompts_activos)

#* ----------------------------------------------------------------
#* ---------------------- Funciones de prueba ---------------------
#* ----------------------------------------------------------------
    
if __name__ == "__main__":
    AsignarModo()
    print(f"\nPrompt combinado:\n{Prompt()}")
