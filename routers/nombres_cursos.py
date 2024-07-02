import os
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from return_codes import *

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
nombres_cursos_router = APIRouter()


@nombres_cursos_router.get("/nombres_cursos", tags=['Funciones_Moodle'], status_code=200)
def nombres_cursos_bd():
    """
    ## **Descripción:**
    Esta función retorna la lista del nombre largo y corto de cada curso activo en la plataforma.

    ## **Parámetros obligatorios:**
        - sin parámetros.
        
    ## **Códigos retornados:**
        - 200 -> Registros encontrados.
        - 452 -> No se encontró información sobre ese curso en la base de datos.

    ## **Campos retornados:**
        - shortname -> Nombre corto del curso.
        - fullname -> Nombre largo del curso.
        - visible -> Tipo de visibilidad del curso.
        
        
    """
    with engine.connect() as connection:
        consulta_sql = text("""
            SELECT
                c.shortname, c.fullname, c.visible
            FROM
                mdl_course as c
            WHERE
                c.visible=1;
        """)
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