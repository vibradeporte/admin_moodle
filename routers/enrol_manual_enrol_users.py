from fastapi import APIRouter, HTTPException, UploadFile, Form
import pandas as pd
import requests
import os
from return_codes import *
import re
import csv
from datetime import datetime, timedelta


enrol_manual_enrol_users_router = APIRouter()



WS_FUNCTION = "enrol_manual_enrol_users"

@enrol_manual_enrol_users_router.post("/enrol_manual_enrol_users/", tags=['Moodle'])
async def enrol_manual_enrol_users(moodle_url: str = Form(...), moodle_token: str = Form(...)):
    """
    ## **Descripción:**
    Esta función permite inscribir usuarios a partir de un archivo excel en formato csv con los parámetros separados por comas de la siguiente manera:

        roleid,userid,courseid,timestart,timeend,suspend
        5,91,8,1720576273,1722217873,1

    ## **Parámetros obligatorios:**
        - roleid -> Id del rol para asignar al usuario.
        - userid -> Id del usuario que va a ser inscrito.
        - courseid -> Id del curso donde se va a inscribir al usuario.

    ## **Parámetros opcionales:**
        - timestart -> Marca de tiempo cuando comienza la inscripción en formato UNIX.
        - timeend -> Marca de tiempo cuando finaliza la inscripción en formato UNIX.
        - suspend -> Establecer en 1 para suspender la inscripción. Por defecto 0.
        

     ## **Códigos retornados:**
        - 200 -> La operación se realizó correctamente.
        - 454 -> La cantidad de caracteres supera el límite de 10 para este KEY.
        - 457 -> La cantidad de caracteres supera el límite de 1 para este KEY.
        - 460 -> La cantidad de caracteres es menor a lo permitido.
        - 465 -> Uno o varios caracteres ingresados son inválidos para este campo.
        - 474 -> Uno o varios caracteres ingresados no están permitidos en este campo. No se permiten letras, espacios ni números negativos.
        - 477 -> El curso consultado no existe.
        - 478 -> El usuario consultado no existe.
        - 484 -> La matrícula manual esta deshabilitada para este curso.


    ## **Valores permitidos en el campo timestart:**
        - Integer del timestamp en formato unix con la fecha de inicio de la matrícula.

    ## **Valores permitidos en el campo timeend:**
        - Integer del timestamp en formato unix con la fecha de finalización de la matrícula.

    ## **Valores permitidos en el campo suspend:**
        - 1 -> Suspender la inscripción.
        - 0 -> Normal.
    """
    
    data = {}
    df = pd.read_csv('temp_files/estudiantes_validados.csv')
    i = 0
    for i, row in df.iterrows():
        #ROLEID = row.get("roleid")
        USERID = row.get("userid")
        COURSEID = row.get("CourseId")
        TIMESTART = row.get("timestart")
        TIMEEND = row.get("timeend")
        #SUSPEND = row.get("suspend")

        
        data[f"enrolments[{i}][roleid]"]= 5
        data[f"enrolments[{i}][userid]"]= USERID
        data[f"enrolments[{i}][courseid]"]= COURSEID
        data[f"enrolments[{i}][timestart]"]= TIMESTART
        data[f"enrolments[{i}][timeend]"]= TIMEEND
        data[f"enrolments[{i}][suspend]"]= 0
        i += 1


    url = f"{moodle_url}/webservice/rest/server.php"
    print(data)
    params = {
        "wstoken": moodle_token,
        "wsfunction": WS_FUNCTION,
        "moodlewsrestformat": "json"
    }
    response = requests.post(url, params=params, data=data)
    response_dict = response.json()
    
    if response_dict == None:
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
    
