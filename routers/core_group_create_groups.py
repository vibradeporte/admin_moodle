from fastapi import APIRouter, HTTPException, Form, Depends
from jwt_manager import JWTBearer
import requests
import pandas as pd
from datetime import datetime

# Definir el enrutador para la API de crear grupos
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

@core_group_create_groups_router.post("/core_group_create_groups/", tags=['Grupos'], dependencies=[Depends(JWTBearer())])
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
        df = pd.read_csv('temp_files/estudiantes_validados.csv')
    except Exception as e:
        raise HTTPException(status_code=400, detail="Error al leer el archivo CSV")

    if 'CourseId' not in df.columns:
        raise HTTPException(status_code=400, detail="El archivo CSV debe contener una columna 'CourseId'.")

    unique_course_ids = df['CourseId'].unique()
    fecha = datetime.now().strftime('%B_%d_%Y')

    # Diccionario para traducir meses de inglés a español
    meses_en_espanol = {
        'January': 'Enero',
        'February': 'Febrero',
        'March': 'Marzo',
        'April': 'Abril',
        'May': 'Mayo',
        'June': 'Junio',
        'July': 'Julio',
        'August': 'Agosto',
        'September': 'Septiembre',
        'October': 'Octubre',
        'November': 'Noviembre',
        'December': 'Diciembre'
    }

    # Extrae el nombre del mes en inglés y lo reemplaza por el equivalente en español
    mes_ingles = datetime.now().strftime('%B')
    fecha_en_espanol = fecha.replace(mes_ingles, meses_en_espanol[mes_ingles])

    successful_groups = []
    failed_groups = []

    url = f"{moodle_url}/webservice/rest/server.php"
    params = {
        "wstoken": moodle_token,
        "wsfunction": WS_FUNCTION,
        "moodlewsrestformat": "json"
    }

    for course_id in unique_course_ids:
        group_data = {
            "groups[0][courseid]": int(course_id),
            "groups[0][name]": {fecha_en_espanol},
            "groups[0][description]": f"Este grupo se compone de los estudiantes matriculados el día {fecha_en_espanol}"
        }

        try:
            response = requests.post(url, params=params, data=group_data)
            response.raise_for_status()
            response_dict = response.json()

            if 'exception' in response_dict:
                errorcode = response_dict.get('errorcode')
                if errorcode == "500" in response_dict.get('message', ''):
                    continue
                elif errorcode in HTTP_MESSAGES:
                    raise HTTPException(status_code=477, detail=HTTP_MESSAGES.get(errorcode))
            else:
                successful_groups.append(int(course_id))

        except requests.RequestException as e:
            failed_groups.append(int(course_id))
            raise HTTPException(status_code=500, detail=f"Error al comunicarse con Moodle: {str(e)}")
        except Exception as e:
            failed_groups.append(int(course_id))
            raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

    return {
        "message": "Operación completada",
        "grupos_creados": successful_groups,
        "grupos_no_creados": failed_groups
    }
