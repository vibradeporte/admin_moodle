import os
import requests
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from jwt_manager import JWTBearer

# Cargar variables de entorno
load_dotenv()
AUTH_KEY = os.getenv("AUTH_KEY")
API_URL = "https://api.turbo-smtp.com/api/v2/mail/send"
AUTH_USER_TSMTP = os.getenv("AUTH_USER_TSMTP")
AUTH_PASS_TSMTP = os.getenv("AUTH_PASS_TSMTP")

MAX_LENGTH_CORREO = 80

class AttachmentSchema(BaseModel):
    """
    Modelo para representar un archivo adjunto.

    Attributes:
        content (str): Contenido del archivo adjunto codificado en base64.
        name (str): Nombre del archivo adjunto.
        type (str): Tipo MIME del archivo adjunto.
    """
    content: str
    name: str
    type: str

class EmailSchema(BaseModel):
    """
    Modelo para representar un correo electrónico.

    Attributes:
        from_e (EmailStr): Dirección de correo electrónico del remitente.
        to (EmailStr): Dirección de correo electrónico del destinatario.
        subject (str): Asunto del correo.
        cc (str): Dirección de correo electrónico para copia (opcional).
        html_content (str): Contenido HTML del correo.
        content (str): Contenido en texto plano del correo.
        attachments (Optional[List[AttachmentSchema]]): Lista de archivos adjuntos (opcional).
    """
    from_e: EmailStr = Field(..., max_length=MAX_LENGTH_CORREO)
    to: EmailStr = Field(..., max_length=MAX_LENGTH_CORREO)
    subject: str
    cc: Optional[str] = None
    html_content: str
    content: str
    attachments: Optional[List[AttachmentSchema]] = None

class EmailBatchSchema(BaseModel):
    """
    Modelo para representar un lote de correos electrónicos.

    Attributes:
        emails (List[EmailSchema]): Lista de correos electrónicos a enviar.
    """
    emails: List[EmailSchema]

# Crear el enrutador de FastAPI
correo_archivo_adjunto_router = APIRouter()

@correo_archivo_adjunto_router.post("/Envio_Archivo_Adjunto/", tags=['correo'], status_code=200, dependencies=[Depends(JWTBearer())])
def enviar_correos(batch: EmailBatchSchema):
    """
    Envía un lote de correos electrónicos con posibles archivos adjuntos.

    Args:
        batch (EmailBatchSchema): Lote de correos electrónicos a enviar.

    Returns:
        dict: Mensaje de éxito y lista de IDs de los mensajes enviados.
    
    Raises:
        HTTPException: Si hay un error al enviar los correos o faltan las credenciales de autenticación.
    """
    if not AUTH_USER_TSMTP or not AUTH_PASS_TSMTP or not AUTH_KEY:
        raise HTTPException(status_code=500, detail="Missing email authentication credentials")

    message_ids = []

    for email in batch.emails:
        data = {
            "authuser": AUTH_USER_TSMTP,
            "authpass": AUTH_PASS_TSMTP,
            "from": email.from_e,
            "to": email.to,
            "subject": email.subject,
            "content": email.content,
            "html_content": email.html_content,
        }

        if email.cc:
            data["cc"] = email.cc

        if email.attachments:
            data["attachments"] = [
                {
                    "content": attachment.content,
                    "name": attachment.name,
                    "type": attachment.type
                } for attachment in email.attachments
            ]

        headers = {
            'Authorization': AUTH_KEY
        }

        try:
            response = requests.post(API_URL, headers=headers, json=data)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Error sending email to {email.to}: {str(e)}")

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"Error sending email to {email.to}: {response.text}")

        response_data = response.json()
        message_id = response_data.get('mid')
        if message_id:
            message_ids.append(message_id)

    return {"message": "Todos los correos fueron enviados exitosamente.", "message_ids": message_ids}










