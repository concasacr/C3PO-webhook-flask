import openai
import os

openai.api_key = os.environ.get('OPENAI_API_KEY')

if not openai.api_key:
    raise ValueError("Debe establecer la llave de API de OpenAI (OPENAI_API_KEY) en el entorno")

def obtener_completacion(pregunta, modelo="gpt-3.5-turbo"):
    # Obtener una completación de chat para una pregunta dada
    mensajes = [{"role": "user", "content": pregunta}]
    respuesta = openai.ChatCompletion.create(
        model=modelo,
        messages=mensajes,
        temperature=0,
    )
    return respuesta.choices[0].message["content"]

def obtener_completacion_desde_mensajes(mensajes, modelo="gpt-3.5-turbo", temperatura=0):
    # Obtener una completación de chat utilizando una lista de mensajes
    respuesta = openai.ChatCompletion.create(
        model=modelo,
        messages=mensajes,
        temperature=temperatura,
    )
    return respuesta.choices[0].message["content"]