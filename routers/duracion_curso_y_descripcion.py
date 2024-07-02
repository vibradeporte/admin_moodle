import os
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
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


@duracion_curso_y_descripcion_router.get("/duracion_curso_y_descripcion", tags=['Funciones_Moodle'], status_code=200)
def duracion_curso_y_descripcion(curso: str = Query(max_length=max_length_courseshortname)):
    """
    ## **Descripción:**
    Esta función retorna la duración de un curso en número de días y su descripción.

    ## **Parámetros obligatorios:**
        - curso -> Nombre corto del curso.
        
    ## **Códigos retornados:**
        - 200 -> Registros encontrados.
        - 452 -> No se encontró información sobre ese curso en la base de datos.

    ## **Campos retornados:**
        - CourseShortName -> Nombre corto del curso.
        - CourseFullName -> Nombre largo del curso.
        - CourseSummary -> Resumen del curso.
        - CourseDaysDuration -> Duración del curso en días.
    """
    with engine.connect() as connection:
        consulta_sql = text("""
            SELECT DISTINCT
                c.shortname as CourseShortName,
                c.fullname as CourseFullName,
                c.summary as CourseSummary,
                SUBSTRING(c.idnumber, LOCATE('[', c.idnumber) + 1, LOCATE(']', c.idnumber) - LOCATE('[', c.idnumber) - 1) as CourseDaysDuration
            FROM
                mdl_course as c

            WHERE
                c.shortname= :curso

            ORDER BY c.shortname;
        """).params(curso=curso)
        result = connection.execute(consulta_sql)
        rows = result.fetchall()
        column_names = result.keys()

        result_dicts = []
        for row in rows:
            row_dict = dict(zip(column_names, row))
            result_dicts.append(row_dict)

        if result_dicts:
            return JSONResponse(content=result_dicts)
        else:
            codigo = SIN_INFORMACION
            mensaje = HTTP_MESSAGES.get(codigo)
            raise HTTPException(codigo, mensaje)

        