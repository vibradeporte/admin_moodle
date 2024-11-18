import os
import pandas as pd
import requests
from fastapi import APIRouter, HTTPException, UploadFile, Form, Depends
from jwt_manager import JWTBearer
from return_codes import *
from datetime import datetime, timedelta

# Crear el enrutador de FastAPI
enrol_manual_enrol_users_router = APIRouter()

# Nombre de la función del servicio web de Moodle
WS_FUNCTION = "enrol_manual_enrol_users"

@enrol_manual_enrol_users_router.post("/api2/enrol_manual_enrol_users/", tags=['Moodle'], dependencies=[Depends(JWTBearer())])
async def enrol_manual_enrol_users(moodle_url: str = Form(...), moodle_token: str = Form(...)):
    """
    Inscribe usuarios a partir de un archivo CSV con los parámetros separados por comas.

    Args:
        moodle_url (str): URL del servidor Moodle.
        moodle_token (str): Token de autenticación para el servidor Moodle.

    Returns:
        dict: Respuesta en formato JSON con el resultado de la inscripción de usuarios.
    
    Raises:
        HTTPException: En caso de error, se retorna un código de error y un mensaje específico.
    """
    data = {}
    df_estudiantes = pd.read_csv('temp_files/estudiantes_validados.csv')
    indice = 0
    
    for indice, fila in df_estudiantes.iterrows():
        # Extraer datos necesarios de la fila del DataFrame
        usuario_id = fila.get("userid")
        curso_id = fila.get("CourseId")
        tiempo_inicio = int(fila.get("timestart"))
        tiempo_fin = int(fila.get("timeend"))

        # Construir los parámetros de inscripción
        data[f"enrolments[{indice}][roleid]"] = 5
        data[f"enrolments[{indice}][userid]"] = int(usuario_id)
        data[f"enrolments[{indice}][courseid]"] = int(curso_id)
        data[f"enrolments[{indice}][timestart]"] = int(tiempo_inicio)
        data[f"enrolments[{indice}][timeend]"] = int(tiempo_fin)
        data[f"enrolments[{indice}][suspend]"] = 0
        indice += 1

    # Definir la URL del servicio web de Moodle
    url = f"{moodle_url}/webservice/rest/server.php"
    
    params = {
        "wstoken": moodle_token,
        "wsfunction": WS_FUNCTION,
        "moodlewsrestformat": "json"
    }
    
    # Realizar la solicitud al servicio web
    response = requests.post(url, params=params, data=data)
    response_dict = response.json()
    
    # Manejo de respuestas según el contenido recibido
    if response_dict is None:
        codigo = OK
        mensaje = HTTP_MESSAGES.get(codigo)
        raise HTTPException(codigo, mensaje)
    if 'message' in response_dict and response_dict['message'] == 'Detectado un error de codificación, debe ser corregido por un programador: User ID does not exist or is deleted!':
        codigo = USER_NO_EXISTE
        mensaje = HTTP_MESSAGES.get(codigo)
        raise HTTPException(codigo, mensaje)
    if 'message' in response_dict and response_dict['message'] == 'Detectado valor de parámetro no válido':
        codigo = COURSE_NO_EXISTE
        mensaje = HTTP_MESSAGES.get(codigo)
        raise HTTPException(codigo, mensaje)
    if 'exception' in response_dict and response_dict['exception'] == 'moodle_exception':
        codigo = NO_MATRICULA_MANUAL
        mensaje = HTTP_MESSAGES.get(codigo)
        raise HTTPException(codigo, mensaje)
    
    return {"output": response.json()}
