from json_Hilos import ExtraerDatosConfig
from json_Hilos import GuardarConversacion, ActualizarDatos
from json_Hilos import ContarArchivos
from EyS import Prompt
import variablesG
from datetime import datetime
import re
import os
import time as t
from markdown import Markdown
from io import StringIO
import traceback
import csv
import subprocess
import json

# Configuración específica para Raspberry Pi
EJECUTAR_EN_RASPI = True  # Cambiar a False para PC

# Si estamos en Raspberry Pi, configuramos variables de entorno específicas
if EJECUTAR_EN_RASPI:
    # Configurar variables de entorno para evitar problemas de visualización X11
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    os.environ["DISPLAY"] = ":0"
    # Configurar para uso eficiente de la GPU de la Raspberry Pi
    os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"
    os.environ["OPENCV_VIDEOIO_DEBUG"] = "0"
    # Eliminar buffers extras que puedan causar retrasos
    os.environ["OPENCV_FFMPEG_DEBUG"] = "0"

# Intentar importar llama_cpp para LLMs locales
try:
    from llama_cpp import Llama
    LLAMA_DISPONIBLE = True
except ImportError:
    print("Advertencia: No se pudo importar llama_cpp. Funcionará en modo simulación.")
    LLAMA_DISPONIBLE = False


# Variables globales para el modelo local
modelo_local = None
conversation_history = []

# Variables para métricas (como en el cobot)
METRICAS_ACTIVAS = True
registro_metricas = []
tiempo_carga_modelo = 0

#! ----------------------------------------------------------------
#! ---------------------- Funciones internas ----------------------
#! ----------------------------------------------------------------

def unmarkElemento(element, stream=None):
    if stream is None:
        stream = StringIO()
    if element.text:
        stream.write(element.text)
    for sub in element:
        unmarkElemento(sub, stream)
    if element.tail:
        stream.write(element.tail)
    return stream.getvalue()

def unmark(text):
    # Parcheando la clase Markdown para agregar el formato 'plain'
    Markdown.output_formats["plain"] = unmarkElemento
    __md = Markdown(output_format="plain")
    __md.stripTopLevelTags = False
    return __md.convert(text)

def obtener_temperatura_cpu():
    """Obtiene la temperatura actual de la CPU - Optimizado para Raspberry Pi"""
    try:
        # Método principal para Raspberry Pi
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = float(f.read()) / 1000.0
            return temp
    except:
        try:
            # Método alternativo con comando vcgencmd (específico para Raspberry Pi)
            proceso = subprocess.Popen(['vcgencmd', 'measure_temp'], stdout=subprocess.PIPE)
            salida, _ = proceso.communicate()
            salida = salida.decode('utf-8')
            # El formato de salida es "temp=XX.X'C"
            temperatura = float(salida.replace('temp=', '').replace("'C", ''))
            return temperatura
        except:
            # Si no podemos obtener la temperatura, devolvemos 0
            return 0.0

def getAPIKey() -> str:
    """Función para obtener la ruta del modelo (mantener compatibilidad)"""
    config = ExtraerDatosConfig()
    return config['CHATGPT'].get('MODELO_LOCAL_PATH', '')

def getModelName() -> str:
    """Función para obtener el nombre del modelo local"""
    config = ExtraerDatosConfig()
    return config['CHATGPT'].get('MODELO_LOCAL_NOMBRE', 'Modelo Local')

def getModelPath() -> str:
    """Función para obtener la ruta del modelo local"""
    config = ExtraerDatosConfig()
    return config['CHATGPT'].get('MODELO_LOCAL_PATH', '')

