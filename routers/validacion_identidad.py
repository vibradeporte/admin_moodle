from return_codes import *
from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError, NoResultFound, OperationalError, ProgrammingError
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

def get_db():
    engine = create_engine(DATABASE_URL)
    try:
        yield engine
    finally:
        engine.dispose()

@identificacion_usuario.get("/user/{user_id}", tags=['Validacion_Usuario'])
def encontrar_usuario(user_id: int, db = Depends(get_db)):
    query = text("""
    SELECT
    c.URL_MOODLE as URL_MOODLE,
    c.TOKEN_MOODLE as TOKEN_MOODLE,
    c.PREFIJO_TABLAS as PREFIJO_TABLAS,
    c.MOTOR_BD as MOTOR_BD,
    c.SERVIDOR as SERVIDOR_BD,
    c.PUERTO as PUERTO_BD,
    c.USUARIO as USUARIO_BD,
    c.CONTRASENA as CONTRASENA_BD,
    c.NOMBRE_BD as NOMBRE_BD,
    u.ID_USUARIO as ID_USUARIO,
    u.NOMBRE as NOMBRE,
    u.APELLIDO as APELLIDO,
    u.MOVIL as MOVIL,
    u.CORREO as CORREO,
    cu.`FID_CASO_USO-CLIENTE` as ID_PERMISO
    FROM
        USUARIO AS u
    JOIN CLIENTE AS c ON u.FID_CLIENTE = c.ID_CLIENTE
    JOIN `CASO_USO-USUARIO` AS cu ON u.ID_USUARIO = cu.FID_USUARIO
    WHERE
        u.IDENTIFICACION = :IDENTIFICACION;
    """)
    

    with db.connect() as connection:
        result = connection.execute(query, {"IDENTIFICACION": user_id})
        rows = result.fetchall()
        column_names = result.keys()

        if not rows:
            mensaje = "No se encontró al usuario con esa identificación."
            return JSONResponse(content={"message": mensaje}, status_code=200)
            
        result_dicts = [dict(zip(column_names, row)) for row in rows]
        return JSONResponse(content=result_dicts)




