from return_codes import *
from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import quote_plus
from dotenv import load_dotenv
import os

identificacion_usuario = APIRouter()

load_dotenv()
usuario = os.getenv("USER_DB_UL_ADMIN")
contrasena = os.getenv("PASS_DB_UL_ADMIN")
host = os.getenv("HOST_DB_ADMIN")
nombre_base_datos = os.getenv("NAME_DB_UL_ADMIN")
contrasena_codificada = quote_plus(contrasena)

DATABASE_URL = f"mysql+mysqlconnector://{usuario}:{contrasena_codificada}@{host}/{nombre_base_datos}"
engine = create_engine(DATABASE_URL)

@identificacion_usuario.get("/user/{user_id}", tags=['Validacion_Identidad'])
def encontrar_usuario(user_id: int):
    query = text("""
    SELECT
    c.URL_MOODLE as URL_MOODLE,
    c.TOKEN_MOODLE as TOKEN_MOODLE,
    c.PREFIJO_TABLAS as PREFIJO_TABLAS,
    c.CADENA_CONEXION_BD as CADENA_CONEXION_BD,
    u.ID_USUARIO as ID_USUARIO,
    u.IDENTIFICACION as IDENTIFICACION,
    u.NOMBRE as NOMBRE,
    u.APELLIDO as APELLIDO,
    u.MOVIL as MOVIL,
    u.CORREO as CORREO,
    p.NOMBRE as NOMBRE_PERMISO
    FROM
        USUARIO AS u
    JOIN CLIENTE AS c ON u.FID_CLIENTE = c.ID_CLIENTE
    JOIN `PERMISO-USUARIO` AS pu ON u.ID_USUARIO = pu.FID_USUARIO
    JOIN PERMISO AS p ON p.ID_PERMISO = pu.FID_PERMISO
    WHERE
        u.IDENTIFICACION = :IDENTIFICACION;
    """)
    
    try:
        with engine.connect() as connection:
            result = connection.execute(query, {"IDENTIFICACION": user_id})
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
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))





