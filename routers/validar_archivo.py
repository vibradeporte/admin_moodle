import os
import pandas as pd
import requests
from fastapi import HTTPException, APIRouter
from fastapi.responses import JSONResponse
from io import BytesIO
from pathlib import Path
import uuid

verificacion_inicial_archivo = APIRouter()

columnas_requeridas = [
    'IDENTIFICACION', 'TIPO_IDENTIFICACION', 'NOMBRES', 'APELLIDOS', 'CORREO',
    'PAIS_DEL_MOVIL', 'NUMERO_MOVIL_WS_SIN_PAIS', 'EMPRESA', 'DESCRIPCIÓN', 
    'PAIS_DE_RESIDENCIA', 'CIUDAD', 'CORREO_SOLICITANTE', 'NRO_SEMANAS_DE_MATRICULA',
    'NOMBRE_LARGO_CURSO', 'NOMBRE_CORTO_CURSO', 'FECHA_MENSAJE_BIENVENIDA', 'HORA_MENSAJE_BIENVENIDAS',
    'DIAS_INFORMADOS_AL_ESTUDIANTE'
]

def lanzar_excepcion_http(codigo_estado, detalle):
    raise HTTPException(status_code=codigo_estado, detail=detalle)

def descargar_archivo(ruta):
    try:
        response = requests.get(ruta)
        response.raise_for_status()  # Verifica si hubo algún error en la solicitud
        return BytesIO(response.content)
    except requests.exceptions.RequestException as e:
        lanzar_excepcion_http(404, f"No se pudo descargar el archivo: {str(e)}")

def leer_archivo_excel(contenido_archivo):
    try:
        df = pd.read_excel(contenido_archivo, sheet_name='ESTUDIANTES')
        return df
    except ValueError:
        lanzar_excepcion_http(422, "El archivo no contiene la hoja ESTUDIANTES.")

def validar_columnas(df):
    columnas_faltantes = [columna for columna in columnas_requeridas if columna not in df.columns]
    if columnas_faltantes:
        lanzar_excepcion_http(401, f"El archivo no contiene las siguientes columnas: {', '.join(columnas_faltantes)}")

def guardar_archivo_validado(df):
    ruta_archivo_validado = 'temp_files/' + 'validacion_inicial.xlsx'
    df.to_excel(ruta_archivo_validado, index=False)
    return ruta_archivo_validado

@verificacion_inicial_archivo.post("/Validar_archivo/", tags=['Validacion Archivo'])
def verificar_archivo(nombre_archivo: str):
    ruta = f'https://ulapi-production.up.railway.app/static/temp_files/{nombre_archivo}'
    
    # Verificar si el archivo tiene la extensión correcta
    if not ruta.endswith(('.xlsx', '.xls')):
        lanzar_excepcion_http(415, "El archivo no es un archivo Excel. Por favor, usa un archivo con extensión .xlsx o .xls.")
    
    # Descargar el archivo desde la URL
    contenido_archivo = descargar_archivo(ruta)
    
    # Leer el archivo Excel descargado usando pandas
    df = leer_archivo_excel(contenido_archivo)

    # Eliminar filas completamente vacías
    df = df.dropna(how='all', axis=0)

    # Verificar si el DataFrame está vacío
    if df.empty:
        lanzar_excepcion_http(204, "El archivo no contiene datos, todas las filas están en blanco.")

    print("Columnas del archivo cargado:", df.columns.tolist())

    # Verificar si faltan columnas requeridas
    validar_columnas(df)

    # Limpiar y formatear columnas necesarias
    df['CORREO_SOLICITANTE'] = df['CORREO_SOLICITANTE'].fillna('').str.lower()
    df['CORREO'] = df['CORREO'].fillna('').str.lower()

    # Guardar el archivo validado
    ruta_archivo_validado = guardar_archivo_validado(df)

    return JSONResponse(
        content={"message": "El archivo cumple con la estructura y tipo deseado.", "validated_file_path": str(ruta_archivo_validado)},
        status_code=200
    )
