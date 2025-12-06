# Multimodal Cognitive Architecture with Local Generative AI for Industrial Control of Concrete Plants on Edge Devices

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%205-red.svg)](https://www.raspberrypi.com/)

Sistema conversacional con IA local para acceso cognitivo a información industrial distribuida a través de lenguaje natural. Integra reconocimiento de voz en español, modelo Mistral-7B cuantizado, y protocolos industriales heterogéneos (OPC UA, MQTT, REST API) ejecutándose completamente en edge devices.

## Tabla de Contenidos

- [Características](#características)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Arquitectura](#arquitectura)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Troubleshooting](#troubleshooting)
- [Publicación](#publicación)
- [Licencia](#licencia)

## Características

- **Interfaz de Voz**: Reconocimiento y síntesis de voz en español (manos libres)
- **IA Local**: Modelo Mistral-7B-Instruct-v0.2 cuantizado (GGUF Q4_0, 3.82 GB)
- **Integración Industrial**: OPC UA, MQTT, REST API para acceso multinivel
- **Privacidad Total**: Inferencia 100% local sin dependencias cloud
- **Edge Computing**: Optimizado para Raspberry Pi 5 (8 GB RAM)
- **Arquitectura Multinivel**: Acceso unificado a sensores, PLC, SCADA, MES y ERP

## Requisitos

### Hardware

- **Raspberry Pi 5** (8 GB RAM recomendado)
- Micrófono USB compatible (ej: GM303)
- Sistema de refrigeración activa
- Tarjeta microSD (32 GB mínimo)
- Conexión Ethernet a red industrial

### Software

- **Sistema Operativo**: Raspberry Pi OS (64-bit)
- **Python**: 3.11.2 o superior
- **Memoria disponible**: ~3.82 GB para el modelo

### Sistemas Industriales (Opcional)

- Servidor OPC UA (Levels 2-3: PLC/SCADA)
- Broker MQTT (Level 1: sensores/actuadores)
- APIs REST (Levels 4-5: MES/ERP)

## Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/your-username/industrial-cognitive-assistant.git
cd industrial-cognitive-assistant
```

### 2. Crear Entorno Virtual

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Instalar llama.cpp con Optimizaciones ARM

```bash
# Instalar OpenBLAS para aceleración en ARM
sudo apt-get update
sudo apt-get install libopenblas-dev

# Compilar llama-cpp-python con optimizaciones
CMAKE_ARGS="-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS" \
pip install llama-cpp-python==0.3.16 --force-reinstall --no-cache-dir
```

### 5. Descargar el Modelo Mistral-7B

```bash
# Crear directorio de modelos
mkdir -p models

# Descargar desde Hugging Face
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_0.gguf \
  -O models/mistral-7b-instruct-v0.2.Q4_0.gguf
```

### 6. Configurar Audio (Raspberry Pi)

```bash
# Listar dispositivos de audio disponibles
python3 -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"

# Configurar ALSA (el sistema lo hace automáticamente, pero puedes verificar)
cat ~/.asoundrc
```

## Configuración

### Archivo `config.json`

Ubicación: `src/config.json`

#### 1. Configuración del Modelo

```json
{
  "CHATGPT": {
    "MODELO_LOCAL_PATH": "/ruta/absoluta/models/mistral-7b-instruct-v0.2.Q4_0.gguf",
    "MODELO_LOCAL_NOMBRE": "Mistral-7B",
    "PROMPT": "AI assistant for monitoring and operational management with real-time data and analysis. Spanish only, very brief responses.",
    "PALABRA_ACTIVACION": "asistente",
    "MAX_TOKENS": 200,
    "TEMPERATURA": 0.3,
    "N_CTX": 1024,
    "N_THREADS": 4,
    "N_BATCH": 48
  }
}
```

**Parámetros clave:**
- `MODELO_LOCAL_PATH`: Ruta al archivo .gguf del modelo
- `PALABRA_ACTIVACION`: Palabra para activar el reconocimiento
- `TEMPERATURA`: Control de aleatoriedad (0.3 = más determinista)
- `N_CTX`: Tamaño de contexto (tokens)
- `N_THREADS`: Núcleos de CPU a usar

#### 2. Configuración de Nivel LOCAL (OPC UA)

```json
{
  "LOCAL": {
    "ESTADO": true,
    "IP_PLC": "192.168.1.10",
    "PORT": 4840,
    "PROMPT": "On-site plant supervision and local management.",
    "VARIABLES": {
      "85": {
        "3": {
          "DBResources": {
            "Humidity": {
              "1": "Humidity Hopper 1",
              "2": "Humidity Hopper 2"
            }
          }
        }
      }
    }
  }
}
```

**Configuración:**
- `ESTADO`: `true` para activar este nivel
- `IP_PLC`: Dirección IP del servidor OPC UA
- `VARIABLES`: Estructura jerárquica de nodos OPC UA

#### 3. Configuración de Nivel GLOBAL (MQTT)

```json
{
  "GLOBAL": {
    "ESTADO": true,
    "BROKER": "mqtt.example.com",
    "PORT": 1883,
    "PROMPT": "Central office, comprehensive vision across all facilities.",
    "VARIABLES": {
      "spBv1.0": {
        "GroupEMQX": {
          "DDATA": {
            "Edge": {
              "Server_Interface_1": "Test Variable 1"
            }
          }
        }
      }
    }
  }
}
```

#### 4. Configuración de Nivel API (REST)

```json
{
  "API": {
    "ESTADO": true,
    "BASE_URL": "http://localhost:5000",
    "TIMEOUT": 5,
    "PROMPT": "Multi-level integration with MES and ERP systems.",
    "ENDPOINTS": {
      "mes_ordenes": "/api/mes/ordenes",
      "erp_inventario": "/api/erp/inventario",
      "health": "/api/health"
    }
  }
}
```

### Estructura de Carpetas

```
industrial-cognitive-assistant/
├── src/
│   ├── config.json          # Configuración principal
│   ├── Imagen.png           # Icono del chatbot
│   └── DatosAsistente/      # Datos adicionales del sistema
│       └── Manuales/        # Manuales y documentación
├── main.py                  # Punto de entrada
├── chatGPT.py              # Gestión del LLM
├── reconocimiento.py       # Reconocimiento de voz
├── sintesis.py             # Síntesis de voz
├── localC.py               # Cliente OPC UA
├── globalC.py              # Cliente MQTT
├── apiC.py                 # Cliente REST API
├── EyS.py                  # Coordinación de datos
├── IG.py                   # Interfaz gráfica
├── variablesG.py           # Variables globales
├── json_Hilos.py           # Gestión de configuración
├── requirements.txt        # Dependencias
└── README.md
└── LICENSE
```

## Uso

### Inicio Rápido

```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar el sistema
python main.py
```

### Modo de Operación

El sistema ofrece dos modalidades de interacción:

#### 1. Interfaz de Voz (Recomendado)

1. Espera el mensaje "Escuchando..."
2. Di la palabra de activación: **"asistente"** (configurable)
3. Formula tu pregunta en lenguaje natural
4. El sistema procesará y responderá por voz

**Ejemplo:**
```
Usuario: "Asistente, ¿cuál es el estado del pedido 2847?"
Sistema: "Consultando... El pedido 2847 está en producción, estimado de finalización: 14:30h"
```

#### 2. Interfaz Gráfica

- Escribe tu consulta en el cuadro de texto
- Presiona Enter o clic en "Enviar"
- La respuesta aparecerá en la ventana de chat

### Ejemplos de Consultas

#### Consultas Simples (Nivel único)
```
"¿Cuál es la temperatura del silo 3?"
"Muestra el estado de la mezcladora 1"
"¿Cuánto cemento hay disponible?"
```

#### Consultas Moderadas (Cálculos)
```
"¿Cuántos pedidos pendientes tenemos hoy?"
"Calcula el inventario total de agregados"
"¿Cuál es el promedio de humedad de las tolvas?"
```

#### Consultas Complejas (Multinivel)
```
"¿Podemos producir 45 m³ de C25/30 mañana a las 7?"
"Verifica disponibilidad de planta 2, materiales y programación"
"Dame un resumen del estado general de producción"
```

## Arquitectura

### Arquitectura de 5 Capas

```
┌─────────────────────────────────────────┐
│  Capa 1: Interfaz Multimodal            │
│  - Reconocimiento de voz (Google API)   │
│  - Síntesis de voz (gTTS)               │
│  - Interfaz gráfica (Tkinter)           │
└─────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────┐
│  Capa 2: Procesamiento de Lenguaje      │
│  - Mistral-7B (llama.cpp)               │
│  - Interpretación semántica             │
└─────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────┐
│  Capa 3: Razonamiento y Planificación   │
│  - Extracción de parámetros             │
│  - Determinación de nivel industrial    │
│  - Gestión de contexto conversacional   │
└─────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────┐
│  Capa 4: Control y Ejecución            │
│  ├─ OPC UA → PLC/SCADA (Levels 2-3)     │
│  ├─ MQTT → Sensores (Level 1)           │
│  └─ REST API → MES/ERP (Levels 4-5)     │
└─────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────┐
│  Capa 5: Retroalimentación y            │
│           Persistencia                  │
│  - Registro de conversaciones (JSON)    │
│  - Monitoreo térmico                    │
│  - Trazabilidad de operaciones          │
└─────────────────────────────────────────┘
```

## Estructura del Proyecto

### Módulos Principales

| Archivo | Descripción | Responsabilidad |
|---------|-------------|-----------------|
| `main.py` | Punto de entrada | Orquestación general, inicialización |
| `chatGPT.py` | Gestión del LLM | Carga del modelo, inferencia, memoria conversacional |
| `reconocimiento.py` | Reconocimiento de voz | Captura de audio, transcripción, detección de activación |
| `sintesis.py` | Síntesis de voz | Generación de audio con gTTS/pygame |
| `localC.py` | Cliente OPC UA | Conexión PLC/SCADA, lectura de variables |
| `globalC.py` | Cliente MQTT | Suscripción a tópicos, recepción de sensores |
| `apiC.py` | Cliente REST | Consultas HTTP a MES/ERP |
| `EyS.py` | Coordinador de datos | Agregación multinivel, persistencia periódica |
| `IG.py` | Interfaz gráfica | Ventana de chat con Tkinter |
| `variablesG.py` | Variables globales | Estado compartido, eventos de sincronización |
| `json_Hilos.py` | Gestión de config | Lectura/escritura de config.json, estructura de archivos |

### Archivos de Datos

- `src/config.json`: Configuración principal del sistema
- `src/datos.txt`: Snapshot periódico de datos industriales (actualizado cada 5s)
- `src/conversacion.json`: Historial conversacional (últimos 10 intercambios)

## Troubleshooting

### Problema: "No se puede acceder al micrófono"

**Solución:**
```bash
# Listar micrófonos disponibles
python3 -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"

# Editar reconocimiento.py línea ~218 con el índice correcto
microphone = sr.Microphone(device_index=2)  # Cambiar el número
```

### Problema: "Temperatura alta / Thermal throttling"

**Solución:**
1. Verificar ventilación del sistema de refrigeración
2. Reducir `N_BATCH` en config.json (de 48 a 32)
3. Limitar `MAX_TOKENS` (de 200 a 150)
4. Asegurar temperatura ambiente < 25°C

```bash
# Monitorear temperatura en tiempo real
watch -n 1 'vcgencmd measure_temp'
```

### Problema: "Modelo demasiado lento"

**Solución:**
1. Verificar que OpenBLAS está activado:
```bash
python3 -c "from llama_cpp import llama_cpp; print(llama_cpp.llama_supports_mmap())"
```

2. Optimizar parámetros en `config.json`:
```json
{
  "N_THREADS": 4,      // Usar todos los núcleos
  "N_BATCH": 48,       // Aumentar si hay RAM disponible
  "N_CTX": 1024        // Reducir a 512 si es necesario
}
```

### Problema: "Error de conexión OPC UA/MQTT"

**Solución:**
1. Verificar conectividad de red:
```bash
ping 192.168.1.10  # IP del servidor OPC UA
```

2. Revisar configuración de firewall
3. Comprobar estado de los servidores industriales
4. Verificar credenciales y permisos

### Problema: "Memory Error al cargar el modelo"

**Solución:**
```bash
# Verificar RAM disponible
free -h

# Cerrar procesos innecesarios
sudo systemctl stop cups  # Ejemplo: servicio de impresión

# Aumentar swap (temporal)
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # Cambiar CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### Logs y Diagnóstico

```bash
# Ver logs del sistema
journalctl -u your-service-name -f

# Monitoreo de recursos
htop

# Verificar uso de GPU/CPU
vcgencmd get_throttled  # Raspberry Pi
```
## Publicación

Este repositorio implementa la investigación publicada en:

**Hidalgo-Castelo, F., Guerrero-González, A., García-Córdova, F., Lloret-Abrisqueta, F., & Torregrosa Bonet, C.** (2025). *Multimodal Cognitive Architecture with Local Generative AI for Industrial Control of Concrete Plants on Edge Devices*. **Sensors**, 25(x). https://doi.org/10.3390/xxxxx

Para más detalles técnicos, metodología experimental y resultados completos, consultar el paper.

## Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Agradecimientos

- **Frumecar S.L.** (Murcia, España) por facilitar las instalaciones de validación
- **Universidad Politécnica de Cartagena** por el apoyo institucional
- Comunidad de **llama.cpp** y **Hugging Face** por las herramientas de inferencia
- Desarrolladores de **Mistral AI** por el modelo base

---

<div align="center">


Desarrollado para la democratización del acceso cognitivo a información industrial

</div>
