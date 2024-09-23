from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import pandas as pd
import re
import openpyxl

nombres_cursos_router = APIRouter()

def get_database_url(user: str, password: str, host: str, port: str, db_name: str) -> str:
    password_encoded = quote_plus(password)
    return f"mysql+mysqlconnector://{user}:{password_encoded}@{host}:{port}/{db_name}"

def limpiar_texto(texto: str) -> str:
    """
    Limpia un texto quitando todos los caracteres especiales excepto - y _.

    Parámetros:
        texto (str): Texto a limpiar

    Returns:
        str: Texto limpio
    """
    # Expresión regular que elimina todos los caracteres especiales excepto - y _
    texto_limpio = re.sub(r'[^\w_-]', '', str(texto))
    return texto_limpio.upper()

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
                mdl_course as c;
        """)
        result = connection.execute(consulta_sql)
        rows = result.fetchall()
        column_names = result.keys()
        cursos_existentes = pd.DataFrame(rows, columns=column_names)

    cursos_no_activos = cursos_existentes[cursos_existentes['visible'] == 0]

    ruta_archivo = 'temp_files/validacion_inicial.xlsx'
    datos = pd.read_excel(ruta_archivo)
    datos['NOMBRE_CORTO_CURSO'].fillna('SIN NOMBRE CORTO CURSO', inplace=True)
    datos['NOMBRE_LARGO_CURSO'].fillna('SIN NOMBRE LARGO CURSO', inplace=True)
    datos['NOMBRE_CORTO_CURSO'] = datos['NOMBRE_CORTO_CURSO'].apply(limpiar_texto)
    cursos_existentes_lista = cursos_existentes['shortname'].tolist()
    datos['nombre_De_Curso_Invalido'] = datos['NOMBRE_CORTO_CURSO'].apply(
        lambda x: "NO" if x in cursos_existentes_lista else "SI"
    )
    cursos_no_activos_lista = cursos_no_activos['shortname'].tolist()
    datos['¿El curso está deshabilitado para matrículas?'] = datos['NOMBRE_CORTO_CURSO'].apply(
        lambda x: "SI" if x in cursos_no_activos_lista else "NO" if x in cursos_existentes_lista else ""
    )


    datos['NOMBRE_LARGO_CURSO'] = datos['NOMBRE_CORTO_CURSO'].apply(
        lambda x: cursos_existentes.loc[cursos_existentes['shortname'] == x, 'fullname'].values[0]
        if not cursos_existentes.loc[cursos_existentes['shortname'] == x, 'fullname'].empty
        else "SIN NOMBRE LARGO CURSO"
    )

    si_rows_count = (datos['nombre_De_Curso_Invalido'] == 'SI').sum()
    no_rows_count = (datos['nombre_De_Curso_Invalido'] == 'NO').sum()
    
    datos.to_excel(ruta_archivo, index=False, engine='openpyxl')
    
    if not datos.empty:
        message = {
            "validacion_nombres_cursos": {
                "nombres_cursos_correctos": int(no_rows_count),
                "nombres_cursos_no_validos": int(si_rows_count)
            }
        }

        return JSONResponse(content=message)
    else:
        codigo = SIN_INFORMACION
        mensaje = HTTP_MESSAGES.get(codigo)
        raise HTTPException(codigo, mensaje)


