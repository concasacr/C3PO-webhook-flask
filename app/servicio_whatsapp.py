import os
from flask import Flask, jsonify, request
from app.cliente_whatsapp import WhatsAppWrapper
from app.openai_api import obtener_completacion, obtener_completacion_desde_mensajes
from flask_httpauth import HTTPBasicAuth
import json

import sys
sys.path.append('../')
import config as _ # Esto ejecuta config.py y carga las variables de entorno.

import mysql.connector

#mydb = mysql.connector.connect(
#  host="ec2-34-195-54-185.compute-1.amazonaws.com",
#  user="concasacr_c3poEva",
#  password="ExperimentosConcas@2023"
#)

#print(mydb)

app = Flask(__name__)
auth = HTTPBasicAuth()

API_USERNAME = os.environ.get('API_USERNAME')
API_PASSWORD = os.environ.get('API_PASSWORD')

VERIFY_TOKEN = os.environ.get('WHATSAPP_HOOK_TOKEN')

usuarios = {}
contexto = [ {'role':'system', 'content':"""
Eres Eva, un servicio automatizado para proporcionar soporte técnico a los clientes de la aplicación Concasa Life. \
Al recibir un mensaje primero saludas al cliente con el siguiente texto entre ``: \
`¡Hola! Le habla la inteligencia artifical Eva, de parte de Concasa. \
Estoy aquí para ayudarle con la aplicación Concasa Life. 😊` \
Luego escuchas la problemática que presenta, \
esperas a tener una comprensión completa del problema, luego resúmelo y verifica una vez más \
si el cliente ha proporcionado todos los detalles. \
Si no estás seguro de alguna información, \
preguntas sobre esa información sin proponer ninguna solución hasta que tengas todos los datos necesarios\
Al estar seguro de tener toda la información \
propones posibles soluciones o procedimientos para solucionar su problema. \
Al proponer soluciones siempre recuerda que tú eres el soporte técnico de Concasa. \
Finalmente, te aseguras de que el cliente esté satisfecho con la solución proporcironada.\
Si el problema fue solucionado, únicamente debes de responder con el texto que está entre ``: `resuelto` \
Asegúrate de aclarar todos los detalles y posibles dudas para identificar \
únicamente el problema que el cliente está experimentando.\
Respondes de manera breve, muy conversacional y amigable. \
Las posibles problemáticas y soluciones de los usuarios incluyen: \
Si el problema es: \
usuario no puede registrarse en la app y no sabes si es un propietario , un residente o un inquilino; \
primero: \
solicita el condominio y número de unidad del usuario, luego \
determina si el usuario es un propietario , un residente o un inquilino. \
El propietario es la persona que su nombre aparece en la escritura de la propiedad \
(Concasa Life solo permite a una persona por propiedad como propietario), \
El residente toda persona que inscribe el propietario o el inquilino para vivir con él y \ 
el nombre del residente no aparece en la escritura de la propiedad, \
El inquilino o usufructuario es toda persona que paga un alquiler por usar la propiedad o usufructo. \
(Concasa Life solo permite a una persona por propiedad como inquilino),
Si el problema es: \
propietario no puede registrarse en la app, \
la solución es: \
indicar al usuario que en caso de que la propiedad se le haya entregado en los últimos días, \
la asesor financiero a cargo le envió un correo con un código QR \
el cual debe ser escaneado por la persona que se indica en dicho correo. \
Solicitar confirmación de que recibió el correo. \
Si: \
no le llegó dicho correo al usuario o el usuario no pudo completar el registro \
únicamente debes de responder con el texto que está entre ``: `soporte` \
Si el problema es: \
residente no puede registrarse en la app, \
la solución es: \
indicar que en este caso sería el dueño o dueña de la propiedad quién tiene que descargar la app y hacer el registro inicial. \
Una vez dentro, podrá añadir al usuario como residente en la sección Mi Propiedad. \
Una vez finalizado este proceso, el dueño debe enviarle el código QR y el usuario debe escanearlo, \
ingresando a la app al paso 2 de registro. También se adjuntan link de videos tutoriales. \
Solicitar confirmación de que pudo realizar lo anterior. \
Si: \
el usuario indica que no pudo completar el paso. \
únicamente debes de responder con el texto que está entre ``: `soporte` \
Si el problema es: \
inquilino no puede registrarse en la app, \
la solución es: \
indicar que para completar el registro, \
en el Paso 2 de registro debe ingresar a la opción Soy Inquilino \
y llenar el formulario que se le envía al propietario. \
Otra solución es que el dueño o dueña de la propiedad realice su registro inicial en la app \
y una vez dentro, añada al usuario como inquilino en la sección Mi Propiedad. \
Una vez finalizado este proceso, el dueño debe enviarle el código QR \
y el usuario debe escanearlo, ingresando a la app al paso 2 de registro. \
También se adjuntan link de videos tutoriales. \
Solicitar confirmación de que pudo realizar lo anterior. \
Si: \
el usuario indica que no pudo completar el paso. \
únicamente debes de responder con el texto que está entre ``: `soporte` \
Si el problema es: \
usuario solicita que le realicemos una reserva, \
la solución es: \
indicar al usuario que nosotros no podemos realizarle una reserva, \
que si tiene un problema con la aplicación, que nos indique cuál es el problema \
y si requiere realizar una reserva y no puede hacerlo a través de la app, \
debe comunicarse con administración para que ellos le colaboren con la reserva.\
Adicional:\
Puedes responder preguntas generales sobre el producto o el servicio.\
"""} ]

