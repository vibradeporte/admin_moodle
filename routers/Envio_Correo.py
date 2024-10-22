from fastapi import FastAPI, HTTPException, APIRouter
#from apscheduler.schedulers.background import BackgroundScheduler
#from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from pydantic import BaseModel
from datetime import datetime
import requests
from typing import List, Optional
from urllib.parse import quote_plus
import csv
from dotenv import load_dotenv
import os

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
    return f"mysql+mysqlconnector://{user}:{password_encoded}@{host}:{port}/{db_name}"

# Configuración de la base de datos con SQLAlchemy (usa PostgreSQL o MySQL)
DATABASE_URL = get_database_url(usuario, contrasena, host, '3306', nombre_base_datos)

jobstores = {
    'default': SQLAlchemyJobStore(url=DATABASE_URL) 
}

scheduler = BackgroundScheduler(jobstores=jobstores)
scheduler.start()
correo_router = APIRouter()

class EmailSchema(BaseModel):
    from_e: str
    to: str
    subject: str
    cc: str = None
    html_content: str
    content: str
    send_time: Optional[datetime] = None

class EmailBatchSchema(BaseModel):
    emails: List[EmailSchema]

def guardar_en_csv(email: str, message_id: str):
    filename = 'temp_files/message_ids.csv'
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([email, message_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')])

def enviar_correo(email: EmailSchema):
    data = {
        "authuser": AUTH_USER_TSMTP,
        "authpass": AUTH_PASS_TSMTP,  
        "from": email.from_e,
        "to": email.to,
        "subject": email.subject,
        "cc": email.cc,
        "content": email.content,
        "html_content": email.html_content
    }

    headers = {
        'Authorization': AUTH_KEY
    }

    try:

        response = requests.post("https://api.turbo-smtp.com/api/v2/mail/send", headers=headers, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar el correo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error enviando el correo a {email.to}")

    response_data = response.json()
    message_id = response_data.get('mid')

    if not message_id:
        raise HTTPException(status_code=500, detail=f"No se recibió el 'message_id' para {email.to}")

    print(f"Correo enviado exitosamente a {email.to}, message_id: {message_id}")
    
    guardar_en_csv(email.to, message_id)

    return {"message": "Correo enviado", "email": email.to, "message_id": message_id}


@correo_router.post("/send_email", tags=['correo'], status_code=200)
def programar_correos(batch: EmailBatchSchema):
    message_ids = [] 
"""
    for email in batch.emails:
        if email.send_time is None or (isinstance(email.send_time, datetime) and email.send_time <= datetime.now()):
            response = enviar_correo(email)
            message_ids.append({"email": email.to, "message_id": response.get("message_id")})
            print(f"Correo enviado inmediatamente a {email.to}")
        else:
            job = scheduler.add_job(
                enviar_correo, 
                'date', 
                run_date=email.send_time, 
                args=[email]
            )
            print(f"Correo programado para {email.to} a las {email.send_time}")
            message_ids.append({"email": email.to, "job_id": job.id})
"""
    return {
        "message": "Correos programados exitosamente.",
        "jobs": message_ids
    }







