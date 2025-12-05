from gtts import gTTS
import pygame
import os
import sys
import time
import threading
from threading import Lock
from chatGPT import VozChatGPT
from chatGPT import EsChatGPTActivadoSintesis as EsChatGPTActivado
import variablesG

# Inicializar pygame mixer una sola vez al importar el módulo
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# Lock para evitar reproducción simultánea
reproduccion_lock = Lock()

# Variables de control
sintesis_activa = True

#! ----------------------------------------------------------------
#! ---------------------- Funciones internas ----------------------
#! ----------------------------------------------------------------

def limpiar_archivo_temporal(archivo_path: str, max_intentos: int = 3) -> None:
    """Función mejorada para eliminar archivos temporales con reintentos"""
    for intento in range(max_intentos):
        try:
            if os.path.exists(archivo_path):
                # Asegurarse que pygame no está usando el archivo
                pygame.mixer.music.stop()
                time.sleep(0.1)
                os.remove(archivo_path)
                return
        except PermissionError:
            time.sleep(0.1 * (intento + 1))
        except Exception as e:
            if intento == max_intentos - 1:
                print(f"No se pudo eliminar archivo temporal: {e}")
            break

def generar_nombre_archivo_unico(base_name: str = "audio", extension: str = ".mp3") -> str:
    """Genera un nombre de archivo único para evitar conflictos"""
    timestamp = str(int(time.time() * 1000))
    thread_id = threading.current_thread().ident
    return f"{base_name}_{timestamp}_{thread_id}{extension}"

    #? ----------------------------------------------------------------
    #? ----------- GTTS con Pygame - Síntesis optimizada -------------
    #? ----------------------------------------------------------------

def TextaVozGTTS_pygame(texto: str, lenguaje: str = 'es', archivo: str = None) -> bool:
    """Función para conversión de texto a voz con gTTS y pygame"""
    
    if not texto or not texto.strip():
        print("Texto vacío, no se puede sintetizar")
        return False
    
    # Generar nombre único si no se proporciona
    if archivo is None:
        archivo = generar_nombre_archivo_unico()
    
    archivo_completo = os.path.join(variablesG.URL, archivo)
    
    try:
        with reproduccion_lock:  # Evitar reproducción simultánea
            print(f"Sintetizando: '{texto[:50]}{'...' if len(texto) > 50 else ''}'")
            
            # Crear síntesis de voz
            tts = gTTS(text=texto, lang=lenguaje, slow=False)
            tts.save(archivo_completo)
            
            # Verificar que el archivo se creó correctamente
            if not os.path.exists(archivo_completo):
                print("Error: No se pudo crear el archivo de audio")
                return False
            
            # Reproducir con pygame
            try:
                pygame.mixer.music.load(archivo_completo)
                pygame.mixer.music.play()
                
                # Esperar a que termine de reproducir
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                    # Permitir interrumpir si es necesario
                    if not variablesG.Var:
                        pygame.mixer.music.stop()
                        break
                
            except pygame.error as e:
                print(f"Error de pygame al reproducir: {e}")
                # Intentar método alternativo con subprocess
                import subprocess
                try:
                    subprocess.run(['mpg123', '-q', archivo_completo], 
                                 check=True, timeout=30)
                except:
                    print("No se pudo reproducir el audio")
                    return False
            
            # Pequeña pausa para asegurar que se liberó el archivo
            time.sleep(0.1)
            
            # Limpiar archivo temporal
            limpiar_archivo_temporal(archivo_completo)
            
        return True
        
    except Exception as e:
        print(f"Error en síntesis gTTS: {e}")
        limpiar_archivo_temporal(archivo_completo)
        return False

    #? ----------------------------------------------------------------
    #? -------------- ChatGPT/Claude - Síntesis de voz ---------------
    #? ----------------------------------------------------------------

def TextaVozChatGPT_pygame(texto: str, archivo: str = None) -> bool:
    """Función para conversión de texto a voz con ChatGPT/Claude y pygame"""
    
    if not texto or not texto.strip():
        print("Texto vacío, no se puede sintetizar")
        return False
    
    # Generar nombre único si no se proporciona
    if archivo is None:
        archivo = generar_nombre_archivo_unico()
    
    archivo_completo = os.path.join(variablesG.URL, archivo)
    
    try:
        with reproduccion_lock:
            print(f"Sintetizando con IA: '{texto[:50]}{'...' if len(texto) > 50 else ''}'")
            
            # Generar audio con ChatGPT/Claude
            VozChatGPT(texto, archivo_completo)
            
            # Verificar que el archivo se creó correctamente
            if not os.path.exists(archivo_completo):
                print("Error: No se pudo crear el archivo de audio con IA")
                return False
            
            # Reproducir con pygame
            try:
                pygame.mixer.music.load(archivo_completo)
                pygame.mixer.music.play()
                
                # Esperar a que termine de reproducir
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                    if not variablesG.Var:
                        pygame.mixer.music.stop()
                        break
                        
            except pygame.error as e:
                print(f"Error de pygame: {e}")
                return False
            
            # Limpiar archivo temporal
            time.sleep(0.1)
            limpiar_archivo_temporal(archivo_completo)
            
        return True
        
    except Exception as e:
        print(f"Error en síntesis con IA: {e}")
        limpiar_archivo_temporal(archivo_completo)
        return False

def verificar_dependencias_audio():
    """Verifica que las dependencias de audio estén disponibles"""
    try:
        # Verificar gTTS
        test_tts = gTTS(text="test", lang='es')
        
        # Verificar pygame mixer
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        return True
    except Exception as e:
        print(f"Error verificando dependencias de audio: {e}")
        return False

