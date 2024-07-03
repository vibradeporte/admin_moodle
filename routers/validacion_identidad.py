from fastapi import FastAPI, Depends, HTTPException, APIRouter
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import quote_plus
from dotenv import load_dotenv
import os

load_dotenv()
usuario = os.getenv("USER_DB_UL_ADMIN")
contrasena = os.getenv("PASS_DB_UL_ADMIN")
host = os.getenv("HOST_DB_ADMIN")
nombre_base_datos = os.getenv("NAME_DB_UL_ADMIN")
contrasena_codificada = quote_plus(contrasena)

DATABASE_URL = f"mysql+mysqlconnector://{usuario}:{contrasena_codificada}@{host}/{nombre_base_datos}"
identificacion_usuario = APIRouter()
engine = create_engine(DATABASE_URL)

@identificacion_usuario.get("/user/{user_id}", tags=['Validacion_Identidad'])
def encontrar_usuario(user_id: int):
    query = text("""
        SELECT 
            usuario.ID_USUARIO,
            usuario.IDENTIFICACION,
            usuario.MOVIL,
            usuario.CORREO,
            cliente.URL_MOODLE,
            cliente.TOKEN_MOODLE,
            cliente.CADENA_CONEXION_BD,
            permiso_usuario.FID_PERMISO AS ID_PERMISO
        FROM 
            usuario
        JOIN 
            cliente ON usuario.FID_CLIENTE = cliente.ID_CLIENTE
        JOIN 
            permiso_usuario ON usuario.ID_USUARIO = permiso_usuario.FID_USUARIO
        WHERE 
            usuario.ID_USUARIO = :user_id
    """)

    try:
        with engine.connect() as connection:
            result = connection.execute(query, {'user_id': user_id}).fetchone()
            if result:
                user_data = {
                    "ID_USUARIO": result.ID_USUARIO,
                    "IDENTIFICACION": result.IDENTIFICACION,
                    "MOVIL": result.MOVIL,
                    "CORREO": result.CORREO,
                    "URL_MOODLE": result.URL_MOODLE,
                    "TOKEN_MOODLE": result.TOKEN_MOODLE,
                    "CADENA_CONEXION_BD": result.CADENA_CONEXION_BD,
                    "ID_PERMISO": result.ID_PERMISO
                }
                return user_data
            else:
                raise HTTPException(status_code=404, detail="Usuario No Encontrado")
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor: Error en la base de datos")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

app.include_router(identificacion_usuario)






