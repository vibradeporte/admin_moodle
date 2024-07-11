from fastapi import APIRouter, HTTPException
import pandas as pd
import json
from typing import List, Dict


Bienvenida_wapp_estudiantes_router = APIRouter()

@Bienvenida_wapp_estudiantes_router.post("/csv_to_json",tags=['JSON'])
async def csv_to_json() -> List[Dict]:
    # Load the CSV file into a DataFrame
    df = pd.read_csv('temp_files/estudiantes_validados.csv')

    # Convert the 'timestart' and 'timeend' columns from Unix timestamp to date
    df['timestart'] = pd.to_datetime(df['timestart'], unit='s').dt.date
    df['timeend'] = pd.to_datetime(df['timeend'], unit='s').dt.date

    # Process the data
    data = []
    for _, row in df.iterrows():
        parametros = [
            row['firstname'],
            row['NOMBRE_LARGO_CURSO'],
            row['timestart'].strftime('%Y-%m-%d'),  # Date format
            row['timeend'].strftime('%Y-%m-%d'),    # Date format
            row['email'],
            "P@SsW0RD123",
            "soporte123@soporte.com"
        ]
        item = {
            "numero": str(row['phone1']),
            "parametros": parametros
        }
        data.append(item)

    return data