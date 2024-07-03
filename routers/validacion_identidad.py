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
            usuario.ID_USUARIO,
            usuario.IDENTIFICACION,
            usuario.NOMBRE,
            usuario.APELLIDO,
            usuario.MOVIL AS MOVIL_USUARIO,
            usuario.CORREO AS CORREO_USUARIO,
            cliente.NOMBRE AS NOMBRE_CLIENTE,
            cliente.CORREO_ADMON,
            cliente.CORREO_OPERACION,
            cliente.MOVIL AS MOVIL_CLIENTE,
            cliente.URL_MOODLE,
            cliente.TOKEN_MOODLE,
            cliente.CADENA_CONEXION_BD,
            `permiso_usuario`.FID_PERMISO AS ID_PERMISO,
            `permiso_usuario`.FECHA AS FECHA_PERMISO
        FROM 
            USUARIO AS usuario
        JOIN 
            CLIENTE AS cliente ON usuario.FID_CLIENTE = cliente.ID_CLIENTE
        JOIN 
            `permiso_usuario` AS PERMISO_USUARIO ON usuario.ID_USUARIO = PERMISO_USUARIO.FID_USUARIO
        WHERE 
            usuario.ID_USUARIO = :user_id;

""")
    
    try:
        with engine.connect() as connection:
            result = connection.execute(query, {"user_id": user_id})
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

app = FastAPI()
app.include_router(identificacion_usuario)



