from fastapi import FastAPI, HTTPException, APIRouter,Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime
from urllib.parse import quote_plus
from jwt_manager import JWTBearer
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()
usuario = os.getenv("USER_DB_UL_ADMIN")
contrasena = os.getenv("PASS_DB_UL_ADMIN")
host = os.getenv("HOST_DB_ADMIN")
nombre_base_datos = os.getenv("NAME_DB_UL_ADMIN")
contrasena_codificada = quote_plus(contrasena)

DATABASE_URL = f"mysql+mysqlconnector://{usuario}:{contrasena_codificada}@{host}/{nombre_base_datos}"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

poblar_tabla_matricula_router = APIRouter()


@poblar_tabla_matricula_router.post("/poblar_tabla_matricula_router/{fid_usuario}", response_model=int,tags=['Base de Datos'],dependencies=[Depends(JWTBearer())])
def create_matricula(fid_usuario: int):

    data = {
        'FECHA_HORA': [datetime.now()],
        'FID_USUARIO': [fid_usuario]
    }
    df = pd.DataFrame(data)
    

    try:
        df.to_sql('MATRICULA', con=engine, if_exists='append', index=False)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al insertar los datos: {e}")
    

    with engine.connect() as connection:
        result = connection.execute(text("SELECT LAST_INSERT_ID()"))
        new_id = result.scalar()
    
    return new_id




