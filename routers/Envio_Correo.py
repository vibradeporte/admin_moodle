import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, APIRouter, Depends
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from sqlalchemy import create_engine, update, Table, MetaData,desc
from pydantic import BaseModel
from datetime import datetime
from jwt_manager import JWTBearer
from typing import List, Optional
from urllib.parse import quote_plus


# Cargar variables de entorno
load_dotenv()
usuario = os.getenv("USER_DB_UL_ADMIN")
contrasena = os.getenv("PASS_DB_UL_ADMIN")
host = os.getenv("HOST_DB_ADMIN")
nombre_base_datos = os.getenv("NAME_DB_UL_ADMIN")
API_URL_ANALYTICS = "https://pro.api.serversmtp.com/api/v2/analytics/{}"
AUTH_KEY_TSMTP = os.getenv("AUTH_KEY_TSMTP")
AUTH_USER_TSMTP = os.getenv("AUTH_USER_TSMTP")
AUTH_PASS_TSMTP = os.getenv("AUTH_PASS_TSMTP")

# Obtener la URL de la base de datos
def get_database_url(user: str, password: str, host: str, port: str, db_name: str) -> str:
    """
    Construye la URL de conexión para la base de datos.

    Args:
        user (str): Usuario de la base de datos.
        password (str): Contraseña del usuario.
        host (str): Host de la base de datos.
        port (str): Puerto de la base de datos.
        db_name (str): Nombre de la base de datos.

    Returns:
        str: URL de conexión a la base de datos.
    """
    password_encoded = quote_plus(password)
    return f"mysql+mysqlconnector://{user}:{password_encoded}@{host}:{port}/{db_name}"

# Configuración de la base de datos con SQLAlchemy
DATABASE_URL = get_database_url(usuario, contrasena, host, '3306', nombre_base_datos)
jobstores = {
    'default': SQLAlchemyJobStore(url=DATABASE_URL)
}

# Crear y configurar el programador de trabajos en segundo plano
scheduler = BackgroundScheduler(jobstores=jobstores)
scheduler.start()
correo_router = APIRouter()

class EmailSchema(BaseModel):
    """
    Modelo para representar un correo electrónico.

    Attributes:
        from_e (str): Dirección de correo electrónico del remitente.
        to (str): Dirección de correo electrónico del destinatario.
        subject (str): Asunto del correo.
        cc (str): Dirección de correo electrónico para copia (opcional).
        html_content (str): Contenido HTML del correo.
        content (str): Contenido en texto plano del correo.
        send_time (Optional[datetime]): Tiempo programado para enviar el correo (opcional).
    """
    from_e: str
    to: str
    subject: str
    cc: Optional[str] = None
    html_content: str
    content: str
    send_time: Optional[datetime] = None

class EmailBatchSchema(BaseModel):
    """
    Modelo para representar un lote de correos electrónicos.

    Attributes:
        emails (List[EmailSchema]): Lista de correos electrónicos a enviar.
    """
    emails: List[EmailSchema]


def estatus_envio_correo(dict_mensajes_correo):
    # Asegurarse de que el message_id no tenga espacios u otros caracteres problemáticos
    message_id = str(dict_mensajes_correo['ID_CORREO_BIENVENIDA']).strip()
    message_id_encoded = quote_plus(message_id)

    # Construcción segura de la URL
    analytics_url = f"https://pro.api.serversmtp.com/api/v2/analytics/{message_id_encoded}"
    print(f"Fetching analytics for URL: {analytics_url}")  # Depuración: Imprimir la URL que se está consultando

    headers = {
        'Authorization': AUTH_KEY_TSMTP
    }

    try:
        response = requests.get(analytics_url, headers=headers)
        response.raise_for_status()  # Levantar un error si el estatus no es 200
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred for message_id {message_id}: {http_err}")
        return []  # Retornar una lista vacía si hay un error HTTP específico
    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud para el message_id {message_id}: {str(e)}")
        return []  # Retornar una lista vacía si hay un error de solicitud

    # Intentar analizar la respuesta
    if response.ok:
        analytics_data = response.json()
        print(f"Analytics data: {analytics_data}")
        dict_mensajes_correo['RES_CORREO_BIENVENIDA'] = analytics_data.get('status', 'SIN DATOS')
        return dict_mensajes_correo
    else:
        print("No se obtuvieron datos de analytics.")
        return []  # Retornar una lista vacía si no hay datos



