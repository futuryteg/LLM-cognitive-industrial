from opcua import Client
from opcua.ua.uaerrors import BadNodeIdUnknown
from json_Hilos import ExtraerDatosConfig
import variablesG
import time

valores = {}
"""Diccionario para almacenar los valores de las variables del cliente OPCUA"""

CLIENTE = None
"""Variable para almacenar el cliente OPCUA"""

conectado = False
"""Flag para saber si el cliente está conectado"""

#! ----------------------------------------------------------------
#! ---------------------- Funciones internas ----------------------
#! ----------------------------------------------------------------

def DatosClienteOPCUA() -> str:
    """Función para extraer los datos de la configuración del cliente OPCUA"""
    
    datos = ExtraerDatosConfig()
    
    ip = datos['LOCAL']["IP_PLC"]
    port = datos['LOCAL']["PORT"]
    
    url = f"opc.tcp://{ip}:{port}"
        
    return url

def ExtraerVariablesNombre() -> dict[str]:
    """Función para extraer las variables del cliente OPCUA"""
    
    datos = ExtraerDatosConfig()
    return datos['LOCAL']['VARIABLES']

def CC_OPCUA():
    """Función para conectar el cliente OPCUA al servidor"""
    global conectado
    
    try:
        CLIENTE.connect()
        conectado = True
        print("✅ Cliente OPC UA Conectado")
        return True
    except Exception as e:
        conectado = False
        print(f"❌ Error al conectar Cliente OPC UA: {e}")
        return False
    
def DC_ClienteOPCUA():
    """Función para desconectar el cliente OPCUA del servidor"""
    global conectado
    
    if not conectado or CLIENTE is None:
        print("ℹ️  Cliente OPC UA no estaba conectado")
        return
    
    try:
        CLIENTE.disconnect()
        conectado = False
        print("✅ Cliente OPC UA Desconectado")
    except Exception as e:
        conectado = False
        print(f"⚠️  Error al desconectar Cliente OPC UA: {e}")
    
    
#! ----------------------------------------------------------------
#! ---------------------- Funciones visibles ----------------------
#! ----------------------------------------------------------------
    
def GenerarDatos():
    """Función para generar los datos del cliente OPCUA con manejo robusto de errores"""
    global CLIENTE, conectado
    
    CLIENTE = Client(DatosClienteOPCUA())
    
    max_reintentos_conexion = 3
    reintentos = 0
    
    # Intentar conectar con reintentos
    while reintentos < max_reintentos_conexion and variablesG.Var:
        if CC_OPCUA():
            break
        else:
            reintentos += 1
            if reintentos < max_reintentos_conexion:
                print(f"⏳ Reintentando conexión OPC UA en 5 segundos... ({reintentos}/{max_reintentos_conexion})")
                time.sleep(5)
    
    if not conectado:
        print("❌ No se pudo conectar al servidor OPC UA después de varios intentos")
        print("ℹ️  El sistema continuará sin datos OPC UA")
        # Marcar nivel local como no disponible
        variablesG.nivel_local = False
        return
    
    # Loop principal de lectura
    try:
        errores_consecutivos = 0
        max_errores = 5
        
        while variablesG.Var and conectado:
            try:
                variables = ExtraerVariablesNombre()
                
                for _, iv in variables.items():
                    for jc, jv in iv.items():
                        for kc, kv in jv.items():
                            if type(kv) == dict:
                                for lc, lv in kv.items():
                                    if type(lv) == dict:
                                        for varc, varv in lv.items():
                                            if type(varv) == dict:
                                                for mc, mv in varv.items():
                                                    try:
                                                        id = f'ns={jc};s="{kc}"."{lc}"[{varc}]."{mc}"'
                                                        valores[mv] = CLIENTE.get_node(id).get_value()
                                                    except Exception as e:
                                                        # Error en variable específica, no fatal
                                                        pass
                                            else:
                                                try:
                                                    id = f'ns={jc};s="{kc}"."{lc}"[{varc}]'
                                                    valores[varv] = CLIENTE.get_node(id).get_value()
                                                except Exception as e:
                                                    pass
                                    else:
                                        try:
                                            id = f'ns={jc};s="{kc}"."{lc}"'
                                            valores[lv] = CLIENTE.get_node(id).get_value()
                                        except Exception as e:
                                            pass
                            else:
                                try:
                                    id = f'ns={jc};s="{kc}"'
                                    valores[kv] = CLIENTE.get_node(id).get_value()
                                except Exception as e:
                                    pass
                
                # Reset contador de errores si la lectura fue exitosa
                errores_consecutivos = 0
                
                # Pequeña pausa entre lecturas
                time.sleep(0.1)
                
            except Exception as e:
                errores_consecutivos += 1
                print(f"⚠️  Error en lectura OPC UA: {e}")
                
                if errores_consecutivos >= max_errores:
                    print(f"❌ Demasiados errores consecutivos ({max_errores}), deteniendo OPC UA")
                    break
                
                time.sleep(1)
        
    except BadNodeIdUnknown as e:
        print(f"❌ El nodo al que se intenta acceder no existe: {e}")
    except Exception as e:
        print(f"❌ Error general en GenerarDatos OPC UA: {e}")
    finally:
        DC_ClienteOPCUA()

def ExtraerVariables():
    """Función para extraer los datos generados por el cliente OPCUA"""
    return valores

#* ----------------------------------------------------------------
#* ---------------------- Funciones de prueba ---------------------
#* ----------------------------------------------------------------
    
if __name__ == "__main__":
    import threading
    variablesG.Var = True
    variablesG.EventoOPCUA = threading.Event()
    variablesG.EventoOPCUA.set()
    
    print("Probando conexión OPC UA...")
    GenerarDatos()
