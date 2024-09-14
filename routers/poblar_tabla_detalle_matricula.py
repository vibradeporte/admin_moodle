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
    Devuelve un DataFrame con los estudiantes que se han matriculado con éxito, con todas las columnas convertidas a tipo str antes de aplicar fillna.
    """
    ruta_archivo = 'temp_files/estudiantes_validados.csv'
    
    # Verificar si el archivo existe
    if not os.path.exists(ruta_archivo):
        print(f"Archivo no encontrado: {ruta_archivo}")
        return pd.DataFrame()

    # Leer el archivo CSV
    df = pd.read_csv(ruta_archivo)
    
    # Verificar si el DataFrame está vacío
    if df.empty:
        print("El archivo CSV existe pero está vacío.")
        return pd.DataFrame()

    # Si falta la columna NRO_DIAS_DE_MATRICULAS, agregarla
    if 'NRO_DIAS_DE_MATRICULAS' not in df.columns:
        df['NRO_DIAS_DE_MATRICULAS'] = 0

    # Mantener solo las columnas de interés
    columnas_interes = ['username', 'TIPO_IDENTIFICACION', 'firstname', 'lastname', 'email',
                        'MOVIL', 'country', 'city', 'EMPRESA', 'CORREO_SOLICITANTE', 
                        'NRO_DIAS_DE_MATRICULAS', 'NOMBRE_CORTO_CURSO']
    
    # Verificar si las columnas de interés están en el DataFrame
    columnas_faltantes = [col for col in columnas_interes if col not in df.columns]
    if columnas_faltantes:
        print(f"Faltan columnas en el DataFrame: {columnas_faltantes}")
        return pd.DataFrame()  # Retornar un DataFrame vacío si faltan columnas importantes
    
    # Filtrar las columnas de interés
    df = df[columnas_interes]
    
    # Verificar si después de filtrar hay datos
    if df.empty:
        print("El DataFrame está vacío después de filtrar las columnas de interés.")
        return df
    
    # Eliminar filas donde todas las columnas de interés sean NaN
    df.dropna(subset=columnas_interes, how='all', inplace=True)
    
    # Convertir todas las columnas a tipo str antes de aplicar fillna
    df = df.astype(str)

    # Reemplazar valores NaN por 'SIN DATOS'
    df.fillna('SIN DATOS', inplace=True)
    df.replace('nan', 'SIN DATOS', inplace=True)
    # Renombrar columnas
    df = df.rename(columns={
        'username': 'IDENTIFICACION',
        'firstname': 'NOMBRES',
        'lastname': 'APELLIDOS',
        'email': 'CORREO',
        'MOVIL': 'MOVIL',
        'country': 'PAIS_DEL_MOVIL',
        'city': 'CIUDAD'
    })

    # Verificación de los mensajes de correo
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


    # Verificación de los mensajes de WhatsApp
    if os.path.exists('temp_files/message_status_wapp.csv'):
        # Leer el archivo CSV con solo las columnas necesarias
        df_mensajes_wapp = pd.read_csv('temp_files/message_status_wapp.csv', usecols=['message_status', 'numero'])

        # Renombrar las columnas
        df_mensajes_wapp = df_mensajes_wapp.rename(columns={'message_status': 'RES_WS_BIENVENIDA', 'numero': 'MOVIL'})

        # Asegurarse de que la columna 'MOVIL' esté en formato string
        df_mensajes_wapp['MOVIL'] = df_mensajes_wapp['MOVIL'].astype(str)

        # Eliminar los dos primeros caracteres de la columna 'MOVIL'
        df_mensajes_wapp['MOVIL'] = df_mensajes_wapp['MOVIL'].str.replace(r'^.{2}', '', regex=True)

        # Verificar si la columna 'MOVIL' existe en ambos DataFrames
        if 'MOVIL' in df.columns and 'MOVIL' in df_mensajes_wapp.columns:
            # Realizar la unión de los DataFrames basándote en la columna 'MOVIL'
            df = pd.merge(df, df_mensajes_wapp, on='MOVIL', how='left')
        else:
            print("Error: La columna 'MOVIL' no existe en ambos DataFrames.")
    else:
        df['RES_WS_BIENVENIDA'] = 'NO ENVIADO AL WHATSAPP'
    
    df['RES_MATRICULA'] = 'MATRICULADO'
    
    # Asegurarse de eliminar la columna 'id' si existe
    if 'id' in df.columns:
        df.drop(columns=['id'], inplace=True)

    df['RES_WS_BIENVENIDA'] = df['RES_WS_BIENVENIDA'].fillna('NO SE ENVIO EL MENSAJE A WHATSAPP')
    df = df.drop_duplicates(subset=['IDENTIFICACION', 'NOMBRE_CORTO_CURSO'])
    return df



def estudiantes_no_matriculados():
    """
    Devuelve un DataFrame con los estudiantes que no se han matriculado
    """
    invalid_students_file_path = 'temp_files/estudiantes_invalidos.xlsx'

    # Verificar si el archivo existe
    if not os.path.exists(invalid_students_file_path):
        print(f"Archivo no encontrado: {invalid_students_file_path}")
        return pd.DataFrame()

    # Leer el archivo Excel
    df = pd.read_excel(invalid_students_file_path)

    # Verificar si el DataFrame está vacío
    if df.empty:
        print("El archivo Excel existe pero está vacío.")
        return pd.DataFrame()

    # Mantener solo las columnas de interés
    columnas_interes = ['username', 'TIPO_IDENTIFICACION', 'firstname', 'lastname', 'email',
                       'MOVIL', 'country', 'city', 'EMPRESA', 'CORREO_SOLICITANTE', 
                       'NOMBRE_CORTO_CURSO']
    
    # Eliminar filas donde todas las columnas de interés sean NaN
    df.dropna(subset=columnas_interes, how='all', inplace=True)
    
    # Convertir todas las columnas a tipo str
    df = df.astype(str)

    # Reemplazar valores NaN por 'SIN DATOS'
    df.fillna('SIN DATOS', inplace=True)
    df.replace('nan', 'SIN DATOS', inplace=True)
    # Filtrar las columnas de interés
    df = df[columnas_interes]

    # Renombrar columnas
    df = df.rename(columns={
        'username': 'IDENTIFICACION',
        'firstname': 'NOMBRES',
        'lastname': 'APELLIDOS',
        'email': 'CORREO',
        'MOVIL': 'MOVIL',
        'country': 'PAIS_DEL_MOVIL',
        'city': 'CIUDAD'
    })

    # Agregar las columnas extra
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
    estudiantes_matriculados_df = estudiantes_matriculados() 
    print(estudiantes_matriculados_df) # Función que obtiene estudiantes matriculados
    estudiantes_no_matriculados_df = estudiantes_no_matriculados()  # Función que obtiene estudiantes no matriculados
    
    # Asegurarse de que ambas funciones devuelvan DataFrames y no None
    estudiantes_matriculados_df = estudiantes_matriculados_df if estudiantes_matriculados_df is not None else pd.DataFrame()
    estudiantes_no_matriculados_df = estudiantes_no_matriculados_df if estudiantes_no_matriculados_df is not None else pd.DataFrame()
    
    # Verificar si ambos DataFrames están vacíos
    if estudiantes_matriculados_df.empty and estudiantes_no_matriculados_df.empty:
        raise HTTPException(status_code=400, detail="No hay datos para insertar")
    
    # Concatenar ambos DataFrames si ambos tienen datos, o utilizar solo el que tenga datos
    if not estudiantes_matriculados_df.empty and not estudiantes_no_matriculados_df.empty:
        df = pd.concat([estudiantes_matriculados_df, estudiantes_no_matriculados_df], ignore_index=True)
    elif not estudiantes_matriculados_df.empty:  # Solo estudiantes matriculados tiene datos
        df = estudiantes_matriculados_df
    elif not estudiantes_no_matriculados_df.empty:  # Solo estudiantes no matriculados tiene datos
        df = estudiantes_no_matriculados_df
    
    # Agregar la columna 'FID_MATRICULA' a todos los registros
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