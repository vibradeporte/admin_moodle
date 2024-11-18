from fastapi import FastAPI, HTTPException, APIRouter, Depends
from sqlalchemy import create_engine, text
from jwt_manager import JWTBearer
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

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
poblar_tabla_detalle_matricula_router = APIRouter()

def estudiantes_no_matriculados():
    """
    Devuelve un DataFrame con los estudiantes que no se han matriculado con el debido formato para llenar la tabla detalle matricula
    """
    ruta_archivo_estudiantes_invalidos = 'temp_files/estudiantes_invalidos.xlsx'

    # Verificar si el archivo existe
    if not os.path.exists(ruta_archivo_estudiantes_invalidos):
        print(f"Archivo no encontrado: {ruta_archivo_estudiantes_invalidos}")
        return pd.DataFrame()

    # Leer el archivo Excel
    df_estudiantes_no_matriculados = pd.read_excel(ruta_archivo_estudiantes_invalidos)

    # Verificar si el DataFrame está vacío
    if df_estudiantes_no_matriculados.empty:
        print("El archivo Excel existe pero está vacío.")
        return pd.DataFrame()

    # Mantener solo las columnas de interés
    columnas_interes = ['username', 'TIPO_IDENTIFICACION', 'firstname', 'lastname', 'email',
                       'MOVIL', 'country', 'city', 'EMPRESA', 'CORREO_SOLICITANTE', 
                       'NOMBRE_CORTO_CURSO']

    # Eliminar filas donde todas las columnas de interés sean NaN
    df_estudiantes_no_matriculados.dropna(subset=columnas_interes, how='all', inplace=True)

    # Convertir todas las columnas a tipo str
    df_estudiantes_no_matriculados = df_estudiantes_no_matriculados.astype(str)

    # Reemplazar valores NaN por 'SIN DATOS'
    df_estudiantes_no_matriculados.fillna('SIN DATOS', inplace=True)
    df_estudiantes_no_matriculados.replace('nan', 'SIN DATOS', inplace=True)

    # Filtrar las columnas de interés
    df_estudiantes_no_matriculados = df_estudiantes_no_matriculados[columnas_interes]

    # Renombrar columnas
    df_estudiantes_no_matriculados = df_estudiantes_no_matriculados.rename(columns={
        'username': 'IDENTIFICACION',
        'firstname': 'NOMBRES',
        'lastname': 'APELLIDOS',
        'email': 'CORREO',
        'MOVIL': 'MOVIL',
        'country': 'PAIS_DEL_MOVIL',
        'city': 'CIUDAD'
    })

    # Agregar las columnas extra que necesita detalle matricula
    columnas_extra = pd.DataFrame({
        'RES_MATRICULA': ['NO MATRICULADO'] * len(df_estudiantes_no_matriculados),
        'RES_CORREO_BIENVENIDA': ['NO MATRICULADO'] * len(df_estudiantes_no_matriculados),
        'ESTADO_CORREO_BIENVENIDA': ['NO MATRICULADO'] * len(df_estudiantes_no_matriculados),
        'ID_CORREO_BIENVENIDA': ['NO MATRICULADO'] * len(df_estudiantes_no_matriculados),
        'RES_WS_BIENVENIDA': ['NO MATRICULADO'] * len(df_estudiantes_no_matriculados),
        'ESTADO_WS_BIENVENIDA': ['NO MATRICULADO'] * len(df_estudiantes_no_matriculados),
        'ID_WS_BIENVENIDA': ['NO MATRICULADO'] * len(df_estudiantes_no_matriculados),
        'FECHA_HORA_PROGRAMADA': [None] * len(df_estudiantes_no_matriculados),
        'NRO_DIAS_DE_MATRICULAS': [0] * len(df_estudiantes_no_matriculados)
    })

    df_estudiantes_no_matriculados = pd.concat([df_estudiantes_no_matriculados, columnas_extra], axis=1)

    return df_estudiantes_no_matriculados

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
    df_estudiantes_matriculados = pd.read_csv(ruta_archivo)
    
    # Verificar si el DataFrame está vacío
    if df_estudiantes_matriculados.empty:
        print("El archivo CSV existe pero está vacío.")
        return pd.DataFrame()

    # Si falta la columna NRO_DIAS_DE_MATRICULAS, agregarla
    if 'NRO_DIAS_DE_MATRICULAS' not in df_estudiantes_matriculados.columns:
        df_estudiantes_matriculados['NRO_DIAS_DE_MATRICULAS'] = 0

    # Mantener solo las columnas de interés
    columnas_interes = [
        'username', 'TIPO_IDENTIFICACION', 'firstname', 'lastname', 'email',
        'MOVIL', 'country', 'city', 'EMPRESA', 'CORREO_SOLICITANTE', 
        'NRO_DIAS_DE_MATRICULAS', 'NOMBRE_CORTO_CURSO','FECHA_HORA_ENVIO_BIENVENIDAS'
    ]
    
    # Verificar si las columnas de interés están en el DataFrame
    columnas_faltantes = [col for col in columnas_interes if col not in df_estudiantes_matriculados.columns]
    if columnas_faltantes:
        print(f"Faltan columnas en el DataFrame: {columnas_faltantes}")
        return pd.DataFrame()  # Retornar un DataFrame vacío si faltan columnas importantes
    
    # Filtrar las columnas de interés
    df_estudiantes_matriculados = df_estudiantes_matriculados[columnas_interes]
    
    # Verificar si después de filtrar hay datos
    if df_estudiantes_matriculados.empty:
        print("El DataFrame está vacío después de filtrar las columnas de interés.")
        return df_estudiantes_matriculados
    
    # Eliminar filas donde todas las columnas de interés sean NaN
    df_estudiantes_matriculados.dropna(subset=columnas_interes, how='all', inplace=True)
    
    # Convertir todas las columnas a tipo str antes de aplicar fillna
    df_estudiantes_matriculados = df_estudiantes_matriculados.astype(str)

    # Reemplazar valores NaN por 'SIN DATOS'
    df_estudiantes_matriculados.fillna('SIN DATOS', inplace=True)
    df_estudiantes_matriculados.replace('nan', 'SIN DATOS', inplace=True)

    # Renombrar columnas
    df_estudiantes_matriculados = df_estudiantes_matriculados.rename(columns={
        'username': 'IDENTIFICACION',
        'firstname': 'NOMBRES',
        'lastname': 'APELLIDOS',
        'email': 'CORREO',
        'MOVIL': 'MOVIL',
        'country': 'PAIS_DEL_MOVIL',
        'city': 'CIUDAD',
        'FECHA_HORA_ENVIO_BIENVENIDAS': 'FECHA_HORA_PROGRAMADA',
    })

    # Reemplazar los valores 'NaT' con una cadena vacía
    # Reemplaza 'SIN DATOS' por None en el DataFrame
    df_estudiantes_matriculados['FECHA_HORA_PROGRAMADA'] = df_estudiantes_matriculados['FECHA_HORA_PROGRAMADA'].replace('SIN DATOS', None)
    # Reemplaza todos los NaN en la columna con None
    df_estudiantes_matriculados['FECHA_HORA_PROGRAMADA'] = df_estudiantes_matriculados['FECHA_HORA_PROGRAMADA'].where(pd.notna(df_estudiantes_matriculados['FECHA_HORA_PROGRAMADA']), None)
     # Reemplazar los valores 'NaT' con una cadena vacía
    df_estudiantes_matriculados['FECHA_HORA_PROGRAMADA'] = df_estudiantes_matriculados['FECHA_HORA_PROGRAMADA'].replace('NaT', '')
    df_estudiantes_matriculados['FECHA_HORA_PROGRAMADA'] = df_estudiantes_matriculados['FECHA_HORA_PROGRAMADA'].replace('', None)
    # Agregar columna de estado de matricula
    df_estudiantes_matriculados['RES_MATRICULA'] = 'MATRICULADO'

    # Agregar columna de estado de correo de bienvenida
    df_estudiantes_matriculados['ESTADO_CORREO_BIENVENIDA'] = df_estudiantes_matriculados.apply(
        lambda row: 'PROGRAMADO' if row.get('FECHA_HORA_PROGRAMADA') != None  
        else 'NO ENVIADO' if row.get('CORREO') == 'NO CORREO' else 'ENVIADO',
        axis=1
    )

    df_estudiantes_matriculados['ESTADO_WS_BIENVENIDA'] = df_estudiantes_matriculados.apply(
        lambda row: 'PROGRAMADO' if row.get('FECHA_HORA_PROGRAMADA') != None
        else 'NO ENVIADO' if row.get('MOVIL') == 'SIN NUMERO DE WHATSAPP' else 'ENVIADO',
        axis=1
    )
    
    # Eliminar duplicados
    df_estudiantes_matriculados = df_estudiantes_matriculados.drop_duplicates(subset=['IDENTIFICACION', 'NOMBRE_CORTO_CURSO'])
    
    return df_estudiantes_matriculados


@poblar_tabla_detalle_matricula_router.post("/api2/poblar_tabla_detalle_matricula/{fid_matricula}", response_model=int, tags=['Base de Datos'], dependencies=[Depends(JWTBearer())])
def crear_registro_detalle_matricula(fid_matricula: int):
    # Obtener los datos de estudiantes matriculados y no matriculados
    """
    Crea un registro en la tabla DETALLE_MATRICULA con los datos de estudiantes matriculados y no matriculados.
    
    :param fid_matricula: ID de la matricula
    :return: El ID del registro insertado
    """
    estudiantes_matriculados_df = estudiantes_matriculados() 
    print(estudiantes_matriculados_df.columns)  # Función que obtiene estudiantes matriculados
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