#! ----------------------------------------------------------------
#! ---------------------- Funciones visibles ----------------------
#! ----------------------------------------------------------------

def TextaVoz(texto: str, archivo: str = "audio.mp3") -> bool:
    """Función principal para conversión de texto a voz con pygame"""
    
    if not sintesis_activa:
        print("Síntesis de voz desactivada")
        return False
    
    if not texto or not texto.strip():
        print("No hay texto para sintetizar")
        return False
    
    # Limpiar el texto
    texto = texto.strip()
    
    # Limitar longitud para evitar problemas
    if len(texto) > 500:
        print("Texto muy largo, truncando...")
        texto = texto[:500]
    
    try:
        # NO usar EventoHablar - simplificar el proceso
        # Seleccionar método de síntesis
        if EsChatGPTActivado():
            return TextaVozChatGPT_pygame(texto, archivo)
        else:
            return TextaVozGTTS_pygame(texto, archivo=archivo)
            
    except Exception as e:
        print(f"Error general en síntesis: {e}")
        return False

def hablar_simple(texto: str) -> None:
    """Función simple de síntesis para compatibilidad - usando pygame"""
    if not texto or not texto.strip():
        return
        
    try:
        # Crear archivo de audio
        tts = gTTS(text=texto, lang='es')
        archivo_temp = os.path.join(variablesG.URL, "temp_audio.mp3")
        tts.save(archivo_temp)
        
        # Reproducir con pygame
        with reproduccion_lock:
            pygame.mixer.music.load(archivo_temp)
            pygame.mixer.music.play()
            
            # Esperar a que termine
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                if not variablesG.Var:
                    pygame.mixer.music.stop()
                    break
        
        # Limpiar archivo
        time.sleep(0.1)
        try:
            os.remove(archivo_temp)
        except:
            pass
            
    except Exception as e:
        print(f"Error en hablar_simple: {e}")

def TextaVozAsincrono(texto: str, archivo: str = "audio.mp3") -> threading.Thread:
    """Ejecuta síntesis de voz en hilo separado para no bloquear"""
    
    def _sintesis_asincrona():
        TextaVoz(texto, archivo)
    
    hilo = threading.Thread(target=_sintesis_asincrona, daemon=True)
    hilo.start()
    return hilo

def InicializarSintesis() -> bool:
    """Inicializa el sistema de síntesis y verifica dependencias"""
    global sintesis_activa
    
    print("Inicializando sistema de síntesis con pygame...")
    
    # Verificar pygame mixer
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    except Exception as e:
        print(f"Error inicializando pygame mixer: {e}")
        sintesis_activa = False
        return False
    
    if not verificar_dependencias_audio():
        print("Error: Dependencias de audio no disponibles")
        sintesis_activa = False
        return False
    
    # Verificar que el directorio existe
    if not os.path.exists(variablesG.URL):
        try:
            os.makedirs(variablesG.URL, exist_ok=True)
        except Exception as e:
            print(f"Error creando directorio: {e}")
            sintesis_activa = False
            return False
    
    sintesis_activa = True
    print("Sistema de síntesis con pygame inicializado correctamente")
    return True

def DetenerSintesis():
    """Detiene el sistema de síntesis"""
    global sintesis_activa
    
    # Detener cualquier reproducción en curso
    try:
        pygame.mixer.music.stop()
    except:
        pass
    
    sintesis_activa = False
    print("Sistema de síntesis detenido")

def EstadoSintesis() -> bool:
    """Devuelve el estado actual del sistema de síntesis"""
    return sintesis_activa

def LimpiarArchivosTemporales():
    """Limpia archivos temporales de audio que puedan haber quedado"""
    try:
        # Detener música si está sonando
        pygame.mixer.music.stop()
        
        if os.path.exists(variablesG.URL):
            for archivo in os.listdir(variablesG.URL):
                if (archivo.startswith("audio_") or archivo.startswith("temp_")) and archivo.endswith(".mp3"):
                    archivo_path = os.path.join(variablesG.URL, archivo)
                    limpiar_archivo_temporal(archivo_path)
        print("Archivos temporales de audio limpiados")
    except Exception as e:
        print(f"Error limpiando archivos temporales: {e}")

#* ----------------------------------------------------------------
#* ---------------------- Funciones de prueba ---------------------
#* ----------------------------------------------------------------

if __name__ == "__main__":
    # Prueba del sistema de síntesis con pygame
    print("=== Prueba del sistema de síntesis con pygame ===")
    
    # Simular variables globales para prueba
    import threading
    
    class VariablesTest:
        def __init__(self):
            self.Var = True
            self.URL = "./src"  # Asegurar que apunta a la carpeta correcta
    
    variablesG = VariablesTest()
    
    # Crear carpeta src si no existe
    if not os.path.exists(variablesG.URL):
        os.makedirs(variablesG.URL)
    
    # Inicializar sistema
    if InicializarSintesis():
        print("Probando síntesis con pygame...")
        TextaVoz("Hola, esta es una prueba del sistema de síntesis con pygame")
        
        # Esperar un poco para que termine
        time.sleep(2)
        
        # Probar función simple
        print("Probando función hablar_simple...")
        hablar_simple("Esta es la función simple")
        
        # Limpiar archivos de prueba
        LimpiarArchivosTemporales()
    else:
        print("No se pudo inicializar el sistema de síntesis")
    
    # Limpiar pygame
    pygame.mixer.quit()
