from fastapi import APIRouter, HTTPException, UploadFile, File
import requests
import os
from return_codes import *
import re
import locale
import pandas as pd
from datetime import datetime

core_group_create_groups_router = APIRouter()

locale.setlocale(locale.LC_TIME, 'es_ES.utf8')
MOODLE_URL = os.getenv("MOODLE_URL")
MOODLE_TOKEN = os.getenv("MOODLE_TOKEN")

WS_FUNCTION = "core_group_create_groups"


@core_group_create_groups_router.post("/core_group_create_groups/", tags=['Moodle'])
async def core_group_create_groups():
    """
    ## **Descripción:**
    Función para crear nuevos grupos dentro de un curso.

    ## **Parámetros obligatorios:**
        - courseid -> Id del curso.
        - name -> Nombre compatible con varios idiomas, curso único.
        - description -> Texto de descripción del grupo.
    
    ## **Parámetros opcionales:**
        - descriptionformat -> Formato de descripción (1 = HTML, 0 = MOODLE, 2 = PLAIN o 4 = MARKDOWN).
        - enrolmentkey -> Frase secreta de inscripción grupal
        - idnumber -> Número de identificación. Es de tipo String.
        - visibility -> Modo de visibilidad de grupo. 0 = Visible para todos. 1 = Visible para los miembros. 2 = Ver membresía propia. 3 = La membresía está oculta. predeterminado: 0.
        - participation -> ¿Está habilitada la participación en la actividad? Sólo para visibilidad de "todos" y "miembros". Verdadero predeterminado.

     ## **Códigos retornados:**
        - 200 -> La operación se realizó correctamente.
        - 452 -> La cantidad de caracteres supera el límite de 100 para este KEY.
        - 453 -> La cantidad de caracteres supera el límite de 255 para este KEY.
        - 454 -> La cantidad de caracteres supera el límite de 10 para este KEY.
        - 455 -> La cantidad de caracteres supera el límite de 2 para este KEY.
        - 457 -> La cantidad de caracteres supera el límite de 1 para este KEY.
        - 460 -> La cantidad de caracteres es menor a lo permitido.
        - 465 -> Uno o varios caracteres ingresados son inválidos para este campo.
        - 474 -> Uno o varios caracteres ingresados no están permitidos en este campo. No se permiten letras, espacios ni números negativos.
        - 477 -> El curso consultado no existe.
        - 482 -> El grupo ya existe en ese curso.


    """
        for i, course_id in enumerate(unique_course_ids):
        data[f"groups[{i}][courseid]"] = course_id
        data[f"groups[{i}][name]"] = datetime.now().strftime('%B_%d_%Y').capitalize()
        data[f"groups[{i}][description]"] = f"Este grupo se compone de los estudiantes matriculados el día {fecha}"
        # Agregar otros parámetros opcionales si es necesario
        # data[f"groups[{i}][descriptionformat]"] = 1  # Por ejemplo, si quieres usar HTML

    url = f"{MOODLE_URL}/webservice/rest/server.php"
    params = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": WS_FUNCTION,
        "moodlewsrestformat": "json"
    }

    response = requests.post(url, params=params, data=data)
    response_dict = response.json()
    for i, group in enumerate(response_dict):
        df.loc[df['CourseId'] == unique_course_ids[i], 'GroupId'] = group['id']
    df.to_csv('temp_files/estudiantes_actualizados.csv', index=False)

    if 'message' in response_dict and response_dict['message'] == 'Detectado valor de parámetro no válido':
        codigo = 482  # GRUPO_YA_EXISTE
        mensaje = HTTP_MESSAGES.get(codigo)
        raise HTTPException(codigo, mensaje)
    elif 'exception' in response_dict and response_dict['exception'] == 'moodle_exception':
        codigo = 477  # COURSE_NO_EXISTE
        mensaje = HTTP_MESSAGES.get(codigo)
        raise HTTPException(codigo, mensaje)


