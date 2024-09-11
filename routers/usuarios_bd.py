from return_codes import *
import os
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from fastapi import APIRouter, HTTPException
import pandas as pd


def get_database_url(user: str, password: str, host: str, port: str, db_name: str) -> str:
    password_encoded = quote_plus(password)
    return f"mysql+mysqlconnector://{user}:{password_encoded}@{host}:{port}/{db_name}"


usuarios_bd_router = APIRouter()


@usuarios_bd_router.get("/usuarios_completos_bd/", tags=['Moodle'], status_code=200)
def lista_usuarios_bd(
    usuario: str,
    contrasena: str,
    host: str,
    port: str,
    nombre_base_datos: str
):
    
    """
    ## **Descripción:**
    Esta función retorna la lista completa de usuarios registrados en la base de datos.

    ## **Parámetros obligatorios:**
        - sin parámetros.
        
    ## **Códigos retornados:**
        - 200 -> Registros encontrados.
        - 452 -> No se encontró información sobre ese curso en la base de datos.

    ## **Campos retornados:**
        - username -> Username del usuario.
        - firstname -> Nombres del usuario.
        - lastname -> Apellidos del usuario.
        - email -> Email del usuario.
        - phone1 -> teléfono del usuario.
        
    """
    database_url = get_database_url(usuario, contrasena, host, port, nombre_base_datos)
    engine = create_engine(database_url)
    with engine.connect() as connection:
        consulta_sql = text("""
            select
                u.username, u.firstname, u.lastname, u.email, u.phone1
            FROM
                mdl_user as u;
        """)
        result = connection.execute(consulta_sql)
        rows = result.fetchall()
        column_names = result.keys()

        result_dicts = []
        for row in rows:
            row_dict = dict(zip(column_names, row))
            result_dicts.append(row_dict)

        if result_dicts:
            df = pd.DataFrame(result_dicts)
            csv_file_path = "temp_files/usuarios_completos.csv"
            df.to_csv(csv_file_path, index=False)

            return JSONResponse({'message': 'Registros encontrados de todos los usuarios'})
        else:
            codigo = SIN_INFORMACION
            mensaje = HTTP_MESSAGES.get(codigo)
            raise HTTPException(codigo, mensaje)

