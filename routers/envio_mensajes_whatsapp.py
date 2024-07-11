from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
import requests
from dotenv import load_dotenv
import os
from typing import List
import pandas as pd
import re

# Cargar variables de entorno desde el archivo .env
load_dotenv()

ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')

envio_mensajes_whatsapp_bienvenida_router = APIRouter()
envio_mensajes_whatsapp_router = APIRouter()

class MessageRequest(BaseModel):
    numero: str
    parametros: List[str]

@envio_mensajes_whatsapp_router.post("/envio_mensajes_whatsapp", tags=['Whatsapp'])
async def send_messages(plantilla: str, id_telefono: str, mensajes: List[MessageRequest]=None):
    """
    ## **Descripción:**
    Esta función permite enviar mensajes a whatsapp colectivamente.

    ## **Parámetros obligatorios:**
        - mensajes -> Lista de objetos que contiene todos los campos a enviar en la plantilla.

    ## **Códigos retornados:**
        - 200 -> Los mensajes se enviaron correctamente.
    """
    regex = r'^[0-9]+$'
    
    #for mensaje in mensajes:
        #if len(mensaje.numero) > 20:
            #codigo = SOBRAN_CARACTERES_20
            #mensaje_texto = HTTP_MESSAGES.get(codigo)
            #raise HTTPException(codigo, mensaje_texto)
        
        #if not re.match(regex, mensaje.numero):
            #codigo = TELEFONO_INCORRECTO
            #mensaje_texto = HTTP_MESSAGES.get(codigo)
            #raise HTTPException(codigo, mensaje_texto)
    
    FACEBOOK_API_URL = f"https://graph.facebook.com/v19.0/{id_telefono}/messages"

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
            results.append({
                "numero": mensaje.numero,
                "status": response.status_code,
                "error": response.text
            })
        else:
            results.append(response.json())
    
    return results

@envio_mensajes_whatsapp_bienvenida_router.post("/envio_mensajes_whatsapp_bienvenida_csv" ,tags=['Whatsapp'])
async def send_messages_csv(id_telefono: str):
    """
    ## **Descripción:**
    Esta función permite enviar mensajes a WhatsApp colectivamente desde un archivo CSV.

    ## **Parámetros obligatorios:**
        - file -> Archivo CSV que contiene todos los campos a enviar en la plantilla.
    """
    # Leer el archivo CSV
    df = pd.read_csv('temp_files/estudiantes_validados.csv')

    telefonos = "+" + df['phone1'].astype(str)
    nombres = df['firstname']
    apellidos = df['lastname']
    cursos = df['NOMBRE_LARGO_CURSO']
    mensaje_plantilla = "Hola {}, {}. Te has inscrito en el siguiente curso: {}. ¡Esperamos verte pronto!"

    # Crear una lista de mensajes
    mensajes = [
        MessageRequest(
            numero=telefono,
            parametros=[nombre, apellido, curso]
        ) for telefono, nombre, apellido, curso in zip(telefonos, nombres, apellidos, cursos)
    ]

    # Llamar a la función de envío de mensajes
    response = await send_messages(mensaje_plantilla, id_telefono, mensajes)

    return response