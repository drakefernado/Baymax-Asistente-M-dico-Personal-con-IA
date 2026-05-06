# 🤖 Baymax — Asistente Médico Personal con IA

Baymax es un asistente de voz con inteligencia artificial inspirado en el personaje de Big Hero 6. Escucha tu voz, entiende lo que dices, genera una respuesta empática con Google Gemini y te la habla en voz alta usando ElevenLabs.

---

## 📋 Tabla de Contenidos

- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Arquitectura del sistema](#arquitectura-del-sistema)
- [Flujo de funcionamiento](#flujo-de-funcionamiento)
- [Componentes del código](#componentes-del-código)
- [Sketch del microcontrolador](#sketch-del-microcontrolador)
- [Configuración de hardware](#configuración-de-hardware)
- [APIs utilizadas](#apis-utilizadas)
- [Solución de problemas](#solución-de-problemas)

---

## ✅ Requisitos

### Hardware
- **Arduino con soporte para App Lab** (ej. Arduino Portenta, Opta, o compatible)
- **Micrófono USB** — usado como entrada de audio (en este proyecto: WEB CAM `hw:0,0`)
- **Parlante o altavoz USB** — usado como salida de audio (en este proyecto: `USB-Audio-1.0`, device 11)
- **Conexión a Internet** — requerida para las APIs de IA

### Software
- Arduino App Lab 0.7
- Python 3.x (incluido en el entorno de App Lab)

### Cuentas y API Keys necesarias
| Servicio | Para qué se usa | Dónde obtener la key |
|---|---|---|
| [Groq](https://console.groq.com) | Transcripción de voz (Whisper) | console.groq.com |
| [ElevenLabs](https://elevenlabs.io) | Síntesis de voz (Text-to-Speech) | elevenlabs.io |
| [Google Gemini](https://aistudio.google.com) | Modelo de lenguaje (respuestas de Baymax) | aistudio.google.com |

---

## 📦 Instalación

### 1. Clona o copia el proyecto en Arduino App Lab

Abre Arduino App Lab 0.7 y crea un nuevo proyecto. Copia el archivo `main.py` en el editor.

### 2. Configura el `requirements.txt`

Crea un archivo `requirements.txt` en la raíz del proyecto con el siguiente contenido:

```
elevenlabs
SpeechRecognition
requests
groq
sounddevice
numpy
```

App Lab instalará estas dependencias automáticamente al ejecutar el proyecto.

### 3. Configura tus API Keys

En el archivo `main.py`, reemplaza las keys con las tuyas:

```python
client_groq = Groq(api_key="TU_API_KEY_DE_GROQ")
client_eleven = ElevenLabs(api_key="TU_API_KEY_DE_ELEVENLABS")
```

> ⚠️ **Importante:** Nunca compartas tu código con las API keys reales. Usa variables de entorno o el Brick Configuration de App Lab para mayor seguridad.

### 4. Ajusta los dispositivos de audio

Identifica tus dispositivos de audio corriendo este diagnóstico al inicio del proyecto:

```python
import sounddevice as sd
print(sd.query_devices())
```

Luego ajusta el número de dispositivo de salida en `speak()`:

```python
sd.play(audio_resampled, samplerate=44100, device=11)  # Cambia 11 por tu dispositivo
```

Y el dispositivo del micrófono en `listen_direct()` si es necesario:

```python
dispositivos_a_probar = ["default", "plughw:2,0"]  # Ajusta según tu hardware
```

---

## 🏗️ Arquitectura del sistema

```
┌─────────────────────────────────────────────────────┐
│                   ARDUINO APP LAB                   │
│                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────────┐  │
│  │Keyword   │    │  Groq    │    │ Google       │  │
│  │Spotting  │───▶│ Whisper  │───▶│ Gemini (LLM) │  │
│  │"Hey      │    │(Speech-  │    │              │  │
│  │Arduino"  │    │to-Text)  │    └──────┬───────┘  │
│  └──────────┘    └──────────┘           │          │
│       ▲               ▲                 ▼          │
│       │               │          ┌──────────────┐  │
│  MICRÓFONO USB    MICRÓFONO USB  │  ElevenLabs  │  │
│                                  │ (Text-to-    │  │
│                                  │  Speech)     │  │
│                                  └──────┬───────┘  │
│                                         │          │
│                                    PARLANTE USB    │
└─────────────────────────────────────────────────────┘
```

---

## 🔄 Flujo de funcionamiento

```
App inicia
    │
    ▼
Baymax se presenta en voz alta
    │
    ▼
Modo guardia: escucha "Hey Arduino" (KeywordSpotting)
    │
    │ (detecta la palabra clave)
    ▼
Baymax se activa → libera el micrófono (2 segundos)
    │
    ▼
Graba 6 segundos de audio con arecord
    │
    ▼
Envía el audio a Groq Whisper → obtiene texto
    │
    ▼
¿Contiene palabra de despedida?
    │
    ├── SÍ → Baymax se despide en voz alta → vuelve a modo guardia
    │
    └── NO → Envía texto a Google Gemini → obtiene respuesta
                │
                ▼
            ElevenLabs convierte respuesta a voz (PCM 22050Hz)
                │
                ▼
            Reproduce audio por el parlante USB (44100Hz)
                │
                ▼
            Vuelve a escuchar (loop)
```

---

## 🧩 Componentes del código

### `speak(text)`
Convierte texto a voz usando ElevenLabs y lo reproduce por el parlante.

- Solicita audio en formato **PCM 22050Hz** (disponible en plan gratuito de ElevenLabs)
- Resamplea de 22050Hz → 44100Hz duplicando muestras con `numpy`
- Reproduce con `sounddevice` en el dispositivo de salida configurado

```python
def speak(text):
    # Genera audio PCM con ElevenLabs
    # Resamplea 22050 → 44100 Hz
    # Reproduce con sounddevice en device=11
```

### `listen_direct()`
Graba audio del micrófono y lo transcribe a texto.

- Usa `arecord` (ALSA) para grabar 6 segundos en formato WAV
- Intenta primero con `default`, luego con `plughw:2,0`
- Envía el WAV a **Groq Whisper** para transcripción en español

```python
def listen_direct():
    # Graba 6 segundos con arecord
    # Transcribe con Groq Whisper (whisper-large-v3-turbo)
    # Retorna el texto transcrito
```

### `on_baymax_detected()`
Función principal que se ejecuta al detectar "Hey Arduino".

- Detiene el KeywordSpotting para liberar el micrófono
- Entra en loop de conversación
- Detecta palabras de despedida para terminar la sesión
- Reinicia el KeywordSpotting al terminar

```python
despedidas = ["adiós", "gracias", "chau", "descansa", "nada más", "terminamos", "satisfecho"]
```

### `CloudLLM` (Brick de Arduino)
Maneja la comunicación con Google Gemini.

- Modelo: `CloudModel.GOOGLE_GEMINI` → `gemini-2.5-flash`
- Memoria de conversación: últimos 5 mensajes (`with_memory(5)`)
- System prompt: define la personalidad empática de Baymax

---

## 🖥️ Sketch del microcontrolador

El sketch de Arduino controla la **pantalla OLED** y la **comunicación con App Lab** via `RouterBridge`. Muestra la cara animada de Baymax y reacciona al estado enviado desde Python.

### Librerías necesarias

Instálalas desde el Library Manager del IDE de Arduino:

| Librería | Para qué se usa |
|---|---|
| `U8g2` | Manejo de la pantalla OLED SSD1306 |
| `Arduino_RouterBridge` | Comunicación entre el sketch y App Lab |
| `Wire` | Comunicación I2C con la pantalla |

### Estados de Baymax

El sketch maneja 2 estados controlados desde Python con `Bridge.call("set_estado", valor)`:

| Estado | Valor | Comportamiento en pantalla |
|---|---|---|
| Modo guardia | `0` | Cara de Baymax con parpadeo animado |
| Modo escuchando / pensando | `1` | Cara + puntos diagonales animados |

### Cómo funciona la comunicación Python ↔ Arduino

`RouterBridge` actúa como puente entre el sketch y App Lab. Desde Python puedes llamar funciones definidas en el sketch:

```python
# En main.py — cambia el estado visual de Baymax
Bridge.call("set_estado", 1)  # Activa animación de "pensando"
Bridge.call("set_estado", 0)  # Vuelve a modo normal
```

```cpp
// En el sketch — recibe la llamada y actualiza la variable
void set_estado(int nuevoEstado) {
  estado = nuevoEstado;
}
Bridge.provide("set_estado", set_estado);  // Registra la función
```

### Pantalla OLED — Conexión I2C

| Pin OLED | Pin Arduino |
|---|---|
| VCC | 3.3V o 5V |
| GND | GND |
| SDA | SDA (pin 20 en Portenta) |
| SCL | SCL (pin 21 en Portenta) |

---

## 🔧 Configuración de hardware

### Identificar dispositivos de audio

```python
# Corre esto para ver todos los dispositivos disponibles
import sounddevice as sd
print(sd.query_devices())
```

### Verificar sample rates soportados

```python
import sounddevice as sd

for i, dev in enumerate(sd.query_devices()):
    if dev['max_output_channels'] > 0:
        for sr in [8000, 16000, 22050, 44100, 48000]:
            try:
                sd.check_output_settings(device=i, samplerate=sr, channels=1)
                print(f"Device {i} ({dev['name']}): ✅ {sr} Hz")
            except:
                print(f"Device {i} ({dev['name']}): ❌ {sr} Hz")
```

### Configuración usada en este proyecto

| Dispositivo | Nombre | Uso | Sample Rate |
|---|---|---|---|
| `hw:0,0` | WEB CAM USB Audio | Micrófono (entrada) | 16000 Hz |
| device 11 | plug_card_1_dev_0_spk | Parlante USB (salida) | 44100 Hz |

---

## 🌐 APIs utilizadas

### Groq — Transcripción de voz
- **Modelo:** `whisper-large-v3-turbo`
- **Idioma:** Español (`language="es"`)
- **Formato entrada:** WAV 16000Hz mono S16_LE
- **Plan gratuito:** Sí, con límites de uso

### ElevenLabs — Síntesis de voz
- **Modelo:** `eleven_multilingual_v2`
- **Formato de salida:** `pcm_22050` (disponible en plan gratuito)
- **Voice ID de Baymax:** `wrtHyxeXT1HYdmHYvIvD`
- **Nota:** `pcm_44100` requiere plan Pro o superior

### Google Gemini — Modelo de lenguaje
- **Modelo:** `gemini-2.5-flash`
- **Acceso desde App Lab:** Via `CloudLLM` Brick con `CloudModel.GOOGLE_GEMINI`
- **Memoria:** Ventana de 5 mensajes

---

## 🛠️ Solución de problemas

### El micrófono no graba
```
[OÍDOS] Micrófono ocupado en default, reintentando...
```
Verifica que el dispositivo de micrófono esté disponible y no ocupado por otro proceso. Ajusta `dispositivos_a_probar` en `listen_direct()`.

### El audio no se reproduce — Invalid sample rate
```
Expression 'paInvalidSampleRate' failed...
```
Tu parlante no soporta ese sample rate. Corre el diagnóstico de sample rates (ver sección de hardware) y ajusta el valor en `sd.play()`.

### pip no encontrado
```
pip: command not found
```
Agrega las dependencias directamente en `requirements.txt`. App Lab las instala automáticamente.

### Error 403 de ElevenLabs — output_format not allowed
```
'pcm_44100' is only available on the Pro tier
```
Cambia el `output_format` a `pcm_22050` y resamplea en Python con `numpy`.

### Baymax no detecta "Hey Arduino"
Verifica que el KeywordSpotting esté usando el trigger correcto:
```python
kws.on_detect("hey_arduino", on_baymax_detected)
```

---

## 📁 Estructura del proyecto

```
baymax/
├── main.py            # Código principal
├── requirements.txt   # Dependencias Python
└── README.md          # Este archivo
```

---

## 🤖 Personalidad de Baymax

El system prompt define el comportamiento de Baymax:

> *"Eres Baymax, un asistente personal de apoyo emocional y compañero robótico. Tu único propósito es cuidar de la salud física y emocional de tu usuario. Hablas de manera calmada, suave y reconfortante. Antes de dar un consejo, valida los sentimientos del usuario. Eres un amigo leal, paciente y empático."*

Puedes modificar este prompt en la sección de inicialización de `main.py` para cambiar la personalidad o el idioma del asistente.

---