def get_optimized_config_for_raspi():
    """Obtiene configuración optimizada para Raspberry Pi"""
    config = ExtraerDatosConfig()['CHATGPT']
    
    if EJECUTAR_EN_RASPI:
        # Configuración optimizada para Raspberry Pi (similar a Ur_control.py)
        return {
            'n_ctx': config.get('N_CTX', 1024),      # Contexto más pequeño para Raspberry Pi
            'n_threads': config.get('N_THREADS', 4), # 4 núcleos típicos en Raspberry Pi
            'n_batch': config.get('N_BATCH', 48),    # Batch pequeño para memoria limitada
            'max_tokens': config.get('MAX_TOKENS', 200),  # Respuestas más cortas
            'use_mlock': False,                       # No bloquear memoria en Raspberry Pi
            'use_mmap': True,                         # Usar memory mapping para eficiencia
            'low_vram': True                          # Modo de baja VRAM
        }
    else:
        # Configuración estándar para PC
        return {
            'n_ctx': config.get('N_CTX', 2048),
            'n_threads': config.get('N_THREADS', 8),
            'n_batch': config.get('N_BATCH', 128),
            'max_tokens': config.get('MAX_TOKENS', 500),
            'use_mlock': True,
            'use_mmap': True,
            'low_vram': False
        }

def ArchivosAsistente() -> list[str]:
    """Obtiene la lista de archivos para el contexto del asistente"""
    archivos = []
    
    def ArchivosCarpeta(carpeta : dict, url : str) -> None:
        for _, archivo in carpeta.items():
            if archivo['TIPO'] == 'CARPETA':
                if archivo['ARCHIVOS'] != {}:
                    ArchivosCarpeta(archivo['ARCHIVOS'], url + archivo['URL'])
            else:
                archivos.append(url + archivo['URL'])

    try:
        for _, carpeta in ExtraerDatosConfig()['CHATGPT']['ARCHIVOS'].items():
            if carpeta['TIPO'] == 'CARPETA':
                ArchivosCarpeta(carpeta['ARCHIVOS'], variablesG.URL + "/" + carpeta['URL'])
            else:
                archivos.append(variablesG.URL + "/" + carpeta['URL'])
    except Exception as e:
        print(f"Error obteniendo archivos del asistente: {e}")
                
    return archivos

def LeerArchivosContexto() -> str:
    """Lee todos los archivos de contexto y los combina en un string - Optimizado para Raspberry Pi"""
    archivos = ArchivosAsistente()
    contexto_completo = ""
    max_contexto = 5000 if EJECUTAR_EN_RASPI else 15000  # Limitar contexto en Raspberry Pi
    
    for archivo in archivos:
        if os.path.exists(archivo):
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                    # Limitar tamaño del contexto para Raspberry Pi
                    if len(contexto_completo) + len(contenido) > max_contexto:
                        contenido = contenido[:max_contexto - len(contexto_completo)]
                    
                    contexto_completo += f"\n--- Archivo: {os.path.basename(archivo)} ---\n"
                    contexto_completo += contenido + "\n"
                    
                    if len(contexto_completo) >= max_contexto:
                        break
            except Exception as e:
                print(f"Error leyendo {archivo}: {e}")
    
    return contexto_completo

def ExisteAsistente() -> bool:
    """Función para saber si existe configuración previa"""
    return ExtraerDatosConfig()['CHATGPT'].get('ASISTENTE', "") != ""

def ArchivoDatos() -> str:
    """Obtiene la ruta completa del archivo de datos"""
    archivo = ExtraerDatosConfig()['CHATGPT']['HISTORICO']['URL']                
    return variablesG.URL + "/" + archivo

def LimpiarMensaje(mensaje : str) -> str:
    """Función que elimina todas las referencias a archivos del mensaje"""
    mensaje = unmark(re.sub(r'【[^【】]*】', '', mensaje))
    return mensaje

