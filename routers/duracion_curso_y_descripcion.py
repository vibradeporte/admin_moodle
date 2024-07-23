import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import pandas as pd
from return_codes import *

# Longitud máxima del nombre corto del curso
max_length_courseshortname = 37

# Crear el enrutador de FastAPI
duracion_curso_y_descripcion_router = APIRouter()

def get_database_url(user: str, password: str, host: str, port: str, db_name: str) -> str:
    password_encoded = quote_plus(password)
    return f"mysql+mysqlconnector://{user}:{password_encoded}@{host}:{port}/{db_name}"

@duracion_curso_y_descripcion_router.post("/duracion_curso_y_descripcion", tags=['Moodle'], status_code=200)
async def duracion_curso_y_descripcion(
    usuario: str,
    contrasena: str,
    host: str,
    port: str,
    nombre_base_datos: str
):
    """
    ## **Descripción:**
    Esta función lee un archivo CSV con una columna 'NOMBRE_CORTO_CURSO', realiza la búsqueda de cada curso
    en la base de datos y agrega las columnas 'CourseId' y 'CourseDaysDuration' al mismo CSV.

    ## **Parámetros obligatorios:**
        - usuario: Usuario para la base de datos.
        - contrasena: Contraseña para la base de datos.
        - host: Host de la base de datos.
        - port: Puerto de la base de datos.
        - nombre_base_datos: Nombre de la base de datos.
        
    ## **Códigos retornados:**
        - 200: Registros encontrados y CSV actualizado.
        - 452: No se encontró información sobre algún curso en la base de datos.
        
    ## **Campos agregados al CSV:**
        - CourseId: ID del curso.
        - CourseDaysDuration: Duración del curso en días.
    """
    database_url = get_database_url(usuario, contrasena, host, port, nombre_base_datos)
    engine = create_engine(database_url)

    input_file = 'temp_files/estudiantes_validados.csv'
    if not os.path.exists(input_file):
        raise HTTPException(status_code=404, detail="El archivo estudiantes_validados.csv no existe.")

    df = pd.read_csv(input_file)

    if 'NOMBRE_CORTO_CURSO' not in df.columns:
        raise HTTPException(status_code=400, detail="El archivo CSV no contiene la columna 'NOMBRE_CORTO_CURSO'.")

    course_ids = []
    course_durations = []

    try:
        with engine.connect() as connection:
            for curso in df['NOMBRE_CORTO_CURSO']:
                consulta_sql = text("""
                    SELECT DISTINCT
                        c.id as CourseId,
                        SUBSTRING(c.idnumber, LOCATE('[', c.idnumber) + 1, LOCATE(']', c.idnumber) - LOCATE('[', c.idnumber) - 1) as CourseDaysDuration
                    FROM
                        mdl_course as c
                    WHERE
                        c.shortname = :curso
                    ORDER BY c.shortname;
                """).params(curso=curso)
                result = connection.execute(consulta_sql)
                row = result.fetchone()
                
                if row:
                    course_ids.append(row[0])
                    course_durations.append(row[1])
                else:
                    course_ids.append(None)
                    course_durations.append(None)

        df['CourseId'] = course_ids
        df['CourseDaysDuration'] = course_durations


        output_file = 'temp_files/estudiantes_validados.csv'
        df.to_csv(output_file, index=False)

        return FileResponse(output_file, media_type='text/csv', filename='estudiantes_validados.csv')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

