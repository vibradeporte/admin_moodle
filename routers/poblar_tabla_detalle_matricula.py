from fastapi import FastAPI, HTTPException, APIRouter
from sqlalchemy import create_engine, text
import pandas as pd
from urllib.parse import quote_plus
from dotenv import load_dotenv
import os
import requests

load_dotenv()
usuario = os.getenv("USER_DB_UL_ADMIN")
contrasena = os.getenv("PASS_DB_UL_ADMIN")
host = os.getenv("HOST_DB_ADMIN")
nombre_base_datos = os.getenv("NAME_DB_UL_ADMIN")
contrasena_codificada = quote_plus(contrasena)
AUTH_KEY = os.getenv("AUTH_KEY")
API_URL_ANALYTICS = "https://pro.api.serversmtp.com/api/v2/analytics/{}"
AUTH_USER_TSMTP = os.getenv("AUTH_USER_TSMTP")
AUTH_PASS_TSMTP = os.getenv("AUTH_PASS_TSMTP")


DATABASE_URL = f"mysql+mysqlconnector://{usuario}:{contrasena_codificada}@{host}/{nombre_base_datos}"

engine = create_engine(DATABASE_URL)
poblar_tabla_detalle_matricula_router = APIRouter()

def estatus_envio_correo():
    df_mensajes_correo = pd.read_csv('temp_files/message_ids.csv')
    message_ids = df_mensajes_correo['message_id'].tolist()
    headers = {
        'Authorization': AUTH_KEY
    }

    analytics_data = []
    
    # Iterar sobre la lista de message_ids
    for message_id in message_ids:
        analytics_url = API_URL_ANALYTICS.format(message_id)
        
        try:
            # Realizar la solicitud a la API
            response = requests.get(analytics_url, headers=headers)
            response.raise_for_status()  # Esto levantará un error si el estatus no es 200
        except requests.exceptions.RequestException as e:
            print(f"Error fetching analytics for message_id {message_id}: {str(e)}")
            continue  # Saltar al siguiente ID si hay un error

        # Agregar los datos obtenidos de la API a la lista analytics_data
        analytics_data.append(response.json())

    # Si se obtuvieron datos, guardarlos en CSV
    if analytics_data:
        df = pd.DataFrame(analytics_data)
        df = df[['id','status']]
        return  df
    else:
        print("No se obtuvieron datos de analytics.")
        return []  # Retornar una lista vacía si no hay datos
    
def estudiantes_matriculados():
    """
    Devuelve un DataFrame con los estudiantes que se han matriculado con éxito
    """
    ruta_archivo = 'temp_files/estudiantes_validados.csv'
    if not os.path.exists(ruta_archivo):
        df = pd.DataFrame()
        return df

    df = pd.read_csv(ruta_archivo)

    if df.empty:
        return df

    if 'NRO_DIAS_DE_MATRICULAS' not in df.columns:
        df['NRO_DIAS_DE_MATRICULAS'] = 0

    columnas_interes = ['username', 'TIPO_IDENTIFICACION', 'firstname', 'lastname', 'email',
                        'MOVIL', 'country', 'city', 'EMPRESA', 'CORREO_SOLICITANTE', 
                        'NRO_DIAS_DE_MATRICULAS', 'NOMBRE_CORTO_CURSO']
    df = df[columnas_interes]
    df.dropna(subset=columnas_interes, how='all', inplace=True)
    df.fillna('SIN DATOS', inplace=True)
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
        df_mensajes_correo = estatus_envio_correo()

        # Si df_mensajes_correo es una lista, conviértela en DataFrame
        if isinstance(df_mensajes_correo, list):
            # Si es una lista de diccionarios o una lista con estructura tabular
            df_mensajes_correo = pd.DataFrame(df_mensajes_correo)

        # Ahora, renombra la columna si es un DataFrame
        if isinstance(df_mensajes_correo, pd.DataFrame):
            df_mensajes_correo = df_mensajes_correo.rename(columns={'status': 'RES_CORREO_BIENVENIDA'})
            df = pd.concat([df, df_mensajes_correo], axis=1)
        else:
            print("Error: No se pudo convertir en un DataFrame.")
    else:
        # En caso de que no exista el archivo o df_mensajes_correo no sea un DataFrame
        df['RES_CORREO_BIENVENIDA'] = 'NO ENVIADO AL CORREO'

        df['RES_MATRICULA'] = 'MATRICULADO'

        return df

def estudiantes_no_matriculados():
    """
    Devuelve un DataFrame con los estudiantes que no se han matriculado
    """
    invalid_students_file_path = 'temp_files/estudiantes_invalidos.xlsx'

    df = pd.read_excel(invalid_students_file_path)
    if df.empty:
        return df
    columnas_interes = ['username', 'TIPO_IDENTIFICACION', 'firstname', 'lastname', 'email',
                       'MOVIL', 'country', 'city', 'EMPRESA', 'CORREO_SOLICITANTE', 
                       'NOMBRE_CORTO_CURSO']
    
    df.dropna(subset=columnas_interes, how='all', inplace=True)
    df.fillna('SIN DATOS', inplace=True)
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
    # Obtener los datos de estudiantes matriculados y no matriculados
    estudiantes_matriculados_df = estudiantes_matriculados()  # Función que obtiene estudiantes matriculados
    estudiantes_no_matriculados_df = estudiantes_no_matriculados()  # Función que obtiene estudiantes no matriculados
    
    # Asegurarse de que ambas funciones devuelvan DataFrames y no None
    if estudiantes_matriculados_df is None:
        estudiantes_matriculados_df = pd.DataFrame()
    if estudiantes_no_matriculados_df is None:
        estudiantes_no_matriculados_df = pd.DataFrame()
    
    # Verificar si ambos DataFrames están vacíos
    if estudiantes_matriculados_df.empty and estudiantes_no_matriculados_df.empty:
        raise HTTPException(status_code=400, detail="No hay datos para insertar")

    # Concatenar solo si ambos DataFrames no están vacíos
    if not estudiantes_matriculados_df.empty and not estudiantes_no_matriculados_df.empty:
        df = pd.concat([estudiantes_matriculados_df, estudiantes_no_matriculados_df], ignore_index=False)
    elif not estudiantes_matriculados_df.empty:  # Solo hay datos de estudiantes matriculados
        df = estudiantes_matriculados_df
    elif not estudiantes_no_matriculados_df.empty:  # Solo hay datos de estudiantes no matriculados
        df = estudiantes_no_matriculados_df
    
    # Agregar la columna 'FID_MATRICULA'
    df['FID_MATRICULA'] = fid_matricula

    try:
        # Intentar insertar los datos en la tabla 'DETALLE_MATRICULA'
        df.to_sql('DETALLE_MATRICULA', con=engine, if_exists='append', index=False)
    except Exception as e:
        # En caso de error, lanzar una excepción con detalles
        raise HTTPException(status_code=400, detail=f"Error al insertar los datos: {e}")

    # Obtener el ID insertado más recientemente
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT LAST_INSERT_ID()"))  # Ajusta según la base de datos
            new_id = result.scalar()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el último ID insertado: {e}")

    return new_id