def LeerDatosOperacionales() -> str:
    """Lee los datos operacionales actuales"""
    try:
        datos_path = ArchivoDatos()
        
        if os.path.exists(datos_path):
            size = os.path.getsize(datos_path)
            
            if size > 0:
                with open(datos_path, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                    return json.dumps(datos, indent=2, ensure_ascii=False)
            else:
                # Crear contenido básico si está vacío
                datos_basicos = {
                    "FECHA": datetime.now().strftime("%Y_%m_%d -> %H:%M"),
                    "VARIABLES": {}
                }
                with open(datos_path, 'w', encoding='utf-8') as f:
                    json.dump(datos_basicos, f, indent=4, ensure_ascii=False)
                return json.dumps(datos_basicos, indent=2, ensure_ascii=False)
        else:
            # Crear archivo básico si no existe
            datos_basicos = {
                "FECHA": datetime.now().strftime("%Y_%m_%d -> %H:%M"),
                "VARIABLES": {}
            }
            os.makedirs(os.path.dirname(datos_path), exist_ok=True)
            with open(datos_path, 'w', encoding='utf-8') as f:
                json.dump(datos_basicos, f, indent=4, ensure_ascii=False)
            return json.dumps(datos_basicos, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"Error leyendo datos operacionales: {e}")
        return json.dumps({"FECHA": "Error", "VARIABLES": {}}, indent=2)

def inicializar_modelo_local():
    """Inicializa el modelo LLM local - Optimizado para Raspberry Pi"""
    global modelo_local, tiempo_carga_modelo
    
    if not LLAMA_DISPONIBLE:
        print("llama_cpp no disponible. Funcionando en modo simulación.")
        return None
    
    modelo_path = getModelPath()
    
    if not modelo_path or not os.path.exists(modelo_path):
        print(f"Modelo no encontrado en: {modelo_path}")
        print("Funcionando en modo simulación.")
        return None
    
    try:
        print(f"Cargando modelo local desde: {modelo_path}")
        if EJECUTAR_EN_RASPI:
            print("Configuración optimizada para Raspberry Pi")
        
        # Medir tiempo de carga y temperatura inicial
        inicio_carga = t.time()
        temp_inicial = obtener_temperatura_cpu()
        
        # Obtener configuración optimizada
        config_opt = get_optimized_config_for_raspi()
        
        # Inicializar modelo con configuración optimizada para Raspberry Pi
        modelo = Llama(
            model_path=modelo_path,
            n_ctx=config_opt['n_ctx'],
            n_threads=config_opt['n_threads'],
            n_batch=config_opt['n_batch'],
            use_mlock=config_opt['use_mlock'],
            use_mmap=config_opt['use_mmap'],
            low_vram=config_opt['low_vram'],
            verbose=False
        )
        
        # Registrar tiempo de carga y temperatura
        fin_carga = t.time()
        tiempo_carga_modelo = fin_carga - inicio_carga
        temp_final = obtener_temperatura_cpu()
        
        print(f"Modelo LLM inicializado correctamente en {tiempo_carga_modelo:.2f} segundos")
        if temp_inicial > 0:
            print(f"Temperatura inicial: {temp_inicial:.1f}°C, final: {temp_final:.1f}°C")
            
            # Advertencia si la temperatura es alta
            if temp_final > 75.0:
                print("⚠ Advertencia: Temperatura alta detectada. Considere mejorar la refrigeración.")
        
        # Guardar métricas de carga
        if METRICAS_ACTIVAS:
            guardar_metricas_carga(tiempo_carga_modelo, temp_inicial, temp_final)
        
        return modelo
    except Exception as e:
        print(f"Error al inicializar el modelo: {e}")
        return None

def guardar_metricas_carga(tiempo_carga, temp_inicial, temp_final):
    """Guarda las métricas de carga del modelo"""
    try:
        if not os.path.exists('metricas'):
            os.makedirs('metricas')
        
        fecha_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        modelo_nombre = getModelName()
        dispositivo = "RaspberryPi" if EJECUTAR_EN_RASPI else "PC"
        nombre_archivo = f"metricas/carga_{modelo_nombre}_{dispositivo}_{fecha_hora}.csv"
        
        with open(nombre_archivo, 'w', newline='') as archivo:
            writer = csv.writer(archivo)
            writer.writerow(['modelo', 'dispositivo', 'fecha_hora', 'tiempo_carga', 'temp_inicial', 'temp_final'])
            writer.writerow([modelo_nombre, dispositivo, fecha_hora, tiempo_carga, temp_inicial, temp_final])
        
        print(f"Métricas de carga guardadas en {nombre_archivo}")
    except Exception as e:
        print(f"Error guardando métricas de carga: {e}")

def guardar_metricas_respuesta():
    """Guarda las métricas de respuesta en un archivo CSV"""
    global registro_metricas
    
    if not registro_metricas:
        return
    
    try:
        if not os.path.exists('metricas'):
            os.makedirs('metricas')
        
        fecha_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        modelo_nombre = getModelName()
        dispositivo = "RaspberryPi" if EJECUTAR_EN_RASPI else "PC"
        nombre_archivo = f"metricas/respuestas_{modelo_nombre}_{dispositivo}_{fecha_hora}.csv"
        
        existe_archivo = os.path.exists(nombre_archivo)
        
        with open(nombre_archivo, 'a', newline='') as archivo:
            writer = csv.DictWriter(archivo, fieldnames=[
                'timestamp', 'modelo', 'dispositivo', 'comando', 
                'tiempo_respuesta', 'temp_inicial', 'temp_final'
            ])
            
            if not existe_archivo:
                writer.writeheader()
            
            for metrica in registro_metricas:
                metrica_completa = metrica.copy()
                metrica_completa['modelo'] = modelo_nombre
                metrica_completa['dispositivo'] = dispositivo
                writer.writerow(metrica_completa)
        
        print(f"Métricas de respuesta guardadas en {nombre_archivo}")
        registro_metricas.clear()
    except Exception as e:
        print(f"Error guardando métricas de respuesta: {e}")

def respuestas_fallback(mensaje: str) -> str:
    """Respuestas predefinidas cuando el modelo no está disponible - Optimizado para el contexto industrial"""
    mensaje_lower = mensaje.lower()
    
    # Respuestas relacionadas con el sistema industrial
    if any(palabra in mensaje_lower for palabra in ["estado", "sistema", "funcionamiento"]):
        return "Sistema funcionando correctamente en modo local."
    elif any(palabra in mensaje_lower for palabra in ["datos", "variables", "lecturas"]):
        return "Datos operacionales disponibles para consulta."
    elif any(palabra in mensaje_lower for palabra in ["temperatura", "temp"]):
        temp = obtener_temperatura_cpu()
        if temp > 0:
            return f"Temperatura actual del sistema: {temp:.1f}°C"
        else:
            return "Temperatura del sistema no disponible."
    elif any(palabra in mensaje_lower for palabra in ["humedad"]):
        return "Consultando sensores de humedad en tolvas."
    elif any(palabra in mensaje_lower for palabra in ["mezclador"]):
        return "Estado del mezclador disponible en variables digitales."
    elif any(palabra in mensaje_lower for palabra in ["elevador"]):
        return "Verificando estado del elevador."
    elif any(palabra in mensaje_lower for palabra in ["ayuda", "help", "comandos"]):
        return "Sistema de asistencia industrial disponible. Puede consultar sobre estados, datos y variables del sistema."
    elif any(palabra in mensaje_lower for palabra in ["hola", "saludar", "buenos"]):
        return "Hola, asistente industrial listo para consultas."
    else:
        return "Procesando solicitud en modo simulación local."

def ReiniciarAsistente() -> None:
    """Reinicia el asistente local"""
    global conversation_history, modelo_local
    print("Reiniciando asistente local...")
    conversation_history = []
    # No reinicializar el modelo a menos que sea necesario (es costoso en Raspberry Pi)
    ActualizarDatos()
    InicializarCHATGPT(reinicio=True)

#! ----------------------------------------------------------------
#! ---------------------- Funciones visibles ----------------------
#! ----------------------------------------------------------------

def InicializarCHATGPT(reinicio = False) -> None:
    """Función para inicializar el modelo local (manteniendo nombre para compatibilidad)"""
    global conversation_history, modelo_local
    
    dispositivo = "Raspberry Pi" if EJECUTAR_EN_RASPI else "PC"
    print(f"Inicializando sistema con modelo local en {dispositivo}...")
    
    # Verificar configuración
    modelo_path = getModelPath()
    if not modelo_path:
        print("Error: No se ha configurado la ruta del modelo local en CHATGPT.MODELO_LOCAL_PATH")
        return
    
    # Inicializar historial de conversación
    if reinicio:
        conversation_history = []
    
    # Inicializar modelo si no existe
    if modelo_local is None:
        modelo_local = inicializar_modelo_local()
    
    # Leer contexto de archivos
    contexto = LeerArchivosContexto()
    if contexto:
        print(f"Contexto cargado: {len(contexto)} caracteres")
    
    # Verificar archivos si es necesario
    if not reinicio and ExisteAsistente():
        try:
            if not (len(ArchivosAsistente()) == ContarArchivos()):
                print("Actualizando archivos...")
                ReiniciarAsistente()
                return
        except Exception as e:
            print(f"Error verificando archivos: {e}")
    else:
        # Actualizar datos de configuración
        timestamp = str(datetime.now().strftime("%Y_%m_%d"))
        ActualizarDatos(Asistente=f"modelo_local_{timestamp}")
    
    print("Sistema local inicializado correctamente")

def ConsultaChatGPT(mensaje: str) -> str:
    """Función para generar una consulta al modelo local (manteniendo nombre para compatibilidad)"""
    global conversation_history, modelo_local, registro_metricas
    
    print("Enviando mensaje al modelo local...")
    
    try:
        # Verificar que tenemos modelo o configuración
        if modelo_local is None and not getModelPath():
            return "Error: Modelo local no configurado correctamente"
        
        # Verificar y esperar archivo de datos
        datos_path = ArchivoDatos()
        max_intentos = 5
        intento = 0
        
        while not os.path.exists(datos_path) or os.path.getsize(datos_path) == 0:
            intento += 1
            if intento > max_intentos:
                break
            t.sleep(1)
        
        # Leer datos operacionales actuales
        datos_operacionales = LeerDatosOperacionales()
        
        # Leer contexto de archivos (limitado en Raspberry Pi)
        contexto_archivos = LeerArchivosContexto()
        
        # Si no tenemos modelo, usar respuestas fallback
        if modelo_local is None:
            return respuestas_fallback(mensaje)
        
        # Construir el prompt del sistema (más corto para Raspberry Pi)
        prompt_base = Prompt()
        
        if EJECUTAR_EN_RASPI:
            # Prompt más corto para Raspberry Pi
            prompt_sistema = f"""{prompt_base}

DATOS OPERACIONALES:
{datos_operacionales[:1000]}  # Limitar datos en Raspberry Pi

Eres un asistente de IA para sistema industrial. Responde de forma breve y precisa."""
        else:
            # Prompt completo para PC
            prompt_sistema = f"""{prompt_base}

CONTEXTO DE ARCHIVOS Y DOCUMENTACIÓN:
{contexto_archivos}

DATOS OPERACIONALES ACTUALES:
{datos_operacionales}

Eres un asistente de IA para un sistema de control industrial Industry 5.0. Responde de forma clara y concisa."""

        # Medir tiempo de inicio y temperatura
        inicio_respuesta = t.time()
        temp_inicial = obtener_temperatura_cpu()
        
        # Preparar el prompt completo
        prompt_completo = f"""[INST] Eres un asistente industrial que SOLO habla español.
        IMPORTANTE: Responde SIEMPRE en español, de forma MUY BREVE y directa (máximo 2-3 oraciones).

        Usuario: {mensaje}
        Asistente (en español, breve): [/INST]"""
        
        # Obtener configuración optimizada
        config_opt = get_optimized_config_for_raspi()
        
        # Generar respuesta
        response = modelo_local(
            prompt_completo,
            max_tokens=config_opt['max_tokens'],
            temperature=0.3,
            top_p=0.95,
            repeat_penalty=1.15,
            stop=["[INST]", "</s>", "\n\nUsuario:", "\n\n", "User:"]
        )
        
        respuesta = response['choices'][0]['text'].strip()
        
        # Limpiar la respuesta de posibles artefactos
        if respuesta.startswith("Assistant:") or respuesta.startswith("Asistente:"):
            respuesta = respuesta.split(":", 1)[1].strip()
        
        # Medir tiempo final y temperatura
        fin_respuesta = t.time()
        temp_final = obtener_temperatura_cpu()
        tiempo_total = fin_respuesta - inicio_respuesta
        
        # Guardar en historial (limitado en Raspberry Pi)
        conversation_history.append({"role": "user", "content": mensaje})
        conversation_history.append({"role": "assistant", "content": respuesta})
        
        # Mantener historial más limitado en Raspberry Pi
        max_history = 10 if EJECUTAR_EN_RASPI else 20
        if len(conversation_history) > max_history:
            conversation_history = conversation_history[-max_history:]
        
        # Guardar conversación para registro
        conversacion_completa = {
            "timestamp": datetime.now().isoformat(),
            "user_message": mensaje,
            "assistant_response": respuesta,
            "processing_time": tiempo_total,
            "device": "RaspberryPi" if EJECUTAR_EN_RASPI else "PC"
        }
        
        try:
            GuardarConversacion(conversacion_completa)
        except Exception as e:
            print(f"Error guardando conversación: {e}")
        
        # Guardar métricas
        if METRICAS_ACTIVAS:
            metrica = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'comando': mensaje,
                'tiempo_respuesta': tiempo_total,
                'temp_inicial': temp_inicial,
                'temp_final': temp_final
            }
            registro_metricas.append(metrica)
            print(f"Tiempo de respuesta: {tiempo_total:.2f}s")
            if temp_inicial > 0:
                print(f"Temperatura: {temp_final:.1f}°C")
            
            # Advertencias para Raspberry Pi
            if EJECUTAR_EN_RASPI and temp_final > 70.0:
                print("⚠ Temperatura alta en Raspberry Pi")
            
            # Guardar cada 5 comandos en Raspberry Pi (menos I/O)
            umbral_guardado = 5 if EJECUTAR_EN_RASPI else 10
            if len(registro_metricas) >= umbral_guardado:
                guardar_metricas_respuesta()
        
        return LimpiarMensaje(respuesta)
        
    except Exception as e:
        print(f"Error general: {str(e)}")
        
        # Solo reiniciar si no es un error de configuración
        if "configurad" not in str(e).lower() and "ruta" not in str(e).lower():
            try:
                ReiniciarAsistente()
                # Intento único de reenvío
                if len(conversation_history) == 0:
                    return ConsultaChatGPT(mensaje)
            except:
                pass
        
        # En caso de error, usar respuesta fallback
        return respuestas_fallback(mensaje)

