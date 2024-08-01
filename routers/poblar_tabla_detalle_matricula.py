from fastapi import FastAPI, HTTPException, APIRouter
from sqlalchemy import create_engine, text
import pandas as pd
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

engine = create_engine(DATABASE_URL)
poblar_tabla_detalle_matricula_router = APIRouter()

def estudiantes_matriculados():
    df = pd.read_csv('temp_files/estudiantes_validados.csv', usecols=['username', 'TIPO_IDENTIFICACION', 'firstname', 'lastname', 'email',
                                                                      'MOVIL', 'country', 'city', 'EMPRESA', 'CORREO_SOLICITANTE', 
                                                                      'NRO_DIAS_DE_MATRICULAS', 'NOMBRE_CORTO_CURSO'])
    
    df.rename(columns={'username': 'IDENTIFICACION', 'firstname': 'NOMBRES', 'lastname': 'APELLIDOS', 'email': 'CORREO',
                       'MOVIL': 'MOVIL', 'country': 'PAIS_DEL_MOVIL', 'city': 'CIUDAD'}, inplace=True)
    
    df_message_correo = pd.read_csv('temp_files/message_ids.csv')
    df_message_correo.rename(columns={'message_id': 'RES_CORREO_BIENVENIDA'}, inplace=True)
    
    df_wapp = pd.read_csv('temp_files/message_status_wapp.csv', usecols=['message_status'])
    df_wapp.rename(columns={'message_status': 'RES_WS_BIENVENIDA'}, inplace=True)
    
    df = pd.concat([df, df_message_correo, df_wapp], axis=1)
    
    df['RES_MATRICULA'] = 'MATRICULADO'
    
    return df

def estudiantes_no_matriculados():
    df = pd.read_excel('temp_files/estudiantes_invalidos.xlsx', usecols=['username', 'TIPO_IDENTIFICACION', 'firstname', 'lastname', 'email',
                                                                           'MOVIL', 'country', 'city', 'EMPRESA', 'CORREO_SOLICITANTE', 
                                                                           'NOMBRE_CORTO_CURSO'])
    
    df.rename(columns={'username': 'IDENTIFICACION', 'firstname': 'NOMBRES', 'lastname': 'APELLIDOS', 'email': 'CORREO',
                       'MOVIL': 'MOVIL', 'country': 'PAIS_DEL_MOVIL', 'city': 'CIUDAD'}, inplace=True)
    
    df_extra = pd.DataFrame({
    'RES_MATRICULA': ['NO MATRICULADO'] * len(df),
    'RES_CORREO_BIENVENIDA': ['NO MATRICULADO'] * len(df),
    'RES_WS_BIENVENIDA': ['NO MATRICULADO'] * len(df),
    'NRO_DIAS_DE_MATRICULAS': [0] * len(df)
    })

    df = pd.concat([df, df_extra], axis=1)
    
    return df

@poblar_tabla_detalle_matricula_router.post("/poblar_tabla_detalle_matricula/{fid_matricula}", response_model=int, tags=['Base de Datos'])
def create_matricula(fid_matricula: int):
    df_estudiantes_validos = estudiantes_matriculados()
    df_estudiantes_invalidos = estudiantes_no_matriculados()
    
    if df_estudiantes_validos.empty and df_estudiantes_invalidos.empty:
        raise HTTPException(status_code = 400, detail="No hay datos para insertar")

    if df_estudiantes_validos.empty:
        df = df_estudiantes_invalidos
    elif df_estudiantes_invalidos.empty:
        df = df_estudiantes_validos
    else:
        df = pd.concat([df_estudiantes_validos, df_estudiantes_invalidos], ignore_index=True)

    df['FID_MATRICULA'] = fid_matricula
    
    try:
        df.to_sql('DETALLE_MATRICULA', con=engine, if_exists='append', index=False)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al insertar los datos: {e}")

    with engine.connect() as connection:
        result = connection.execute(text("SELECT LAST_INSERT_ID()"))
        new_id = result.scalar()

    return new_id
