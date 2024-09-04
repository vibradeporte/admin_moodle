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

def construir_url_mysql(usuario_base_datos: str, contrasena_base_datos: str, host_base_datos: str, puerto_base_datos: str, nombre_base_datos: str) -> str:
    """
    Convierte los parámetros para una conexión a una base de datos MySQL en una cadena de conexión compatible con sqlalchemy.

    Parámetros:
    usuario_bd (str): El usuario de la base de datos.
    contrasena_bd (str): La contraseña de la base de datos.
    host_bd (str): El host de la base de datos.
    puerto_bd (str): El puerto de la base de datos.
    nombre_bd (str): El nombre de la base de datos.

    Regresa:
    str: La cadena de conexión compatible con sqlalchemy.
    """
    contrasena_codificada = quote_plus(contrasena_base_datos)
    return f"mysql+mysqlconnector://{usuario_base_datos}:{contrasena_codificada}@{host_base_datos}:{puerto_base_datos}/{nombre_base_datos}"

@duracion_curso_y_descripcion_router.post("/duracion_curso_y_descripcion", tags=['Cursos'], status_code=200)
async def duracion_curso_y_descripcion(
    usuario_base_datos: str,
    contrasena_base_datos: str,
    host_base_datos: str,
    puerto_base_datos: str,
    nombre_base_datos: str
):
    """
    ## **Descripción:**
    Esta función lee un archivo excel con una columna 'NOMBRE_CORTO_CURSO', realiza la búsqueda de cada curso
    en la base de datos y agrega las columnas 'CourseId' y 'CourseDaysDuration' al mismo excel.

    ## **Parámetros obligatorios:**
        - usuario_base_datos: Usuario para la base de datos.
        - contrasena_base_datos: Contraseña para la base de datos.
        - host_base_datos: Host de la base de datos.
        - puerto_base_datos: Puerto de la base de datos.
        - nombre_base_datos: Nombre de la base de datos.
        
    ## **Códigos retornados:**
        - 200: Registros encontrados y Excel actualizado.
        - 452: No se encontró información sobre algún curso en la base de datos.
        
    ## **Campos agregados al Excel:**
        - CourseId: ID del curso.
        - CourseDaysDuration: Duración del curso en días.
    """
    url_base_datos = construir_url_mysql(usuario_base_datos, contrasena_base_datos, host_base_datos, puerto_base_datos, nombre_base_datos)
    motor_base_datos = create_engine(url_base_datos)

    archivo_de_entrada = 'temp_files/validacion_inicial.xlsx'
    if not os.path.exists(archivo_de_entrada):
        raise HTTPException(status_code=404, detail="El archivo estudiantes_validados.xslsx no existe.")

    df_estudiantes = pd.read_excel(archivo_de_entrada)

    if 'NOMBRE_CORTO_CURSO' not in df_estudiantes.columns:
        raise HTTPException(status_code=400, detail="El archivo Excel no contiene la columna 'NOMBRE_CORTO_CURSO'.")

    course_ids = []
    course_durations = []

    try:
        with motor_base_datos.connect() as connection:
            for curso in df_estudiantes['NOMBRE_CORTO_CURSO']:
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

        df_estudiantes['CourseId'] = course_ids
        df_estudiantes['CourseDaysDuration'] = course_durations



        df_estudiantes.to_excel(archivo_de_entrada, index=False)

        return FileResponse(archivo_de_entrada, media_type='xslx', filename='validacion_inicial.xlsx')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

