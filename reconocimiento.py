import speech_recognition as sr
from json_Hilos import ExtraerPalabraAct
from chatGPT import EsChatGPTActivadoReconocimiento as EsChatGPTActivado
from difflib import SequenceMatcher as SM
from threading import Thread
import variablesG
import time
import logging
import os
import sys
import contextlib

# Configurar logging para suprimir mensajes innecesarios
logging.basicConfig(level=logging.ERROR)
logging.getLogger('speechrecognition').setLevel(logging.ERROR)

# SUPRESIÓN AGRESIVA DE LOGS ALSA - MÉTODO MEJORADO
# Esto DEBE ir antes de cualquier importación de audio
@contextlib.contextmanager
def suprimir_alsa():
    """Context manager para suprimir todos los logs de ALSA"""
    # Guardar descriptores originales
    old_stderr = os.dup(2)
    old_stdout = os.dup(1)
    
    # Abrir /dev/null
    devnull = os.open(os.devnull, os.O_WRONLY)
    
    try:
        # Redirigir stderr y stdout a /dev/null
        os.dup2(devnull, 2)
        os.dup2(devnull, 1)
        yield
    finally:
        # Restaurar descriptores originales
        os.dup2(old_stderr, 2)
        os.dup2(old_stdout, 1)
        # Cerrar descriptores
        os.close(old_stderr)
        os.close(old_stdout)
        os.close(devnull)

# Variables globales para control
reconocimiento_activo = True
reconocedor_inicializado = False

#! ----------------------------------------------------------------
#! ---------------------- Funciones internas ----------------------
#! ----------------------------------------------------------------

def EsActivacion(texto, nombre_activacion):
    """Función para verificar si el nombre de activación está en el texto con un margen de error"""
    # Se comprueba si el nombre de activación está en el texto con un margen de error
    for palabra in texto.split():
        if SM(None, palabra.lower(), nombre_activacion.lower()).ratio() >= 0.6:
            return palabra
    return None

def inicializar_reconocedor():
    """Inicializa y configura el reconocedor de voz con parámetros optimizados"""
    global reconocedor_inicializado
    
    try:
        print("Configurando reconocedor de voz...")
        
        # Crear reconocedor y micrófono con supresión total
        with suprimir_alsa():
            recognizer = sr.Recognizer()
            
            # Intentar especificar el dispositivo directamente si es posible
            try:
                # En Raspberry Pi, el micrófono USB suele ser el dispositivo 2
                microphone = sr.Microphone(device_index=2)
            except:
                # Si falla, usar el predeterminado
                microphone = sr.Microphone()
        
        # Configuración robusta del micrófono
        print("Ajustando para ruido ambiente...")
        with suprimir_alsa():
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source, duration=1.5)
            
        # Configuración optimizada del reconocedor
        recognizer.dynamic_energy_threshold = True
        recognizer.energy_threshold = 200  # Ajustado para mejor detección
        recognizer.pause_threshold = 0.8   # Pausa antes de considerar que terminó de hablar
        recognizer.phrase_threshold = 0.3  # Tiempo mínimo de audio para procesar
        recognizer.non_speaking_duration = 0.8  # Tiempo de silencio para detener grabación
        
        reconocedor_inicializado = True
        print("Reconocedor configurado correctamente")
        
        return recognizer, microphone
        
    except Exception as e:
        print(f"Error inicializando reconocedor: {e}")
        return None, None

