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
    """
    Devuelve un DataFrame con los estudiantes que se han matriculado con exito
    """
    if not os.path.exists('temp_files/estudiantes_validados.csv'):
        return pd.DataFrame()

    columns_to_read = ['username', 'TIPO_IDENTIFICACION', 'firstname', 'lastname', 'email',
                       'MOVIL', 'country', 'city', 'EMPRESA', 'CORREO_SOLICITANTE', 
                       'NRO_DIAS_DE_MATRICULAS', 'NOMBRE_CORTO_CURSO']

    df = pd.read_csv('temp_files/estudiantes_validados.csv', usecols=columns_to_read)
    df = df.dropna(how='all')

    if df.empty:
        return df

    df = df.rename(columns={
        'username': 'IDENTIFICACION',
        'firstname': 'NOMBRES',
        'lastname': 'APELLIDOS',
        'email': 'CORREO',
        'MOVIL': 'MOVIL',
        'country': 'PAIS_DEL_MOVIL',
        'city': 'CIUDAD'
    })

    if os.path.exists('temp_files/message_ids.csv'):
        df_message_correo = pd.read_csv('temp_files/message_ids.csv')
        df_message_correo = df_message_correo.rename(columns={'message_id': 'RES_CORREO_BIENVENIDA'})
        df = pd.concat([df, df_message_correo], axis=1)
    else:
        df['RES_CORREO_BIENVENIDA'] = 'NO ENVIADO AL CORREO'

    if os.path.exists('temp_files/message_status_wapp.csv'):
        df_wapp = pd.read_csv('temp_files/message_status_wapp.csv', usecols=['message_status'])
        df_wapp = df_wapp.rename(columns={'message_status': 'RES_WS_BIENVENIDA'})
        df = pd.concat([df, df_wapp], axis=1)
    else:
        df['RES_WS_BIENVENIDA'] = 'NO ENVIADO A WAPP'

    df['RES_MATRICULA'] = 'MATRICULADO'

    return df


def estudiantes_no_matriculados():
    """
    Devuelve un DataFrame con los estudiantes que no se han matriculado
    """
    invalid_students_file_path = 'temp_files/estudiantes_invalidos.xlsx'
    if not os.path.exists(invalid_students_file_path):
        return pd.DataFrame()

    columns_to_read = ['username', 'TIPO_IDENTIFICACION', 'firstname', 'lastname', 'email',
                       'MOVIL', 'country', 'city', 'EMPRESA', 'CORREO_SOLICITANTE', 
                       'NOMBRE_CORTO_CURSO']

    df = pd.read_excel(invalid_students_file_path, usecols=columns_to_read)
    if df.empty:
        return df

    df.dropna(inplace=True)
    df.fillna('SIN DATOS', inplace=True)

    df.rename(columns={'username': 'IDENTIFICACION', 'firstname': 'NOMBRES', 'lastname': 'APELLIDOS', 'email': 'CORREO',
                       'MOVIL': 'MOVIL', 'country': 'PAIS_DEL_MOVIL', 'city': 'CIUDAD'}, inplace=True)

    extra_columns = pd.DataFrame({
        'RES_MATRICULA': ['NO MATRICULADO'] * len(df),
        'RES_CORREO_BIENVENIDA': ['NO MATRICULADO'] * len(df),
        'RES_WS_BIENVENIDA': ['NO MATRICULADO'] * len(df),
        'NRO_DIAS_DE_MATRICULAS': [0] * len(df)
    })

    df = pd.concat([df, extra_columns], axis=1)

    return df


@poblar_tabla_detalle_matricula_router.post("/poblar_tabla_detalle_matricula/{fid_matricula}", response_model=int, tags=['Base de Datos'])
def create_matricula(fid_matricula: int):
    df_estudiantes_validos = estudiantes_matriculados()
    df_estudiantes_invalidos = estudiantes_no_matriculados()

    if df_estudiantes_validos is None and df_estudiantes_invalidos is None:
        raise HTTPException(status_code=400, detail="No hay datos para insertar")

    if df_estudiantes_validos is None:
        df = df_estudiantes_invalidos
    elif df_estudiantes_invalidos is None:
        df = df_estudiantes_validos
    else:
        df = pd.concat([df_estudiantes_validos, df_estudiantes_invalidos], ignore_index=True)


    if df is None:
        raise HTTPException(status_code=400, detail="No se puede concatenar los DataFrames")

    df['FID_MATRICULA'] = fid_matricula
    
    try:
        df.to_sql('DETALLE_MATRICULA', con=engine, if_exists='append', index=False)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al insertar los datos: {e}")

    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT LAST_INSERT_ID()"))
            new_id = result.scalar()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al obtener el ID del registro insertado: {e}")

    return new_id



