import os
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from sqlalchemy import create_engine, text
from datetime import timedelta, datetime
from typing import List, Dict
from utils import meses_espanol, construir_url_mysql

Bienvenida_wapp_estudiantes_router = APIRouter()

# Diccionario con los meses en español
meses_espanol = {
    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
    5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
}

@Bienvenida_wapp_estudiantes_router.post("/Estructura_Wapp_Bienvenida/", tags=['Whatsapp'])
def csv_to_json() -> List[Dict]:
    # Leer y limpiar el archivo CSV
    df_estudiantes = pd.read_csv('temp_files/estudiantes_validados.csv', dtype={'phone1': str})
    df_estudiantes['phone1'] = df_estudiantes['phone1'].fillna('').astype(str)
    df_estudiantes['phone1'] = df_estudiantes['phone1'].str.replace('\.0$', '', regex=True)

    df_plantilla_wapp = pd.read_csv('temp_files/plantillas_wapp.csv', usecols=['NOMBRE_CORTO_CURSO', 'plantilla_whatsapp'])
    df = pd.merge(df_estudiantes, df_plantilla_wapp[['NOMBRE_CORTO_CURSO', 'plantilla_whatsapp']], on='NOMBRE_CORTO_CURSO', how='left')

    # Filtrar los registros con números de teléfono válidos
    df = df.dropna(subset=['phone1'])
    df = df[df['phone1'].apply(lambda x: str(x).isdigit() and x not in ["none", "null"])]
    df['FECHA_HORA_ENVIO_BIENVENIDAS'] = df['FECHA_HORA_ENVIO_BIENVENIDAS'].replace('NaT', np.nan)

    # Convertir los valores de 'FECHA_HORA_ENVIO_BIENVENIDAS' a datetime, errores se convierten en NaT
    df['FECHA_HORA_ENVIO_BIENVENIDAS'] = pd.to_datetime(df['FECHA_HORA_ENVIO_BIENVENIDAS'], errors='coerce')

    # Convertir toda la columna a cadenas (str), incluyendo los valores NaT
    df['FECHA_HORA_ENVIO_BIENVENIDAS'] = df['FECHA_HORA_ENVIO_BIENVENIDAS'].astype(str)

    # Reemplazar los valores 'NaT' con una cadena vacía
    df['FECHA_HORA_ENVIO_BIENVENIDAS'] = df['FECHA_HORA_ENVIO_BIENVENIDAS'].replace('NaT', '')
    df['FECHA_HORA_ENVIO_BIENVENIDAS'] = df['FECHA_HORA_ENVIO_BIENVENIDAS'].replace('', None)
    # Calcular timeend y dia_anterior
    def calcular_fechas(row):
        if pd.notna(row['DIAS_INFORMADOS_AL_ESTUDIANTE']) and row['DIAS_INFORMADOS_AL_ESTUDIANTE'] != 'SIN DIAS':
            dias_informados = int(float(row['DIAS_INFORMADOS_AL_ESTUDIANTE']))
            timeend = datetime.now() + timedelta(days=dias_informados)
            dia_anterior = timeend - timedelta(days=1)
        else:
            # Convertir timeend a datetime si es necesario
            timeend = pd.to_datetime(row['timeend'], unit='s', errors='coerce')
            dia_anterior = timeend - timedelta(days=1) if pd.notna(timeend) else None
        return pd.Series([timeend, dia_anterior])

    # Aplicar la función a todo el DataFrame
    df[['timeend', 'dia_anterior']] = df.apply(calcular_fechas, axis=1)

    # Crear el formato de fecha en español para el día anterior
    df['timeend_str'] = df['dia_anterior'].apply(
        lambda x: f"{x.day} de {meses_espanol[x.month]} de {x.year} a las 11:59 PM hora colombiana" if pd.notna(x) else "Fecha no disponible"
    )

    # Procesar los datos para generar el JSON
    data = []
    for _, row in df.iterrows():
        parametros = [
            row['firstname'],
            row['lastname'],
            row['NOMBRE_LARGO_CURSO'],
            row['timeend_str'],
            str(row['password']) if pd.notna(row['password']) else '' # Manejo de contraseñas faltantes
        ]
        item = {
            "numero": str(row['phone1']),
            "plantilla": row['plantilla_whatsapp'].strip() if pd.notna(row['plantilla_whatsapp']) else '',
            "parametros": parametros,
            "send_time": row['FECHA_HORA_ENVIO_BIENVENIDAS']
        }
        data.append(item)

    return data

