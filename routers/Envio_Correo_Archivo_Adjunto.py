from http.client import HTTPException
import os
import requests
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from fastapi import APIRouter, Query, Depends
from typing import List


max_lenght_correo = 80

class AttachmentSchema(BaseModel):
    content: str
    name: str
    type: str

class EmailSchema(BaseModel):
    from_e: str = Field(..., max_length=max_lenght_correo)
    to: str = Field(..., max_length=max_lenght_correo)
    subject: str
    html_content: str
    content: str
    attachments: List[AttachmentSchema] = []

load_dotenv()
AUTH_KEY = os.getenv("AUTH_KEY")
MVAPI_KEY = os.getenv("MVAPI_KEY")
API_URL = "https://api.turbo-smtp.com/api/v2/mail/send"
AUTH_USER_TSMTP = os.getenv("AUTH_USER_TSMTP")
AUTH_PASS_TSMTP = os.getenv("AUTH_PASS_TSMTP")

correo_router = APIRouter()

# Servicio para realizar envio de correos con la plataforma turboSMTP
@correo_router.post("/send_email", tags=['correo'], status_code=200)
def enviar_correo(email: EmailSchema):
    data = {
        "authuser": AUTH_USER_TSMTP,
        "authpass": AUTH_PASS_TSMTP,
        "from": email.from_e,
        "to": email.to,
        "subject": email.subject,
        "content": email.content,
        "html_content": email.html_content,
        "attachments": [
            {
                "content": attachment.content,
                "name": attachment.name,
                "type": attachment.type
            } for attachment in email.attachments
        ]
    }

    headers = {
        'Authorization': AUTH_KEY
    }

    try:
        # Realizar la petición POST a la API de turboSMTP
        response = requests.post(API_URL, headers=headers, json=data)
    except Exception as e:
        return e

    if response.status_code == 200:
        return {"message": "Correo enviado exitosamente."}
    else:
        # En caso de error, retorna un mensaje con el código de estado y el error
        raise HTTPException(response.status_code, response.text)
    













