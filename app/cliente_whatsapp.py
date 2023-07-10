import os
import requests
import json

from app.openai_api import obtener_completacion_desde_mensajes

import sys

sys.path.append('../')
import config as _  # Esto ejecuta config.py y carga las variables de entorno.


class WhatsAppWrapper:

  API_URL = "https://graph.facebook.com/v13.0/"
  API_TOKEN = os.environ.get("WHATSAPP_API_TOKEN")
  NUMBER_ID = os.environ.get("WHATSAPP_NUMBER_ID") #Phone number ID

  def __init__(self):
    self.headers = {
      "Authorization": f"Bearer {self.API_TOKEN}",
      "Content-Type": "application/json",
    }
    self.API_URL = self.API_URL + self.NUMBER_ID

  def preparar_payload(self, recipient_wa_id, message_type, content, caption=None):
    # Prepara el payload con los datos necesarios para enviar un mensaje de WhatsApp
    payload = {
      "messaging_product": "whatsapp",
      "to": recipient_wa_id,
      "type": message_type
    }

    if message_type == "text":
      payload["text"] = {
        "body": content
      }
    elif message_type == "location":
      payload["location"] = {
        "latitude": content["latitude"],
        "longitude": content["longitude"]
      }
    else:
      payload[message_type] = {
        "id": content
      }

      if caption:
        payload[message_type]["caption"] = caption

    return payload

  def send_template_message(self, template_name, language_code, phone_number):
    #Enviar mensaje plantilla
    payload = json.dumps({
      "messaging_product": "whatsapp",
      "to": phone_number,
      "type": "template",
      "template": {
        "name": template_name,
        "language": {
          "code": language_code
        }
      }
    })

    response = requests.request("POST", f"{self.API_URL}/messages", headers=self.headers, data=payload)

    if response.status_code != 200:
      print(f"Error sending message: {response.status_code}, {response.text}")
      return {
        "error":
        f"Error sending message: {response.status_code}, {response.text}"
      }
    else:
      return response

  def obtener_tipo_mensaje(self, data):
    #Devuelve el tipo del mensaje
    respuesta = "N/A"

    for entry in data["entry"]:
      for change in entry["changes"]:
        for message in change["value"]["messages"]:
          respuesta = message["type"]
    return respuesta

  def obtener_texto_mensaje(self, data):
    #Devuelve el texto del mensaje
    respuesta = "N/A"

    for entry in data["entry"]:
      for change in entry["changes"]:
        for message in change["value"]["messages"]:
          respuesta = message["text"]["body"]
    return respuesta

  def obtener_id_imagen(self, data):
    # Implementa la lógica para obtener el ID de la imagen
    if "entry" in data and len(data["entry"]) > 0:
        entry = data["entry"][0]
        if "changes" in entry and len(entry["changes"]) > 0:
            changes = entry["changes"][0]
            if "value" in changes and "messages" in changes["value"] and len(changes["value"]["messages"]) > 0:
                message = changes["value"]["messages"][0]
                if "image" in message and "id" in message["image"]:
                    return message["image"]["id"]
    return None
  
  def obtener_id_video(self, data):
    # Implementa la lógica para obtener el ID del video
    if "entry" in data and len(data["entry"]) > 0:
      entry = data["entry"][0]
      if "changes" in entry and len(entry["changes"]) > 0:
        changes = entry["changes"][0]
        if "value" in changes and "messages" in changes["value"] and len(changes["value"]["messages"]) > 0:
          message = changes["value"]["messages"][0]
          if "video" in message and "id" in message["video"]:
            return message["video"]["id"]
    return None

  def obtener_id_documento(self, data):
    # Implementa la lógica para obtener el ID del documento
    if "entry" in data and len(data["entry"]) > 0:
        entry = data["entry"][0]
        if "changes" in entry and len(entry["changes"]) > 0:
            changes = entry["changes"][0]
            if "value" in changes and "messages" in changes["value"] and len(changes["value"]["messages"]) > 0:
                message = changes["value"]["messages"][0]
                if "document" in message and "id" in message["document"]:
                    return message["document"]["id"]
    return None

  def obtener_ubicacion(self, data):
    # Implementa la lógica para obtener la ubicación
    if "entry" in data and len(data["entry"]) > 0:
        entry = data["entry"][0]
        if "changes" in entry and len(entry["changes"]) > 0:
            changes = entry["changes"][0]
            if "value" in changes and "messages" in changes["value"] and len(changes["value"]["messages"]) > 0:
                message = changes["value"]["messages"][0]
                if "location" in message and "latitude" in message["location"] and "longitude" in message["location"]:
                    return message["location"]
    return None
  
  def obtener_wa_id_usuario(self, data):
    #Obtener el wa_id del usuario
    respuesta = "N/A"
    for entry in data["entry"]:
        for change in entry["changes"]:
            for contact in change["value"]["contacts"]:
                respuesta = contact["wa_id"]
    return respuesta

  def obtener_nombre_usuario(self, data):
    #Obtener el nombre del usuario
    respuesta = "N/A"
    for entry in data["entry"]:
        for change in entry["changes"]:
            for contact in change["value"]["contacts"]:
                respuesta = contact["profile"]["name"]
    return respuesta

  def obtener_datos_usuario(self, data):
    #Obtener el datos del usuario
    respuesta = []
    for entry in data["entry"]:
        for change in entry["changes"]:
            for contact in change["value"]["contacts"]:
                respuesta.append(contact["wa_id"])
                respuesta.append(contact["profile"]["name"])
    return respuesta

  def obtener_texto_caption(self, data):
    # Busca el texto en el atributo "caption" de imágenes o videos
    for entry in data["entry"]:
      for change in entry["changes"]:
        messages = change["value"]["messages"]
        for message in messages:
          if "image" in message and "caption" in message["image"]:
            return message["image"]["caption"]
          if "video" in message and "caption" in message["video"]:
            return message["video"]["caption"]
    return None

  def tiene_contactos(self, data):
    #Verifica si el JSON tiene la sección de contactos
    for entry in data["entry"]:
        for change in entry["changes"]:
            return "contacts" in change["value"]

  def tiene_caption(self, data):
    # Verifica si el JSON tiene el atributo "caption" en la sección de imágenes o videos
    for entry in data["entry"]:
      for change in entry["changes"]:
        if "messages" in change["value"]:
          messages = change["value"]["messages"]
          for message in messages:
            if "image" in message:
              return "caption" in message["image"]
            if "video" in message:
              return "caption" in message["video"]
  
  def error_mensaje_formato(self, data):
    #Le devuelve al remitente un mensaje indicando que no maneja ese formato
    
      # Obtener el wa_id del remitente
      remitente_wa_id = self.obtener_wa_id_usuario(data)

      # Preparar el payload
      payload = json.dumps(self.preparar_payload(
        remitente_wa_id, 
        "text", 
        "Lo siento, no puedo procesar ese tipo de información. Por favor, escriba su consulta."))

      # Enviar el mensaje de respuesta
      response = requests.request("POST", f"{self.API_URL}/messages", headers=self.headers, data=payload)

      if response.status_code != 200:
          print(f"Error sending message: {response.status_code}, {response.text}")

  def mensaje_eco(self, data):
  #Le devuelve al remitente el mismo mensaje que envió
    tipo_mensaje = self.obtener_tipo_mensaje(data)
    remitente_wa_id = self.obtener_wa_id_usuario(data)
    
    if tipo_mensaje == "text":
      message_text = self.obtener_texto_mensaje(data)
      payload = self.preparar_payload(remitente_wa_id, "text", message_text)
    elif tipo_mensaje == "image":
      imagen_id = self.obtener_id_imagen(data)
      if imagen_id is not None:
        if self.tiene_caption(data):
          payload = self.preparar_payload(remitente_wa_id, "image", imagen_id, self.obtener_texto_caption(data))
        else:
          payload = self.preparar_payload(remitente_wa_id, "image", imagen_id)
    elif tipo_mensaje == "video":
      video_id = self.obtener_id_video(data)
      if video_id is not None:
        if self.tiene_caption(data):
          payload = self.preparar_payload(remitente_wa_id, "video", video_id, self.obtener_texto_caption(data))
        else:
          payload = self.preparar_payload(remitente_wa_id, "video", video_id)
    elif tipo_mensaje == "document":
      documento_id = self.obtener_id_documento(data)
      if documento_id is not None:
        payload = self.preparar_payload(remitente_wa_id, "document", documento_id)
    elif tipo_mensaje == "location":
      ubicacion = self.obtener_ubicacion(data)
      if ubicacion is not None:
        payload = self.preparar_payload(remitente_wa_id, "location", ubicacion)
    payload = json.dumps(payload)
    
    # Enviar el mensaje devuelta al remitente
    response = requests.request("POST", f"{self.API_URL}/messages", headers=self.headers, data=payload)

    if response.status_code != 200:
        print(f"Error sending message: {response.status_code}, {response.text}")

  def respuesta_gpt(self, data, mensajes_gpt):
  #Le devuelve al remitente una respuesta de GPT en base al texto enviado
    tipo_mensaje = self.obtener_tipo_mensaje(data)
    remitente_wa_id = self.obtener_wa_id_usuario(data)
    respuesta_asistente = None
    
    if tipo_mensaje == "text":
      respuesta_asistente = obtener_completacion_desde_mensajes(mensajes_gpt)
      payload = self.preparar_payload(remitente_wa_id, "text", respuesta_asistente)
    elif tipo_mensaje == "image":
      imagen_id = self.obtener_id_imagen(data)
      if imagen_id is not None:
        if self.tiene_caption(data):
          respuesta_asistente = obtener_completacion_desde_mensajes(mensajes_gpt)
          payload = self.preparar_payload(remitente_wa_id, "text", respuesta_asistente)
    elif tipo_mensaje == "video":
      video_id = self.obtener_id_video(data)
      if video_id is not None:
        if self.tiene_caption(data):
          respuesta_asistente = obtener_completacion_desde_mensajes(mensajes_gpt)
          payload = self.preparar_payload(remitente_wa_id, "text", respuesta_asistente)
    payload = json.dumps(payload)
    
    # Enviar el mensaje al remitente
    response = requests.request("POST", f"{self.API_URL}/messages", headers=self.headers, data=payload)

    if response.status_code != 200:
        print(f"Error sending message: {response.status_code}, {response.text}")

    return respuesta_asistente

  def reenviar_mensaje(self, data, wa_id_destino):
    #Enviar un mensaje recibido a otra persona ajena
    tipo_mensaje = self.obtener_tipo_mensaje(data)
    if tipo_mensaje == "text":
        message_text = self.obtener_texto_mensaje(data)
        payload = self.preparar_payload(wa_id_destino, "text", message_text)
    elif tipo_mensaje == "image":
        imagen_id = self.obtener_id_imagen(data)
        if imagen_id is not None:
            payload = self.preparar_payload(wa_id_destino, "image", imagen_id)
    elif tipo_mensaje == "video":
        video_id = self.obtener_id_video(data)
        if video_id is not None:
            payload = self.preparar_payload(wa_id_destino, "video", video_id)
    elif tipo_mensaje == "document":
      documento_id = self.obtener_id_documento(data)
      if documento_id is not None:
        payload = self.preparar_payload(wa_id_destino, "document", documento_id)
    elif tipo_mensaje == "location":
      ubicacion = self.obtener_ubicacion(data)
      if ubicacion is not None:
        payload = self.preparar_payload(wa_id_destino, "location", ubicacion)
    payload = json.dumps(payload)
    # Enviar el mensaje al destinatario
    response = requests.request("POST", f"{self.API_URL}/messages", headers=self.headers, data=payload)

    if response.status_code != 200:
        print(f"Error sending message: {response.status_code}, {response.text}")

  def enviar_mensaje_texto(self, wa_id_destino, message_text):
    # Preparar el payload con el mensaje de texto
    payload = self.preparar_payload(wa_id_destino, "text", message_text)
    payload = json.dumps(payload)

    # Enviar el mensaje al destinatario
    response = requests.request("POST", f"{self.API_URL}/messages", headers=self.headers, data=payload)
    
    if response.status_code != 200:
      print(f"Error sending message: {response.status_code}, {response.text}")

  def enviar_mensaje_texto_a_lista(self, lista_wa_id_destino, message_text):
    for wa_id_destino in lista_wa_id_destino:
      # Preparar el payload con el mensaje de texto
      payload = self.preparar_payload(wa_id_destino, "text", message_text)
      payload = json.dumps(payload)

      # Enviar el mensaje al destinatario
      response = requests.request("POST", f"{self.API_URL}/messages", headers=self.headers, data=payload)
    
      if response.status_code != 200:
        print(f"Error sending message to {wa_id_destino}: {response.status_code}, {response.text}")
