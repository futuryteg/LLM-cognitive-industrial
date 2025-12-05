from threading import Event
import os


EventoVoz = Event() 
"""Evento para activar el reconocimiento de voz"""

EventoHablar = Event() 
"""Evento para activar el reconocimiento de voz"""

EventoOPCUA = Event() 
"""Evento para activar la lectura de datos"""

global_local = 0 
"""Variable para saber si se está en modo local o global
VALORES:
0 = Ningún nivel activo
1 = Solo LOCAL (OPC UA)
2 = Solo GLOBAL (MQTT)
3 = LOCAL + GLOBAL
4 = Solo API (REST)
5 = LOCAL + API
6 = GLOBAL + API
7 = LOCAL + GLOBAL + API (MULTINIVEL COMPLETO)
"""

# NUEVO: Variables para control independiente de cada nivel
nivel_local = False
"""True si el nivel LOCAL (OPC UA) está activo"""

nivel_global = False
"""True si el nivel GLOBAL (MQTT) está activo"""

nivel_api = False
"""True si el nivel API (REST ERP/MES) está activo"""

DatosLeidos = {} 
"""Diccionario para almacenar los datos leídos
Estructura:
{
    'LOCAL': {...},   # Datos OPC UA
    'GLOBAL': {...},  # Datos MQTT
    'API': {...}      # Datos REST API
}
"""

Var = True
"""Variable para saber si el programa está encendido o apagado"""

Interfaz = None
"""Variable para almacenar la interfaz"""

URL = os.path.dirname(os.path.abspath(__file__)).replace("\\","/") + '/src' 
"""URL de la carpeta src"""