#todo ----------------------------------------------------------- Funciones para conversion de voz

def EsChatGPTActivadoSintesis() -> bool:
    """Función para saber si está activado para texto-voz"""
    datos = ExtraerDatosConfig()
    return datos['CHATGPT']['ACTIVAR_VOZ']

def EsChatGPTActivadoReconocimiento() -> bool:
    """Función para saber si está activado para voz-texto"""
    datos = ExtraerDatosConfig()
    return datos['CHATGPT']['ACTIVAR_RECONOCIMIENTO']

def VozChatGPT(texto: str, URL: str) -> None:
    """Función para síntesis de voz - usando gTTS ya que no hay TTS local"""
    try:
        from gtts import gTTS
        tts = gTTS(text=texto, lang='es')
        tts.save(URL)
    except Exception as e:
        print(f"Error en síntesis de voz: {e}")

#* ----------------------------------------------------------------
#* ---------------------- Funciones de prueba ---------------------
#* ----------------------------------------------------------------

if __name__ == '__main__':
    print("=== Prueba de chatGPT_local.py - Optimizado para Raspberry Pi ===")
    print(f"Dispositivo: {'Raspberry Pi' if EJECUTAR_EN_RASPI else 'PC'}")
    print(f"URL base: {variablesG.URL}")
    print(f"Ruta del modelo: {getModelPath()}")
    print(f"Temperatura CPU: {obtener_temperatura_cpu():.1f}°C")
    print(f"Archivos del asistente: {ArchivosAsistente()}")
    
    # Prueba de inicialización
    InicializarCHATGPT()
    
    # Prueba de consulta
    respuesta = ConsultaChatGPT("¿Cómo está el sistema?")
    print(f"Respuesta: {respuesta}")