def actualizar_estado_mensaje(database_url, valores_actualizar):
    """
    Actualiza el estado del mensaje de bienvenida por WhatsApp en la base de datos.

    :param database_url: URL de la base de datos
    :param valores_actualizar: Diccionario con los valores a actualizar, incluyendo los campos del WHERE (NOMBRE_CORTO_CURSO, IDENTIFICACION, CORREO, FECHA_HORA_PROGRAMADA)
    """
    # Crear una conexión a la base de datos
    engine = create_engine(database_url)
    metadata = MetaData()

    # Conectar con la tabla 'DETALLE_MATRICULA' con una conexión explícita
    with engine.begin() as connection:
        metadata.reflect(bind=connection)
        detalle_matricula = Table('DETALLE_MATRICULA', metadata, autoload_with=connection)

        # Verificar que la tabla se cargó correctamente
        print("Columnas de la tabla DETALLE_MATRICULA:", detalle_matricula.columns.keys())

        # Construir los valores y condiciones del WHERE
        condiciones_actualizar_tabla = {
            'NOMBRE_CORTO_CURSO': str(valores_actualizar.pop('NOMBRE_CORTO_CURSO')).strip(),
            'IDENTIFICACION': str(valores_actualizar.pop('IDENTIFICACION')).strip(),
            'CORREO': str(valores_actualizar.pop('CORREO')).strip()
        }

        # Verificar si los valores están bien formateados
        print("Valores utilizados en las condiciones WHERE:", condiciones_actualizar_tabla)

        # Construir las condiciones WHERE comunes
        where_conditions = [
            detalle_matricula.c.NOMBRE_CORTO_CURSO == condiciones_actualizar_tabla['NOMBRE_CORTO_CURSO'],
            detalle_matricula.c.IDENTIFICACION == condiciones_actualizar_tabla['IDENTIFICACION'],
            detalle_matricula.c.CORREO == condiciones_actualizar_tabla['CORREO']
        ]

        # Si FECHA_HORA_PROGRAMADA tiene un valor, agregar la condición al WHERE
        fecha_hora_programada = valores_actualizar.pop('FECHA_HORA_PROGRAMADA', None)
        if fecha_hora_programada is not None:
            where_conditions.append(detalle_matricula.c.FECHA_HORA_PROGRAMADA == fecha_hora_programada)

        # Consulta con todas las condiciones, ordenando por ID para obtener el registro más nuevo
        print("Condiciones WHERE antes de la consulta:", where_conditions)
        select_query = detalle_matricula.select().where(*where_conditions).order_by(desc(detalle_matricula.c.ID_DETALLE_MATRICULA)).limit(1)
        result = connection.execute(select_query).fetchone()

        if not result:
            print("No se encontraron registros con las condiciones especificadas.")
            print("Condiciones WHERE:", {key: value for key, value in condiciones_actualizar_tabla.items() if key != 'FECHA_HORA_PROGRAMADA' or value is not None})
            return
        else:
            print("Registro encontrado:", result)

        # Ejecutar el update si se encontró el registro
        query = (
            update(detalle_matricula)
            .where(detalle_matricula.c.ID_DETALLE_MATRICULA == result.ID_DETALLE_MATRICULA)
            .values(
                RES_CORREO_BIENVENIDA=valores_actualizar['RES_CORREO_BIENVENIDA'],
                ESTADO_CORREO_BIENVENIDA='ENVIADO',
                ID_CORREO_BIENVENIDA=valores_actualizar['ID_CORREO_BIENVENIDA']
            )
        )

        # Imprimir la consulta para depuración
        print("Query de actualización:", str(query))

        # Ejecutar la consulta
        connection.execute(query)
        select_query = detalle_matricula.select().where(detalle_matricula.c.ID_DETALLE_MATRICULA == result.ID_DETALLE_MATRICULA)
        verification_result = connection.execute(select_query).fetchone()
        return print("Registro actualizado:", verification_result)




# Función para enviar un correo electrónico
def enviar_correo(email: EmailSchema):
    """
    Envía un correo electrónico usando la API de TurboSMTP.

    Args:
        email (EmailSchema): Información del correo electrónico a enviar.

    Returns:
        dict: Mensaje de éxito y detalles del correo enviado.

    Raises:
        HTTPException: Si hay un error al enviar el correo.
    """

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
    content = data["content"]
    # Dividir la cadena por el guion '-'
    nombres = content.split('-')
    datos_separados = {
    "NOMBRE_CORTO_CURSO": nombres[0],  # Extrae 'INDU_PYTHON'
    "IDENTIFICACION": nombres[1]  # Extrae '1098813244'
}
    valores_actualizar = {
        'CORREO': email.to,
        'NOMBRE_CORTO_CURSO': datos_separados.get('NOMBRE_CORTO_CURSO'),
        'IDENTIFICACION': datos_separados.get('IDENTIFICACION'),
        'FECHA_HORA_PROGRAMADA': email.send_time
    }
    headers = {
        'Authorization': AUTH_KEY_TSMTP
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
    
    valores_actualizar['ID_CORREO_BIENVENIDA'] = message_id
    print(valores_actualizar)
    estatus_envio_correo(valores_actualizar)
    actualizar_estado_mensaje(DATABASE_URL, valores_actualizar)

    return {"message": "Correo enviado", "email": email.to, "message_id": message_id}

# Endpoint para programar el envío de correos electrónicos
@correo_router.post("/Envio_Programados_Correos/", tags=['correo'], status_code=200, dependencies=[Depends(JWTBearer())])
def programar_correos(batch: EmailBatchSchema):
    """
    Programa el envío de correos electrónicos.

    Args:
        batch (EmailBatchSchema): Lote de correos electrónicos a enviar.

    Returns:
        dict: Mensaje de éxito y lista de IDs de trabajos programados o mensajes enviados.
    """
    message_ids = [] 

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

    return {
        "message": "Correos programados exitosamente.",
        "jobs": message_ids
    }

