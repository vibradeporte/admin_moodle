from fastapi import APIRouter, HTTPException
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict

Bienvenida_wapp_estudiantes_router = APIRouter()

@Bienvenida_wapp_estudiantes_router.post("/Estructura_Wapp_Bienvenida/", tags=['Whatsapp'])
async def csv_to_json() -> List[Dict]:
    # Diccionario para los nombres de los meses en español
    meses_espanol = {
        1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
        5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
        9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
    }
    
    # Leer y limpiar el archivo CSV
    df = pd.read_csv('temp_files/estudiantes_validados.csv')
    df = df.dropna(subset=['phone1']).query('phone1 != "" and phone1.str.lower() not in ["none", "null"]')

    # Convertir las columnas timestart y timeend a fechas
    df['timeend'] = pd.to_datetime(df['timeend'], unit='s')
    
    # Calcular el día anterior al timeend
    df['dia_anterior'] = df['timeend'] - timedelta(days=1)
    
    # Crear el formato de fecha en español para el día anterior
    df['timeend_str'] = df['dia_anterior'].apply(
        lambda x: f"{x.day} de {meses_espanol[x.month]} de {x.year} a las 11:59 PM hora colombiana"
    )

    # Procesar los datos para generar el JSON
    data = []
    for _, row in df.iterrows():
        parametros = [
            row['firstname'],
            row['NOMBRE_LARGO_CURSO'],
            row['timeend_str'],
            row['email'],
            "P@SsW0RD123", #va a cambiar cuando se agregue la columna contraseña de usuario
            "soporte123@soporte.com"
        ]
        item = {
            "numero": str(row['phone1']),
            "parametros": parametros
        }
        data.append(item)

    return data
