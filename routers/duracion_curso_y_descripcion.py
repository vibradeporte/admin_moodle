import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import pandas as pd
from return_codes import *

# Longitud máxima del nombre corto del curso
max_length_courseshortname = 37

# Cargar variables de entorno
load_dotenv()
usuario = os.getenv("USER_DB_UL")
contrasena = os.getenv("PASS_DB_UL")
host = os.getenv("HOST_DB")
nombre_base_datos = os.getenv("NAME_DB_UL")

# Codificar la contraseña para la URL de conexión
contrasena_codificada = quote_plus(contrasena)
DATABASE_URL = f"mysql+mysqlconnector://{usuario}:{contrasena_codificada}@{host}/{nombre_base_datos}"
engine = create_engine(DATABASE_URL)

# Crear el enrutador de FastAPI
duracion_curso_y_descripcion_router = APIRouter()


@duracion_curso_y_descripcion_router.post("/duracion_curso_y_descripcion", tags=['Funciones_Moodle'], status_code=200)
def duracion_curso_y_descripcion():
    """
    ## **Descripción:**
    Esta función recibe un archivo CSV con una columna 'NOMBRE_CORTO_CURSO', realiza la búsqueda de cada curso
    en la base de datos y agrega las columnas 'CourseId' y 'CourseDaysDuration' al mismo CSV.

    ## **Parámetros obligatorios:**
        - file -> Archivo CSV que contiene una columna 'NOMBRE_CORTO_CURSO'.
        
    ## **Códigos retornados:**
        - 200 -> Registros encontrados y CSV actualizado.
        - 452 -> No se encontró información sobre algún curso en la base de datos.

    ## **Campos agregados al CSV:**
        - CourseId -> ID del curso.
        - CourseDaysDuration -> Duración del curso en días.
    """
    # Leer el archivo CSV
    df = pd.read_csv('temp_files/estudiantes_validados.csv')

    # Verificar si la columna 'NOMBRE_CORTO_CURSO' existe
    if 'NOMBRE_CORTO_CURSO' not in df.columns:
        codigo = SIN_INFORMACION
        mensaje = HTTP_MESSAGES.get(codigo)
        raise HTTPException(codigo, mensaje)

    # Inicializar listas para almacenar los resultados
    course_ids = []
    course_durations = []

    # Conectar a la base de datos y realizar las búsquedas
    with engine.connect() as connection:
        for curso in df['NOMBRE_CORTO_CURSO']:
            consulta_sql = text("""
                SELECT DISTINCT
                    c.id as CourseId,
                    SUBSTRING(c.idnumber, LOCATE('[', c.idnumber) + 1, LOCATE(']', c.idnumber) - LOCATE('[', c.idnumber) - 1) as CourseDaysDuration
                FROM
                    mdl_course as c
                WHERE
                    c.shortname= :curso
                ORDER BY c.shortname;
            """).params(curso=curso)
            result = connection.execute(consulta_sql)
            row = result.fetchone()
            
            if row:
                course_ids.append(row[0])  # Acceder por índice
                course_durations.append(row[1])  # Acceder por índice
            else:
                # Agregar valores nulos si no se encuentra información
                course_ids.append(None)
                course_durations.append(None)

    # Agregar los resultados al DataFrame
    df['CourseId'] = course_ids
    df['CourseDaysDuration'] = course_durations

    # Guardar el DataFrame actualizado a un nuevo archivo CSV
    output_file = 'temp_files/estudiantes_validados.csv'
    df.to_csv(output_file, index=False)

    return FileResponse(output_file, media_type='text/csv', filename='estudiantes_validados.csv')