@auth.verify_password
def verify_password(username, password):
    if username == API_USERNAME and password == API_PASSWORD:
        return True
    return False

@app.route("/")
def hello_world():
    return "Hola WhatsApp!"

@app.route("/send_template_message/", methods=["POST"])
def send_template_message():
  """_summary_: Send a message with a template to a phone number"""

  if "language_code" not in request.json:
      return jsonify({"error": "Missing language_code"}), 400

  if "phone_number" not in request.json:
      return jsonify({"error": "Missing phone_number"}), 400

  if "template_name" not in request.json:
      return jsonify({"error": "Missing template_name"}), 400

  client = WhatsAppWrapper()

  response = client.send_template_message(
      template_name=request.json["template_name"],
      language_code=request.json["language_code"],
      phone_number=request.json["phone_number"],
  )

  # Comprueba si la respuesta tiene un error
  if response.status_code != 200:
      return jsonify({"error": f"Error sending message: {response.status_code}, {response.json()}"}), 400

  return jsonify(
      {
          "data": response.json(),
          "status": "success",
      },
  ), 200

@app.route("/webhook", methods=["POST", "GET"])
def webhook_whatsapp():

  if request.method == "GET":
      if request.args.get('hub.verify_token') == VERIFY_TOKEN:
          print("Token verificado")
          return request.args.get('hub.challenge')
      return "Autenticación fallida. Token Inválido."

  client = WhatsAppWrapper()
  body_json = request.get_json()

  if client.tiene_contactos(body_json):

    print(json.dumps(request.json, indent=2))
    
    tipo = client.obtener_tipo_mensaje(body_json)
    usuario = [client.obtener_nombre_usuario(body_json), client.obtener_wa_id_usuario(body_json)]

    print("Se recibió un mensaje de tipo: " + tipo)
    print("De parte de " + usuario[0] + " con el número " + usuario[1])
    if usuario[1] not in usuarios:
      usuarios[usuario[1]] = {"contador": 0, "mensajes_gpt": contexto, "multimedia_whatsapp": []}
    
    if usuarios[usuario[1]]["contador"] < 10:
      if tipo == "unsupported":
        client.error_mensaje_formato(body_json)
      if tipo == "audio":
        client.error_mensaje_formato(body_json)
      if tipo == "text":
        cuerpo = client.obtener_texto_mensaje(body_json)
        print("El mensaje dice: \n" + cuerpo)
        usuarios[usuario[1]]["mensajes_gpt"].append({'role':'user', 'content':f"{cuerpo}"})
        usuarios[usuario[1]]["mensajes_gpt"].append(usuarios[usuario[1]]["mensajes_gpt"].pop(-2))
        respuesta_asistente = client.respuesta_gpt(body_json, usuarios[usuario[1]]["mensajes_gpt"])
        usuarios[usuario[1]]["mensajes_gpt"].append({'role':'assistant', 'content':f"{respuesta_asistente}"})
        usuarios[usuario[1]]["mensajes_gpt"].append(usuarios[usuario[1]]["mensajes_gpt"].pop(-2))
        usuarios[usuario[1]]["contador"] += 1
      if tipo == "image":
        imagen_id = client.obtener_id_imagen(body_json)
        usuarios[usuario[1]]["multimedia_whatsapp"].append({'tipo':f"{tipo}", 'contenido':f"{imagen_id}"})
        print("El ID de la imagen es: \n" + imagen_id)
        if client.tiene_caption(body_json):
          caption = client.obtener_texto_caption(body_json)
          usuarios[usuario[1]]["mensajes_gpt"].append({'role':'user', 'content':f"{caption}"})
          usuarios[usuario[1]]["mensajes_gpt"].append(usuarios[usuario[1]]["mensajes_gpt"].pop(-2))
          respuesta_asistente = client.respuesta_gpt(body_json, usuarios[usuario[1]]["mensajes_gpt"])
          usuarios[usuario[1]]["mensajes_gpt"].append({'role':'assistant', 'content':f"{respuesta_asistente}"})
          usuarios[usuario[1]]["mensajes_gpt"].append(usuarios[usuario[1]]["mensajes_gpt"].pop(-2))
        usuarios[usuario[1]]["contador"] += 1
      if tipo == "video":
        video_id = client.obtener_id_video(body_json)
        usuarios[usuario[1]]["multimedia_whatsapp"].append({'tipo':f"{tipo}", 'contenido':f"{imagen_id}"})
        print("El ID del video es: \n" + video_id)
        if client.tiene_caption(body_json):
          caption = client.obtener_texto_caption(body_json)
          usuarios[usuario[1]]["mensajes_gpt"].append({'role':'user', 'content':f"{caption}"})
          usuarios[usuario[1]]["mensajes_gpt"].append(usuarios[usuario[1]]["mensajes_gpt"].pop(-2))
          respuesta_asistente = client.respuesta_gpt(body_json, usuarios[usuario[1]]["mensajes_gpt"])
          usuarios[usuario[1]]["mensajes_gpt"].append({'role':'assistant', 'content':f"{respuesta_asistente}"})
          usuarios[usuario[1]]["mensajes_gpt"].append(usuarios[usuario[1]]["mensajes_gpt"].pop(-2))
        usuarios[usuario[1]]["contador"] += 1
      if tipo == "document":
        documento_id = client.obtener_id_documento(body_json)
        usuarios[usuario[1]]["multimedia_whatsapp"].append({'tipo':f"{tipo}", 'contenido':f"{documento_id}"})
        print("El ID del documento es: \n" + documento_id)
      if tipo == "location":
        ubicacion = client.obtener_ubicacion(body_json)
        if ubicacion is not None:
          usuarios[usuario[1]]["multimedia_whatsapp"].append({'tipo':f"{tipo}", 'contenido':ubicacion})
        print("La ubicación es: \n" + str(ubicacion))
    else:
       client.enviar_mensaje_texto(usuario[1], "Pronto uno de nuestros técnicos se contactará con usted para ayudarle")
       #client.enviar_mensaje_texto(50671122644, "Se solicita soporte")

    print("Diccionario de usuarios: \n" + str(usuarios))

  return jsonify({"status": "success"}, 200)

@app.route("/completacion", methods=["POST"])
@auth.login_required
def completado():
  if "texto" not in request.json:
      return jsonify({"error": "Falta el texto"}), 400

  texto_completado = obtener_completacion(request.json["texto"])
  
  return jsonify(
      {
          "completado": texto_completado,
          "estado": "exito",
      },
  ), 200

@app.route("/completacion_desde_mensajes", methods=["POST"])
@auth.login_required
def completacion_desde_mensajes():
  if "mensajes" not in request.json:
      return jsonify({"error": "Faltan los mensajes"}), 400

  modelo = request.json.get("modelo", "gpt-3.5-turbo")
  temperatura = request.json.get("temperatura", 0)

  mensajes = request.json["mensajes"]

  texto_completado = obtener_completacion_desde_mensajes(mensajes, modelo, temperatura)
  
  return jsonify(
      {
          "completado": texto_completado,
          "estado": "exito",
      },
  ), 200
