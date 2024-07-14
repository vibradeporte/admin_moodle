import os
import requests
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
import pandas as pd

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


class EmailBatchSchema(BaseModel):
    emails: List[EmailSchema]


correo_router = APIRouter()


@correo_router.post("/send_email", tags=['correo'], status_code=200)
def enviar_correos(batch: EmailBatchSchema):
    message_ids = []

    for email in batch.emails:
        data = {
            "authuser": AUTH_USER_TSMTP,
            "authpass": AUTH_PASS_TSMTP,
            "from": email.from_e,
            "to": email.to,
            "subject": email.subject,
            "content": email.content,
            "html_content": email.html_content
        }

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

    # Save message_ids to a CSV file using pandas
    df = pd.DataFrame(message_ids, columns=["message_id"])
    csv_file_path = "temp_files/message_ids.csv"
    df.to_csv(csv_file_path, index=False)

    return {"message": "Todos los correos fueron enviados exitosamente.", "message_ids": message_ids, "csv_file_path": csv_file_path}
