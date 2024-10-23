from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from urllib.parse import quote_plus
import requests
import csv
from celery import Celery
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()
usuario = os.getenv("USER_DB_UL_ADMIN")
contrasena = os.getenv("PASS_DB_UL_ADMIN")
host = os.getenv("HOST_DB_ADMIN")
nombre_base_datos = os.getenv("NAME_DB_UL_ADMIN")
AUTH_KEY = os.getenv("AUTH_KEY")
AUTH_USER_TSMTP = os.getenv("AUTH_USER_TSMTP")
AUTH_PASS_TSMTP = os.getenv("AUTH_PASS_TSMTP")

def get_database_url(user: str, password: str, host: str, port: str, db_name: str) -> str:
    password_encoded = quote_plus(password)
    return f"db+mysql://{user}:{password_encoded}@{host}:{port}/{db_name}"


# Configuración de la base de datos con SQLAlchemy (usa PostgreSQL o MySQL)
DATABASE_URL = get_database_url(usuario, contrasena, host, '3306', nombre_base_datos)

# Inicializar Celery con Redis como broker y la base de datos como backend
celery_app = Celery(
    'tasks',
    broker='redis://localhost:6379/0',  # Broker: Redis
    backend=DATABASE_URL  # Backend: Conexión a la base de datos para almacenar los resultados de las tareas
)

# Inicializar el router
correo_router = APIRouter()

class EmailSchema(BaseModel):
    from_e: str
    to: str
    subject: str
    cc: Optional[str] = None
    html_content: str
    content: str
    send_time: Optional[datetime] = None

class EmailBatchSchema(BaseModel):
    emails: List[EmailSchema]

# Función para guardar información en CSV
def guardar_en_csv(email: str, message_id: str):
    filename = 'temp_files/message_ids.csv'
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([email, message_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')])

# Tarea Celery para enviar correos
@celery_app.task
def enviar_correo(email_dict):
    data = {
        "authuser": AUTH_USER_TSMTP,
        "authpass": AUTH_PASS_TSMTP,
        "from": email_dict["from_e"],
        "to": email_dict["to"],
        "subject": email_dict["subject"],
        "cc": email_dict["cc"],
        "content": email_dict["content"],
        "html_content": email_dict["html_content"]
    }

    headers = {
        'Authorization': AUTH_KEY
    }

    try:
        response = requests.post("https://api.turbo-smtp.com/api/v2/mail/send", headers=headers, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar el correo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error enviando el correo a {email_dict['to']}")

    response_data = response.json()
    message_id = response_data.get('mid')

    if not message_id:
        raise HTTPException(status_code=500, detail=f"No se recibió el 'message_id' para {email_dict['to']}")

    print(f"Correo enviado exitosamente a {email_dict['to']}, message_id: {message_id}")
    
    guardar_en_csv(email_dict['to'], message_id)

    return {"message": "Correo enviado", "email": email_dict['to'], "message_id": message_id}

# Endpoint para programar correos
@correo_router.post("/send_email", tags=['correo'], status_code=200)
def programar_correos(batch: EmailBatchSchema):
    message_ids = []

    for email in batch.emails:
<<<<<<< HEAD
        email_dict = email.dict()  # Convertir el email a un diccionario

        if email.send_time is None or (isinstance(email.send_time, datetime) and email.send_time <= datetime.now()):
            # Enviar inmediatamente usando Celery
            result = enviar_correo.delay(email_dict)
            message_ids.append({"email": email.to, "task_id": result.id})
=======
        if email.send_time is None or email.send_time <= datetime.now():
            response = enviar_correo(email)
            message_ids.append({"email": email.to, "message_id": response.get("message_id")})
>>>>>>> parent of 0b3d6e9 (Manejo de formatos Null NaT)
            print(f"Correo enviado inmediatamente a {email.to}")
        else:
            # Se programa el envío para el futuro
            eta = email.send_time
            result = enviar_correo.apply_async((email_dict,), eta=eta)
            message_ids.append({"email": email.to, "task_id": result.id})
            print(f"Correo programado para {email.to} a las {email.send_time}")

    return {
        "message": "Correos programados exitosamente.",
        "jobs": message_ids
    }
