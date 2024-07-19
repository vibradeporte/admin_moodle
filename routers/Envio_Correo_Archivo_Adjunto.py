import os
import requests
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional

load_dotenv()
AUTH_KEY = os.getenv("AUTH_KEY")
API_URL = "https://api.turbo-smtp.com/api/v2/mail/send"
AUTH_USER_TSMTP = os.getenv("AUTH_USER_TSMTP")
AUTH_PASS_TSMTP = os.getenv("AUTH_PASS_TSMTP")

MAX_LENGTH_CORREO = 80

class AttachmentSchema(BaseModel):
    content: str
    name: str
    type: str

class EmailSchema(BaseModel):
    from_e: EmailStr = Field(..., max_length=MAX_LENGTH_CORREO)
    to: EmailStr = Field(..., max_length=MAX_LENGTH_CORREO)
    subject: str
    cc: Optional[EmailStr] = None
    html_content: str
    content: str
    attachments: Optional[List[AttachmentSchema]] = None

class EmailBatchSchema(BaseModel):
    emails: List[EmailSchema]

correo_archivo_adjunto_router = APIRouter()

@correo_archivo_adjunto_router.post("/enviar_correos_archivo_adjunto", tags=['correo'], status_code=200)
def enviar_correos(batch: EmailBatchSchema):
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









