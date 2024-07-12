import os
import requests
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional

load_dotenv()
AUTH_KEY = os.getenv("AUTH_KEY")
API_URL = "https://api.turbo-smtp.com/api/v2/mail/send"
AUTH_USER_TSMTP = os.getenv("AUTH_USER_TSMTP")
AUTH_PASS_TSMTP = os.getenv("AUTH_PASS_TSMTP")

MAX_LENGTH_CORREO = 80

class EmailSchema(BaseModel):
    from_e: str = Field(..., max_length=MAX_LENGTH_CORREO)
    to: str = Field(..., max_length=MAX_LENGTH_CORREO)
    subject: str
    html_content: str
    content: str
    attachments: Optional[List[str]] = None

class EmailBatchSchema(BaseModel):
    emails: List[EmailSchema]

correo_router = APIRouter()

@correo_router.post("/send_email", tags=['correo'], status_code=200)
async def enviar_correos(batch: EmailBatchSchema, files: Optional[List[UploadFile]] = File(None)):
    for email in batch.emails:
        data = {
            "authuser": AUTH_USER_TSMTP,
            "authpass": AUTH_PASS_TSMTP,
            "from": email.from_e,
            "to": email.to,
            "subject": email.subject,
            "content": email.content,
            "html_content": email.html_content,
            "attachments": []
        }

        if files:
            for file in files:
                file_content = await file.read()
                encoded_file_content = file_content.encode("base64")  # encode file content in base64
                data["attachments"].append(
                    {
                        "filename": file.filename,
                        "content": encoded_file_content,
                        "type": file.content_type
                    }
                )

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

    return {"message": "Todos los correos fueron enviados exitosamente."}

