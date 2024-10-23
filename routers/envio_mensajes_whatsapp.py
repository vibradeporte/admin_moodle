from fastapi import FastAPI, HTTPException, APIRouter
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from pydantic import BaseModel
from datetime import datetime
import requests
from typing import List, Optional
from urllib.parse import quote_plus
import csv
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()
usuario = os.getenv("USER_DB_UL_ADMIN")
contrasena = os.getenv("PASS_DB_UL_ADMIN")
host = os.getenv("HOST_DB_ADMIN")
nombre_base_datos = os.getenv("NAME_DB_UL_ADMIN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
id_telefono_env = os.getenv("ID_TELEFONO")


def get_database_url(user: str, password: str, host: str, port: str, db_name: str) -> str:
    password_encoded = quote_plus(password)
    return f"mysql+mysqlconnector://{user}:{password_encoded}@{host}:{port}/{db_name}"

DATABASE_URL = get_database_url(usuario, contrasena, host, '3306', nombre_base_datos)

# Configuración de APScheduler
jobstores = {
    'default': SQLAlchemyJobStore(url=DATABASE_URL)
}
scheduler = BackgroundScheduler(jobstores=jobstores)
scheduler.start()

envio_mensajes_whatsapp_router = APIRouter()

class WhatsAppMessageSchema(BaseModel):
    numero: str
    plantilla: str
    parametros: List[str]
    send_time: Optional[datetime] = None

class WhatsAppBatchSchema(BaseModel):
    mensajes: List[WhatsAppMessageSchema]

def guardar_en_csv(numero: str, message_id: str):
    filename = 'temp_files/whatsapp_message_ids.csv'
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([numero, message_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')])

def enviar_mensaje_whatsapp(mensaje: WhatsAppMessageSchema):
    FACEBOOK_API_URL = f"https://graph.facebook.com/v19.0/{id_telefono_env}/messages"
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }


    parameters = [{"type": "text", "text": param} for param in mensaje.parametros]

    data = {
            "messaging_product": "whatsapp",
            "to": mensaje.numero,
            "type": "template",
            "template": {
                "name": mensaje.plantilla,
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

    try:

        response = requests.post(FACEBOOK_API_URL, headers=headers, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar el mensaje a {mensaje.numero}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error enviando el mensaje a {mensaje.numero}")

    response_data = response.json()
    message_id = response_data.get('messages', [{}])[0].get('id')

    if not message_id:
        raise HTTPException(status_code=500, detail=f"No se recibió el 'message_id' para {mensaje.numero}")

    print(f"Mensaje enviado exitosamente a {mensaje.numero}, message_id: {message_id}")

    guardar_en_csv(mensaje.numero, message_id)

    return {"message": "Mensaje enviado", "numero": mensaje.numero, "message_id": message_id}


@envio_mensajes_whatsapp_router.post("/envio_mensajes_whatsapp/", tags=['Whatsapp'])
def programar_mensajes(mensajes: WhatsAppBatchSchema):
    message_ids = []

    for mensaje in mensajes.mensajes:
        if mensaje.send_time and mensaje.send_time <= datetime.now():
            raise HTTPException(status_code=400, detail="La fecha y hora deben estar en el futuro.")

        if not mensaje.send_time:
            response = enviar_mensaje_whatsapp(mensaje)
            message_ids.append({"numero": mensaje.numero, "message_id": response.get("message_id")})
            print(f"Mensaje enviado inmediatamente a {mensaje.numero}")
        else:
            job = scheduler.add_job(
                enviar_mensaje_whatsapp, 
                'date', 
                run_date=mensaje.send_time, 
                args=[mensaje]
            )
            print(f"Mensaje programado para {mensaje.numero} a las {mensaje.send_time}")
            message_ids.append({"numero": mensaje.numero, "job_id": job.id})

    return {
        "message": "Mensajes programados exitosamente.",
        "jobs": message_ids
    }

