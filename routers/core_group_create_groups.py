from fastapi import APIRouter, HTTPException, UploadFile, File, Form
import requests
import pandas as pd
from datetime import datetime
from typing import Dict, List

core_group_create_groups_router = APIRouter()
WS_FUNCTION = "core_group_create_groups"

HTTP_MESSAGES = {
    452: "La cantidad de caracteres supera el límite de 100 para este KEY.",
    453: "La cantidad de caracteres supera el límite de 255 para este KEY.",
    454: "La cantidad de caracteres supera el límite de 10 para este KEY.",
    455: "La cantidad de caracteres supera el límite de 2 para este KEY.",
    457: "La cantidad de caracteres supera el límite de 1 para este KEY.",
    460: "La cantidad de caracteres es menor a lo permitido.",
    465: "Uno o varios caracteres ingresados son inválidos para este campo.",
    474: "Uno o varios caracteres ingresados no están permitidos en este campo. No se permiten letras, espacios ni números negativos.",
    477: "El curso consultado no existe.",
    482: "El grupo ya existe en ese curso."
}

@core_group_create_groups_router.post("/core_group_create_groups/", tags=['Grupos'])
async def core_group_create_groups(
    moodle_url: str = Form(...),
    moodle_token: str = Form(...)
):
    """
    ## **Descripción:**
    Función para crear nuevos grupos dentro de un curso.

    ## **Parámetros obligatorios:**
        - moodle_url -> URL de la plataforma Moodle.
        - moodle_token -> Token de autenticación de Moodle.
        - file -> Archivo CSV con la información de los estudiantes.

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
    try:
        # Read the uploaded file into a DataFrame
        df = pd.read_csv('temp_files/estudiantes_validados.csv')
    except Exception as e:
        raise HTTPException(status_code=400, detail="Error al leer el archivo CSV")

    if 'CourseId' not in df.columns:
        raise HTTPException(status_code=400, detail="El archivo CSV debe contener una columna 'CourseId'.")

    unique_course_ids = df['CourseId'].unique()
    data = {}
    fecha = datetime.now().strftime('%Y-%m-%d_%H')

    for i, course_id in enumerate(unique_course_ids):
        data[f"groups[{i}][courseid]"] = int(course_id)  # Convert to native Python int
        data[f"groups[{i}][name]"] = f"Grupo_{course_id}_{fecha}"
        data[f"groups[{i}][description]"] = f"Este grupo se compone de los estudiantes matriculados el día {fecha}"

    url = f"{moodle_url}/webservice/rest/server.php"
    params = {
        "wstoken": moodle_token,
        "wsfunction": WS_FUNCTION,
        "moodlewsrestformat": "json"
    }

    successful_groups = []
    failed_groups = []

    for i, course_id in enumerate(unique_course_ids):
        group_data = {
            "groups[0][courseid]": int(course_id),  # Convert to native Python int
            "groups[0][name]": f"Grupo_{course_id}_{fecha}",
            "groups[0][description]": f"Este grupo se compone de los estudiantes matriculados el día {fecha}"
        }

        try:
            response = requests.post(url, params=params, data=group_data)
            response.raise_for_status()
            response_dict = response.json()

            if 'exception' in response_dict:
                errorcode = response_dict.get('errorcode')
                if errorcode in HTTP_MESSAGES:
                    if errorcode == "482":
                        # Group already exists, continue to the next one
                        continue
                    else:
                        raise HTTPException(status_code=477, detail=HTTP_MESSAGES.get(errorcode))
                else:
                    raise HTTPException(status_code=500, detail="Error desconocido al crear grupos en Moodle")
            else:
                successful_groups.append(int(course_id))  # Convert to native Python int

        except requests.RequestException as e:
            failed_groups.append(int(course_id))  # Convert to native Python int
            raise HTTPException(status_code=500, detail=f"Error al comunicarse con Moodle: {str(e)}")

    return {
        "message": "Operación completada",
        "successful_groups": successful_groups,
        "failed_groups": failed_groups
    }