def reconocer_con_reintentos(recognizer, audio, na: str, max_intentos=2):
    """Función para reconocer el audio con reintentos y mejor manejo de errores"""
    
    for intento in range(max_intentos):
        try:
            # Reconoce el audio con supresión
            with suprimir_alsa():
                texto = recognizer.recognize_google(audio, language="es-ES")
            
            if texto:
                print(f"Has dicho: {texto}")
                
                # Verificar si el nombre de activación está en el texto
                palabra_activacion = EsActivacion(texto, na)
                if palabra_activacion:
                    # Extraer el comando después de la palabra de activación
                    texto_lower = texto.lower()
                    palabra_lower = palabra_activacion.lower()
                    
                    # Encontrar la posición de la palabra de activación
                    pos = texto_lower.find(palabra_lower)
                    if pos != -1:
                        # Extraer todo después de la palabra de activación
                        comando = texto[pos + len(palabra_activacion):].strip()
                        
                        if comando:
                            print(f"Activación detectada, comando: '{comando}'")
                            
                            # Procesar mensaje
                            from main import procesarMensaje_fuera            
                            procesarMensaje_fuera(comando)
                        else:
                            print("Activación detectada, pero no se detectó comando específico")
                
                return True  # Reconocimiento exitoso
                        
        except sr.UnknownValueError:
            if intento == 0:  # Solo mostrar en el primer intento
                print("No se pudo entender el audio, reintentando...")
            continue
            
        except sr.RequestError as e:
            if "quota" in str(e).lower():
                print("Límite de cuota alcanzado, usando reconocimiento offline si está disponible")
            else:
                print(f"Error del servicio de reconocimiento: {e}")
            break
            
        except Exception as e:
            print(f"Error inesperado en reconocimiento: {e}")
            break
    
    return False  # No se pudo reconocer

def capturar_audio_con_timeout(recognizer, microphone, timeout=10, phrase_limit=10):
    """Captura audio con timeouts configurables y manejo de errores"""
    try:
        # Capturar audio con supresión total
        with suprimir_alsa():
            with microphone as source:
                audio = recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_limit
                )
        return audio
        
    except sr.WaitTimeoutError:
        # No es un error real, simplemente no se detectó audio
        return None
    except Exception as e:
        print(f"Error capturando audio: {e}")
        return None

def Escuchar(recognizer, microphone, na: str):
    """Función optimizada para escuchar y procesar el audio"""
    if not variablesG.EventoVoz.wait(timeout=1):
        return
    
    print("Escuchando...")
    
    # Capturar audio con timeout
    audio = capturar_audio_con_timeout(recognizer, microphone)
    
    if audio:
        print("Procesando audio...")
        # Procesar en hilo separado para no bloquear
        Thread(target=reconocer_con_reintentos, args=(recognizer, audio, na), daemon=True).start()
    
def verificar_microfono():
    """Verifica que el micrófono esté disponible y funcionando"""
    try:
        # Verificar con supresión total de logs
        with suprimir_alsa():
            # Intentar con dispositivo específico primero
            try:
                microfono_test = sr.Microphone(device_index=2)
            except:
                microfono_test = sr.Microphone()
                
            with microfono_test as source:
                pass  # Solo verificar que se puede acceder
        
        return True
        
    except Exception as e:
        print(f"Error verificando micrófono: {e}")
        
        # Mostrar micrófonos disponibles para debugging
        try:
            with suprimir_alsa():
                microfonos = sr.Microphone.list_microphone_names()
            
            if microfonos:
                print("Micrófonos disponibles:")
                for i, mic in enumerate(microfonos):
                    # Solo mostrar micrófonos relevantes
                    if "usb" in mic.lower() or "gm303" in mic.lower() or "microphone" in mic.lower():
                        print(f"  {i}: {mic} <- RECOMENDADO")
                    else:
                        print(f"  {i}: {mic}")
            else:
                print("No se encontraron micrófonos")
        except:
            pass
        
        return False

def configurar_alsa_raspberry():
    """Configura ALSA específicamente para Raspberry Pi"""
    try:
        # Crear configuración ALSA optimizada
        asoundrc_content = """# Configuración optimizada para Raspberry Pi
pcm.!default {
    type asym
    playback.pcm "plughw:0,0"
    capture.pcm "plughw:2,0"
}

ctl.!default {
    type hw
    card 2
}

pcm.mic {
    type hw
    card 2
    device 0
}
"""
        asoundrc_path = os.path.expanduser('~/.asoundrc')
        
        # Solo escribir si no existe o es diferente
        if not os.path.exists(asoundrc_path):
            with open(asoundrc_path, 'w') as f:
                f.write(asoundrc_content)
            print("Configuración ALSA creada para Raspberry Pi")
    except:
        pass  # No es crítico

