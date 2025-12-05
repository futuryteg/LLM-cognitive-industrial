import json
import paho.mqtt.client as mqtt_client
from json_Hilos import ExtraerDatosConfig
from threading import Thread
import random
import variablesG
import time

valores = {}
"""Diccionario para almacenar los valores de MQTT"""

DECODE_PAYLOAD = True      
"""Enable / disable payload"""

conectado = False
"""Flag para saber si el cliente MQTT está conectado"""

#! ----------------------------------------------------------------
#! ---------------------- Funciones internas ----------------------
#! ----------------------------------------------------------------

def ConectarMQTT():
    """Función para conectar con el broker de MQTT y obtener los datos"""
    global conectado
    
    def ExtraerDatos():
        """Función para extraer los datos de la configuración de MQTT y generar el ID del cliente aleatorio"""
        datos = ExtraerDatosConfig()
        datos["GLOBAL"]["CLIENT_ID"] = f'python-mqtt-{random.randint(0, 10000)}'
        
        return datos["GLOBAL"]
        
    def Conectar(client, userdata, flags, rc):
        """Función para conectar con el broker de MQTT"""
        global conectado
        if rc == 0:
            print("✅ Conectado a MQTT Broker")
            conectado = True
        else:
            print(f"❌ Falló la conexión a MQTT, código de retorno: {rc}")
            conectado = False
    
    try:
        datos = ExtraerDatos()
        client = mqtt_client.Client(client_id=datos["CLIENT_ID"])

        client.on_connect = Conectar
        
        # Intentar conectar con timeout
        try:
            client.connect(datos["BROKER"], datos["PORT"], keepalive=60)
            return client
        except Exception as e:
            print(f"❌ Error al conectar a MQTT: {e}")
            conectado = False
            return None
            
    except Exception as e:
        print(f"❌ Error en configuración MQTT: {e}")
        conectado = False
        return None

def Suscribir(client, variables):
    """Función para suscribirse a los tópicos de MQTT y obtener los datos"""            
    
    def Mensaje(client, userdata, message):
        """Función para obtener los mensajes de MQTT"""
        
        global DECODE_PAYLOAD
        _data = "" ; nombre = "" ; datos = ""

        if DECODE_PAYLOAD:
            try:
                # Parsear el payload directamente sin usar mqtt_spb_wrapper
                _data = json.loads(message.payload.decode())
                nombre = _data["metrics"][0]["name"]
                datos = _data["metrics"][0]["value"]
            except Exception as e:
                # Error al parsear, no es fatal
                pass
        
        valores[nombre] = datos
        
        # Comprobar si variableG.Var es False
        if not variablesG.Var:
            # Si es False, desconectar el cliente
            if client:
                client.disconnect()
    
    if not client:
        return None
    
    try:
        for topic in variables:
            client.subscribe(topic)
        client.on_message = Mensaje
        return client
    except Exception as e:
        print(f"❌ Error al suscribirse a tópicos: {e}")
        return None

def ExtraerTopics() -> dict:
    Topics = {}
    
    for key1, value1 in ExtraerDatosConfig()["GLOBAL"]["VARIABLES"].items():
        if type(value1) == dict:
            for key2, value2 in value1.items():
                if type(value2) == dict:
                    for key3, value3 in value2.items():
                        if type(value3) == dict:
                            for key4, value4 in value3.items():
                                if type(value4) == dict:
                                    for key5, value5 in value4.items():
                                        if type(value5) == dict:
                                            for key6, value6 in value5.items():
                                                Topics[key1 + '/' + key2 + '/' + key3 + '/' + key4 + '/' + key5 + '/' + key6] = value6
                                        else:
                                            Topics[key1 + '/' + key2 + '/' + key3 + '/' + key4 + '/' + key5] = value5
                                else:
                                    Topics[key1 + '/' + key2 + '/' + key3 + '/' + key4] = value4
                        else:
                            Topics[key1 + '/' + key2 + '/' + key3] = value3
                else:
                    Topics[key1 + '/' + key2] = value2
        else:
            Topics[key1] = value1
    
    return Topics

#! ----------------------------------------------------------------
#! ---------------------- Funciones visibles ----------------------
#! ----------------------------------------------------------------

def GenerarDatos():
    """Función para generar datos a partir de MQTT y almacenarlos en un diccionario"""
    global conectado
    
    client = None
    max_reintentos = 3
    reintentos = 0
    
    # Intentar conectar con reintentos
    while reintentos < max_reintentos and variablesG.Var:
        client = ConectarMQTT()
        if client and conectado:
            break
        else:
            reintentos += 1
            if reintentos < max_reintentos:
                print(f"⏳ Reintentando conexión MQTT en 5 segundos... ({reintentos}/{max_reintentos})")
                time.sleep(5)
    
    if not client or not conectado:
        print("❌ No se pudo conectar al broker MQTT después de varios intentos")
        print("ℹ️  El sistema continuará sin datos MQTT")
        # Marcar nivel global como no disponible
        variablesG.nivel_global = False
        return
    
    try:
        client = Suscribir(client, ExtraerTopics())
        
        if client:
            print("✅ Suscrito a tópicos MQTT, esperando mensajes...")
            client.loop_forever()
        else:
            print("❌ No se pudo suscribir a los tópicos")
            variablesG.nivel_global = False
            
    except Exception as e:
        print(f"❌ Error en loop MQTT: {e}")
    finally:
        # Intentar desconectar de forma segura
        if client:
            try:
                if hasattr(client, 'is_connected') and client.is_connected():
                    client.disconnect()
                    print("✅ Cliente MQTT desconectado")
            except Exception as e:
                print(f"⚠️  Error al desconectar MQTT: {e}")

def ExtraerVariables():
    """Función para extraer las variables generadas por MQTT"""
    return valores

#* ----------------------------------------------------------------
#* ---------------------- Funciones de prueba ---------------------
#* ----------------------------------------------------------------
    
if __name__ == "__main__":
    import threading
    variablesG.Var = True
    variablesG.EventoOPCUA = threading.Event()
    variablesG.EventoOPCUA.set()
    
    print("Probando conexión MQTT...")
    GenerarDatos()
