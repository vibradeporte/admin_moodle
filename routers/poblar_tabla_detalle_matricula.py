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
    Devuelve un DataFrame con los estudiantes que se han matriculado con éxito
    """
    ruta_archivo = 'temp_files/estudiantes_validados.csv'
    if not os.path.exists(ruta_archivo):
        df = pd.DataFrame()
        return df

    df = pd.read_csv(ruta_archivo)
    df = df.dropna(how='all')

    if df.empty:
        return df

    if 'NRO_DIAS_DE_MATRICULAS' not in df.columns:
        df['NRO_DIAS_DE_MATRICULAS'] = 0

    columnas_interes = ['username', 'TIPO_IDENTIFICACION', 'firstname', 'lastname', 'email',
                        'MOVIL', 'country', 'city', 'EMPRESA', 'CORREO_SOLICITANTE', 
                        'NRO_DIAS_DE_MATRICULAS', 'NOMBRE_CORTO_CURSO']
    df = df[columnas_interes]

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
        df_mensajes_correo = pd.read_csv('temp_files/message_ids.csv')
        df_mensajes_correo = df_mensajes_correo.rename(columns={'message_id': 'RES_CORREO_BIENVENIDA'})
        df = pd.concat([df, df_mensajes_correo], axis=1)
    else:
        df['RES_CORREO_BIENVENIDA'] = 'NO ENVIADO AL CORREO'

    if os.path.exists('temp_files/message_status_wapp.csv'):
        df_estado_wapp = pd.read_csv('temp_files/message_status_wapp.csv', usecols=['message_status'])
        df_estado_wapp = df_estado_wapp.rename(columns={'message_status': 'RES_WS_BIENVENIDA'})
        df = pd.concat([df, df_estado_wapp], axis=1)
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

    df = pd.read_excel(invalid_students_file_path)
    if df.empty:
        return df
    columnas_interes = ['username', 'TIPO_IDENTIFICACION', 'firstname', 'lastname', 'email',
                       'MOVIL', 'country', 'city', 'EMPRESA', 'CORREO_SOLICITANTE', 
                       'NOMBRE_CORTO_CURSO']

    df.dropna(inplace=True)
    df.fillna('SIN DATOS', inplace=True)
    df = df[columnas_interes]

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
    estudiantes_matriculados_df = estudiantes_matriculados()
    estudiantes_no_matriculados_df = estudiantes_no_matriculados()

    if estudiantes_matriculados_df.empty and estudiantes_no_matriculados_df.empty:
        raise HTTPException(status_code=400, detail="No hay datos para insertar")


    df = pd.concat([estudiantes_matriculados_df, estudiantes_no_matriculados_df], ignore_index=True)

    df['FID_MATRICULA'] = fid_matricula
    
    try:
        df.to_sql('DETALLE_MATRICULA', con=engine, if_exists='append', index=False)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al insertar los datos: {e}")

    with engine.connect() as connection:
        result = connection.execute(text("SELECT LAST_INSERT_ID()"))
        new_id = result.scalar()

    return new_id