def ReconocimientoVozSR():
    """Función principal de reconocimiento de voz mejorada"""
    global reconocimiento_activo
    
    print(f"Iniciando reconocimiento de voz: '{ExtraerPalabraAct()}'")
    
    # Configurar ALSA si estamos en Raspberry Pi
    if os.path.exists('/proc/device-tree/model'):
        try:
            with open('/proc/device-tree/model', 'r') as f:
                if 'Raspberry' in f.read():
                    configurar_alsa_raspberry()
        except:
            pass
    
    # Verificar micrófono antes de iniciar
    if not verificar_microfono():
        print("Error: No se puede acceder al micrófono")
        return
    
    # Inicializar reconocedor
    recognizer, microphone = inicializar_reconocedor()
    if not recognizer or not microphone:
        print("Error: No se pudo inicializar el reconocedor")
        return
    
    # Contador de errores consecutivos
    errores_consecutivos = 0
    max_errores = 5
    
    print("Sistema de reconocimiento listo")
    
    # Bucle principal optimizado
    while variablesG.Var and reconocimiento_activo:
        try:
            Escuchar(recognizer, microphone, ExtraerPalabraAct())
            errores_consecutivos = 0  # Resetear contador en éxito
            
        except OSError as e:
            # Errores específicos de PyAudio
            if e.errno in [-9999, -9988]:
                print("Error de PyAudio detectado")
                errores_consecutivos += 1
                
                if errores_consecutivos >= max_errores:
                    print("Demasiados errores de audio, deteniendo reconocimiento")
                    break
                
                # Pausa antes de reintentar
                time.sleep(2)
            else:
                raise e
                
        except KeyboardInterrupt:
            print("\nInterrupción detectada, deteniendo reconocimiento...")
            break
            
        except Exception as e:
            print(f"Error inesperado: {e}")
            errores_consecutivos += 1
            
            if errores_consecutivos >= max_errores:
                print("Demasiados errores, deteniendo reconocimiento")
                break
            
            time.sleep(1)
    
    print("Reconocimiento de voz desactivado")

def ReconocimientoVozCHATGPT():
    """Función para reconocimiento de voz usando Whisper de OpenAI/ChatGPT"""
    # Implementación futura si se requiere
    print("Reconocimiento con Whisper no implementado aún")

def ReconocimientoVoz():
    """Función principal que selecciona el método de reconocimiento"""
    
    if EsChatGPTActivado():
        ReconocimientoVozCHATGPT()
    else:
        ReconocimientoVozSR()

#! ----------------------------------------------------------------
#! ---------------------- Funciones visibles ----------------------
#! ----------------------------------------------------------------

def IniciarReconocimiento():
    """Función para iniciar el reconocimiento de voz en hilo separado"""
    global reconocimiento_activo
    
    reconocimiento_activo = True
    hilo_reconocimiento = Thread(target=ReconocimientoVoz, daemon=True)
    hilo_reconocimiento.start()
    return hilo_reconocimiento

def DetenerReconocimiento():
    """Función para detener el reconocimiento de voz"""
    global reconocimiento_activo
    reconocimiento_activo = False

def EstadoReconocimiento():
    """Devuelve el estado actual del reconocimiento"""
    return reconocimiento_activo and reconocedor_inicializado

#* ----------------------------------------------------------------
#* ---------------------- Funciones de prueba ---------------------
#* ----------------------------------------------------------------

if __name__ == "__main__":
    # Prueba del sistema de reconocimiento
    print("=== Prueba del sistema de reconocimiento ===")
    
    # Simular variables globales para prueba
    import threading
    variablesG.EventoVoz = threading.Event()
    variablesG.EventoVoz.set()
    variablesG.Var = True
    
    try:
        ReconocimientoVozSR()
    except KeyboardInterrupt:
        print("\nPrueba finalizada")