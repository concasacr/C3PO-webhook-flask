# app/whatsapp_client.py

import os
import requests
import json

import sys
sys.path.append('../')
import config as _ # Esto ejecuta config.py y carga las variables de entorno.

class WhatsAppWrapper:

    API_URL = "https://graph.facebook.com/v13.0/"
    API_TOKEN = os.environ.get("WHATSAPP_API_TOKEN")
    NUMBER_ID = os.environ.get("WHATSAPP_NUMBER_ID")

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {self.API_TOKEN}",
            "Content-Type": "application/json",
        }
        self.API_URL = self.API_URL + self.NUMBER_ID

    def send_template_message(self, template_name, language_code, phone_number):

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
            return {"error": f"Error sending message: {response.status_code}, {response.text}"}
        else:
            return response
