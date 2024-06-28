from fastapi import FastAPI, Depends, HTTPException, APIRouter, Request
from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.orm import sessionmaker, Session
from urllib.parse import quote_plus
import requests


usuario = "elasistenteia_aiaadmmoodle"
contrasena = "Un1vl3@rn1ngAdm0nM00dl3"
host = "cloud.univlearning.com"
nombre_base_datos = "elasistenteia_aiaadmmoodle"
contrasena_codificada = quote_plus(contrasena)

DATABASE_URL = f"mysql+mysqlconnector://{usuario}:{contrasena_codificada}@{host}/{nombre_base_datos}"


identificacion_usuario = APIRouter()


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
metadata = MetaData()
metadata.reflect(bind=engine)

usuario_table = metadata.tables.get('USUARIO')
cliente_table = metadata.tables.get('CLIENTE')
permiso_usuario_table = metadata.tables.get('PERMISO-USUARIO')


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@identificacion_usuario.get("/user/{user_id}", tags=['Validacion_Identidad'])
def read_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host
    logger.info(f"Request received from IP: {client_ip}")

    if usuario_table is None or cliente_table is None or permiso_usuario_table is None:
        raise HTTPException(status_code=500, detail="Database tables not found.")
    
    try:
        query = select(
            usuario_table.c.ID_USUARIO,
            usuario_table.c.IDENTIFICACION,
            usuario_table.c.MOVIL,
            usuario_table.c.CORREO,
            cliente_table.c.URL_MOODLE,
            cliente_table.c.TOKEN_MOODLE,
            cliente_table.c.CADENA_CONEXION_BD,
            permiso_usuario_table.c.FID_PERMISO.label('ID_PERMISO')
        ).select_from(
            usuario_table
            .join(cliente_table, usuario_table.c.FID_CLIENTE == cliente_table.c.ID_CLIENTE)
            .join(permiso_usuario_table, usuario_table.c.ID_USUARIO == permiso_usuario_table.c.FID_USUARIO)
        ).where(usuario_table.c.ID_USUARIO == user_id)

        result = db.execute(query).fetchone()

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





