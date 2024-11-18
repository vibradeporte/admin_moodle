from return_codes import *
import os
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from fastapi import APIRouter, HTTPException, Depends
from jwt_manager import JWTBearer
import pandas as pd
import unidecode

# Inicializar el router para usuarios de la base de datos
usuarios_bd_router = APIRouter()

def get_database_url(user: str, password: str, host: str, port: str, db_name: str) -> str:
    """
    Construye la URL de conexión a la base de datos.

    :param user: Usuario de la base de datos.
    :param password: Contraseña del usuario de la base de datos.
    :param host: Host de la base de datos.
    :param port: Puerto de la base de datos.
    :param db_name: Nombre de la base de datos.
    :return: URL de conexión a la base de datos.
    """
    password_encoded = quote_plus(password)
    return f"mysql+mysqlconnector://{user}:{password_encoded}@{host}:{port}/{db_name}"

@usuarios_bd_router.get("/api2/usuarios_completos_bd/", tags=['Moodle'], status_code=200, dependencies=[Depends(JWTBearer())])
def lista_usuarios_bd(
    usuario: str,
    contrasena: str,
    host: str,
    port: str,
    nombre_base_datos: str
):
    """
    Retorna la lista completa de usuarios registrados en la base de datos.

    ## Parámetros:
    - usuario: Usuario de la base de datos.
    - contrasena: Contraseña del usuario de la base de datos.
    - host: Host de la base de datos.
    - port: Puerto de la base de datos.
    - nombre_base_datos: Nombre de la base de datos.

    ## Retorno:
    - JSONResponse con un mensaje de éxito si se encuentran registros.
    - HTTPException si no se encuentran registros.
    """
    database_url = get_database_url(usuario, contrasena, host, port, nombre_base_datos)
    engine = create_engine(database_url)
    with engine.connect() as connection:
        consulta_sql = text("""
            SELECT
                u.username, u.firstname, u.lastname, u.email, u.phone1
            FROM
                mdl_user AS u;
        """)
        result = connection.execute(consulta_sql)
        rows = result.fetchall()
        column_names = result.keys()

        result_dicts = [dict(zip(column_names, row)) for row in rows]

        if result_dicts:
            df_usuarios = pd.DataFrame(result_dicts)
            df_usuarios['firstname'] = df_usuarios['firstname'].str.strip().apply(unidecode.unidecode).str.upper()
            df_usuarios['lastname'] = df_usuarios['lastname'].str.strip().apply(unidecode.unidecode).str.upper()
            ruta_archivo_csv = "temp_files/usuarios_completos.csv"
            df_usuarios.to_csv(ruta_archivo_csv, index=False)

            return JSONResponse({'message': 'Registros encontrados de todos los usuarios'})
        else:
            codigo = SIN_INFORMACION
            mensaje = HTTP_MESSAGES.get(codigo)
            raise HTTPException(codigo, mensaje)
