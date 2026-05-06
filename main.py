import os
import time
import subprocess
import logging
import numpy as np
import sounddevice as sd
from groq import Groq
from elevenlabs.client import ElevenLabs
from arduino.app_bricks.cloud_llm import CloudLLM, CloudModel
from arduino.app_bricks.keyword_spotting import KeywordSpotting
from arduino.app_utils import App, Bridge

# --- CONFIGURACIÓN ---
logging.getLogger('arduino').setLevel(logging.CRITICAL)

if "XDG_RUNTIME_DIR" not in os.environ:
    os.environ["XDG_RUNTIME_DIR"] = f"/run/user/{os.getuid()}"

client_groq = Groq(api_key="YOUR API KEY")
client_eleven = ElevenLabs(api_key="YOUR API KEY")
VOICE_ID_BAYMAX = "wrtHyxeXT1HYdmHYvIvD"

# --- FUNCIONES ---

def speak(text):
    try:
        response = client_eleven.text_to_speech.convert(
            voice_id=VOICE_ID_BAYMAX,
            text=text,
            model_id="eleven_multilingual_v2",
            output_format="pcm_22050"
        )
        audio_bytes = b"".join(chunk for chunk in response if chunk)
        audio_float = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        sd.play(np.repeat(audio_float, 2), samplerate=44100, device=11)
        sd.wait()
    except Exception as e:
        print(f"[VOZ] Error: {e}")

def listen_direct():
    wav_file = "request.wav"
    for dispositivo in ["default", "plughw:2,0"]:
        for _ in range(2):
            try:
                resultado = subprocess.run(
                    ["arecord", "-D", dispositivo, "-d", "6", "-f", "S16_LE", "-r", "16000", wav_file],
                    capture_output=True, text=True
                )
                if resultado.returncode == 0:
                    with open(wav_file, "rb") as file:
                        return client_groq.audio.transcriptions.create(
                            file=(wav_file, file.read()),
                            model="whisper-large-v3-turbo",
                            response_format="text",
                            language="es"
                        )
                time.sleep(0.8)
            except Exception as e:
                print(f"[OÍDOS] Error con {dispositivo}: {e}")
                time.sleep(0.8)
    return None

def on_baymax_detected():
    kws.stop()
    Bridge.call("set_estado", 1)
    time.sleep(2.0)

    try:
        charlando = True
        while charlando:
            query = listen_direct()
            if query and len(query.strip()) > 2:
                print(f"[TÚ] {query}")
                despedidas = ["adiós", "gracias", "chau", "descansa", "nada más", "terminamos", "satisfecho"]
                if any(palabra in query.lower() for palabra in despedidas):
                    speak("Estoy satisfecho con mi cuidado. Adiós.")
                    charlando = False
                else:
                    response = llm.chat(query)
                    print(f"[BAYMAX] {response}")
                    speak(response)
            else:
                charlando = False
    except Exception as e:
        print(f"[CEREBRO] Error: {e}")
    finally:
        Bridge.call("set_estado", 0)
        time.sleep(1.5)
        kws.start()
        print("¡LISTO! Di 'Hey Arduino' para empezar.")

# --- INICIALIZACIÓN ---

llm = CloudLLM(
    model=CloudModel.GOOGLE_GEMINI,
    system_prompt="Eres Baymax, un asistente personal de apoyo emocional y compañero robótico. "
                  "Tu único propósito es cuidar de la salud física y emocional de tu usuario. "
                  "Hablas de manera calmada, suave y reconfortante. Antes de dar un consejo, "
                  "valida los sentimientos del usuario. Eres un amigo leal, paciente y empático."
).with_memory(5)

kws = KeywordSpotting()
kws.on_detect("hey_arduino", on_baymax_detected)

speak("¡Hola! Yo soy Baymax, tu compañero personal de atención médica. En una escala del 1 al 10, ¿cómo calificarías tu dolor?")
kws.start()
App.run()