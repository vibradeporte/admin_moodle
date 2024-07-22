from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import pandas as pd
import openpyxl

nombres_cursos_router = APIRouter()

def get_database_url(user: str, password: str, host: str, port: str, db_name: str) -> str:
    password_encoded = quote_plus(password)
    return f"mysql+mysqlconnector://{user}:{password_encoded}@{host}:{port}/{db_name}"

@nombres_cursos_router.get("/nombres_cursos", tags=['Cursos'], status_code=200)
def nombres_cursos_bd(usuario: str, contrasena: str, host: str, port: str, nombre_base_datos: str):
    """
    ## **Descripción:**
    Esta función retorna la lista del nombre largo y corto de cada curso activo en la plataforma.

    ## **Parámetros obligatorios:**
        - usuario: Nombre de usuario de la base de datos.
        - contrasena: Contraseña de la base de datos.
        - host: Host de la base de datos.
        - port: Puerto de la base de datos.
        - nombre_base_datos: Nombre de la base de datos.

    ## **Códigos retornados:**
        - 200 -> Registros encontrados.
        - 452 -> No se encontró información sobre ese curso en la base de datos.

    ## **Campos retornados:**
        - shortname -> Nombre corto del curso.
        - fullname -> Nombre largo del curso.
        - visible -> Tipo de visibilidad del curso.
    """
    database_url = get_database_url(usuario, contrasena, host, port, nombre_base_datos)
    engine = create_engine(database_url)

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
        cursos_existentes = pd.DataFrame(rows, columns=column_names)

    file_path = 'temp_files/validacion_inicial.xlsx'
    datos = pd.read_excel(file_path)
    
    existing_courses = cursos_existentes['shortname'].tolist()
    datos['nombre_De_Curso_Invalido'] = datos['NOMBRE_CORTO_CURSO'].apply(
        lambda x: "NO" if x in existing_courses else "SI"
    )
    
    si_rows_count = (datos['nombre_De_Curso_Invalido'] == 'SI').sum()
    no_rows_count = (datos['nombre_De_Curso_Invalido'] == 'NO').sum()
    
    datos.to_excel(file_path, index=False, engine='openpyxl')
    
    if not datos.empty:
        message = (
            f"Validación de nombres de cursos: \n"
            f"{no_rows_count} Nombres de cursos correctos. \n"
            f"{si_rows_count} Nombres de cursos no validos. \n"
        )
        return PlainTextResponse(content=message)
    else:
        codigo = SIN_INFORMACION
        mensaje = HTTP_MESSAGES.get(codigo)
        raise HTTPException(codigo, mensaje)



