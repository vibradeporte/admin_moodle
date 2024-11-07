from fastapi import FastAPI, HTTPException, APIRouter, Depends
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from sqlalchemy import create_engine, MetaData, Table, update, desc
from jwt_manager import JWTBearer
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

DATABASE_URL = get_database_url(usuario, contrasena, host, '3306', nombre_base_datos)

# Configuración de APScheduler
jobstores = {
    'default': SQLAlchemyJobStore(url=DATABASE_URL)
}
scheduler = BackgroundScheduler(jobstores=jobstores)
scheduler.start()

envio_mensajes_whatsapp_router = APIRouter()

class WhatsAppMessageSchema(BaseModel):
    """
    Modelo para representar un mensaje de WhatsApp.

    Attributes:
        numero (str): Número de teléfono del destinatario.
        plantilla (str): Nombre de la plantilla de mensaje de WhatsApp.
        parametros (List[str]): Lista de parámetros para la plantilla.
        send_time (Optional[datetime]): Tiempo programado para enviar el mensaje (opcional).
    """
    numero: str
    plantilla: str
    parametros: List[str]
    send_time: Optional[datetime] = None
    identificacion: str
    nombre_corto_curso: str
    numero_sin_prefijo: str

class WhatsAppBatchSchema(BaseModel):
    """
    Modelo para representar un lote de mensajes de WhatsApp.

    Attributes:
        mensajes (List[WhatsAppMessageSchema]): Lista de mensajes de WhatsApp a enviar.
    """
    mensajes: List[WhatsAppMessageSchema]


def actualizar_estado_mensaje(database_url, valores_actualizar):
    """
    Actualiza el estado del mensaje de bienvenida por WhatsApp en la base de datos.

    :param database_url: URL de la base de datos
    :param valores_actualizar: Diccionario con los valores a actualizar, incluyendo los campos del WHERE (NOMBRE_CORTO_CURSO, IDENTIFICACION, MOVIL, FECHA_HORA_PROGRAMADA)
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
            'MOVIL': str(valores_actualizar.pop('MOVIL')).strip()
        }

        # Verificar si los valores están bien formateados
        print("Valores utilizados en las condiciones WHERE:", condiciones_actualizar_tabla)

        # Construir las condiciones WHERE comunes
        where_conditions = [
            detalle_matricula.c.NOMBRE_CORTO_CURSO == condiciones_actualizar_tabla['NOMBRE_CORTO_CURSO'],
            detalle_matricula.c.IDENTIFICACION == condiciones_actualizar_tabla['IDENTIFICACION'],
            detalle_matricula.c.MOVIL == condiciones_actualizar_tabla['MOVIL'],
            detalle_matricula.c.RES_MATRICULA == 'MATRICULADO'
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
                RES_WS_BIENVENIDA=valores_actualizar['RES_WS_BIENVENIDA'],
                ESTADO_WS_BIENVENIDA='ENVIADO',
                ID_WS_BIENVENIDA=valores_actualizar['ID_WS_BIENVENIDA']
            )
        )

        # Imprimir la consulta para depuración
        print("Query de actualización:", str(query))

        # Ejecutar la consulta
        connection.execute(query)
        select_query = detalle_matricula.select().where(detalle_matricula.c.ID_DETALLE_MATRICULA == result.ID_DETALLE_MATRICULA)
        verification_result = connection.execute(select_query).fetchone()
        return print("Registro actualizado:", verification_result)


# Función para enviar un mensaje de WhatsApp
def enviar_mensaje_whatsapp(mensaje: WhatsAppMessageSchema):
    """
    Envía un mensaje de WhatsApp usando la API de Facebook.

    Args:
        mensaje (WhatsAppMessageSchema): Información del mensaje de WhatsApp a enviar.

    Returns:
        dict: Mensaje de éxito y detalles del mensaje enviado.

    Raises:
        HTTPException: Si hay un error al enviar el mensaje.
    """
    FACEBOOK_API_URL = f"https://graph.facebook.com/v19.0/{id_telefono_env}/messages"
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }


    parameters = [{"type": "text", "text": param} for param in mensaje.parametros]

    valores_actualizar = {
        'IDENTIFICACION': mensaje.identificacion,
        'NOMBRE_CORTO_CURSO': mensaje.nombre_corto_curso,
        'MOVIL': mensaje.numero_sin_prefijo,
        'FECHA_HORA_PROGRAMADA': mensaje.send_time,
        
    }

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
    message_id = response_data.get("messages", [{}])[0].get("id", "unknown")
    message_status = response_data.get("messages", [{}])[0].get("message_status", "unknown")
    print(f"Mensaje enviado a {mensaje.numero} con estatus {message_status} y id {message_id}")

    if not message_id:
        raise HTTPException(status_code=500, detail=f"No se recibió el 'message_id' para {mensaje.numero}")

    print(f"Mensaje enviado exitosamente a {mensaje.numero}, message_id: {message_id}")

    valores_actualizar['ID_WS_BIENVENIDA'] = message_id
    valores_actualizar['RES_WS_BIENVENIDA'] = message_status
    
    print(valores_actualizar)
    actualizar_estado_mensaje(DATABASE_URL, valores_actualizar)

    return {"message": "Mensaje enviado", "numero": mensaje.numero, "message_id": message_id,"message_status": message_status}

# Endpoint para programar el envío de mensajes de WhatsApp
@envio_mensajes_whatsapp_router.post("/envio_mensajes_whatsapp/", tags=['Whatsapp'], dependencies=[Depends(JWTBearer())])
def programar_mensajes(mensajes: WhatsAppBatchSchema):
    """
    Programa el envío de mensajes de WhatsApp.

    Args:
        mensajes (WhatsAppBatchSchema): Lote de mensajes de WhatsApp a enviar.

    Returns:
        dict: Mensaje de éxito y lista de IDs de trabajos programados o mensajes enviados.
    """
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

