from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
from dotenv import load_dotenv
import os
from typing import List
import re
import pandas as pd

load_dotenv()

ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
id_telefono_env = os.getenv('id_telefono')

if not ACCESS_TOKEN or not id_telefono_env:
    raise RuntimeError("ACCESS_TOKEN or id_telefono_env not set in environment variables")

# Error codes and messages
SOBRAN_CARACTERES_20 = 422
TELEFONO_INCORRECTO = 422
HTTP_MESSAGES = {
    SOBRAN_CARACTERES_20: "El número de teléfono excede los 20 caracteres permitidos.",
    TELEFONO_INCORRECTO: "El número de teléfono contiene caracteres no válidos."
}

# Setting up routers
envio_mensajes_whatsapp_router = APIRouter()

class MessageRequest(BaseModel):
    numero: str
    parametros: List[str]

@envio_mensajes_whatsapp_router.post("/envio_mensajes_whatsapp", tags=['Whatsapp'])
async def send_messages(plantilla: str, mensajes: List[MessageRequest] = None):
    """
    ## **Descripción:**
    Esta función permite enviar mensajes a whatsapp colectivamente.

    ## **Parámetros obligatorios:**
        - mensajes -> Lista de objetos que contiene todos los campos a enviar en la plantilla.

    ## **Códigos retornados:**
        - 200 -> Los mensajes se enviaron correctamente.
    """
    regex = r'^[0-9]+$'

    for mensaje in mensajes:
        if len(mensaje.numero) > 20:
            codigo = SOBRAN_CARACTERES_20
            mensaje_texto = HTTP_MESSAGES.get(codigo)
            print(f"Error {codigo}: {mensaje_texto} - {mensaje.numero}")
            raise HTTPException(status_code=codigo, detail=mensaje_texto)
        
        if not re.match(regex, mensaje.numero):
            codigo = TELEFONO_INCORRECTO
            mensaje_texto = HTTP_MESSAGES.get(codigo)
            print(f"Error {codigo}: {mensaje_texto} - {mensaje.numero}")
            raise HTTPException(status_code=codigo, detail=mensaje_texto)
    
    FACEBOOK_API_URL = f"https://graph.facebook.com/v19.0/{id_telefono_env}/messages"

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    results = []
    
    for mensaje in mensajes:
        parameters = [{"type": "text", "text": param} for param in mensaje.parametros]
        
        data = {
            "messaging_product": "whatsapp",
            "to": mensaje.numero,
            "type": "template",
            "template": {
                "name": plantilla,
                "language": {
                    "code": "es"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": parameters
                    }
                ]
            }
        }

        response = requests.post(FACEBOOK_API_URL, headers=headers, json=data)
        if response.status_code != 200:
            print(f"Failed to send message to {mensaje.numero}: {response.status_code} - {response.text}")
            results.append({
                "numero": mensaje.numero,
                "status": response.status_code,
                "error": response.text
            })
        else:
            response_json = response.json()
            message_id = response_json.get("messages", [{}])[0].get("id", "unknown")
            message_status = response_json.get("messages", [{}])[0].get("message_status", "unknown")
            print(f"Mensaje enviado a {mensaje.numero} con estatus {message_status} y id {message_id}")
            results.append({
                "numero": mensaje.numero,
                "message_status": message_status,
                "id": message_id
            })
    
    # Convert results to DataFrame
    df = pd.DataFrame(results)
    
    # Save DataFrame to CSV
    df.to_csv('temp_files/message_status_wapp.csv', index=False)
    
    return results
