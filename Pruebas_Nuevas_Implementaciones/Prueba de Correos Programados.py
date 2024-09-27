import requests
from pydantic import BaseModel, Field
from typing import List
from threading import Timer
from datetime import datetime, timedelta

# Credenciales de TurboSMTP SE quitaron para no subirlos al commit
AUTH_KEY = ""
API_URL = "" 
AUTH_USER_TSMTP = ""
AUTH_PASS_TSMTP = ""

MAX_LENGTH_CORREO = 80


class EmailSchema(BaseModel):
    from_e: str = Field(..., max_length=MAX_LENGTH_CORREO)
    to: str = Field(..., max_length=MAX_LENGTH_CORREO)
    subject: str
    cc: str = None
    html_content: str
    content: str
    send_time: datetime  

class EmailBatchSchema(BaseModel):
    emails: List[EmailSchema]

# Función para enviar un correo
def send_email(email: EmailSchema):
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
        print(f"Enviando correo a {email.to} con asunto '{email.subject}'")
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        print(f"Correo enviado a {email.to}")
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar el correo a {email.to}: {str(e)}")
    
    if response.status_code != 200:
        print(f"Error al enviar el correo a {email.to}: {response.text}")
    else:
        response_data = response.json()
        return response_data.get('mid')


def schedule_email(email: EmailSchema):
    delay = (email.send_time - datetime.now()).total_seconds()
    
    if delay > 0:
        print(f"Correo programado para {email.to} en {email.send_time} con un retraso de {delay} segundos")
        Timer(delay, send_email, [email]).start()
    else:
        print(f"La hora de envío debe ser en el futuro. No se programará el correo para {email.to}.")


def enviar_correos(batch: EmailBatchSchema):
    for email in batch.emails:
        schedule_email(email)

    print("Todos los correos han sido programados para su envío.")


if __name__ == "__main__":
    email_batch = EmailBatchSchema(
        emails=[
            EmailSchema(
                from_e="soporte1@univlearning.com",
                to="mafenavas5@gmail.com",
                subject="Prueba 1",
                cc="",
                content="Este es el contenido del correo 1",
                html_content="<p>Este es el contenido del correo 1 en HTML</p>",
                send_time=datetime.now() + timedelta(minutes=10)
            ),
            EmailSchema(
                from_e="soporte1@eunivlearning.com",
                to="mafenavas5@gmail.com",
                subject="Prueba 32",
                cc="",
                content="Este es el contenido del correo 2",
                html_content="<p>Este es el contenido del correo 2 en HTML</p>",
                send_time=datetime.now() + timedelta(seconds=10)
            )
        ]
    )

    enviar_correos(email_batch)