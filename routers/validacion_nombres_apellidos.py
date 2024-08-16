from fastapi import FastAPI, File, UploadFile,APIRouter,HTTPException
from fastapi.responses import HTMLResponse,JSONResponse,PlainTextResponse
import pandas as pd
from io import StringIO ,BytesIO
import re
import time
import os
import json
import unidecode
import nltk
import requests
from nltk.tokenize import word_tokenize
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from collections import Counter
nltk.download('punkt')

validacion_nombres_apellidos_router = APIRouter()

def verificar_cruzados(row):
    columnas = [
        'pimer_nombre_es_apellido', 'segundo_nombre_es_apellido',
        'pimer_apellido_es_nombre', 'segundo_apellido_es_nombre'
    ]

    num_trues = sum(row[col] for col in columnas)
    if num_trues == 0:
        return 'NO'
    elif num_trues >= 3:
        return 'SI'
    else:
        return 'ES PROBABLE'

def validar_nombre_apellido(s):
    if not s:
        return "SI"
    if re.match("^[a-zA-ZáéíóúÁÉÍÓÚ ñÑ]*$", s):
        return "NO"
    else:
        return "SI"
    
def longitud_cadena(s):
    if len(s) > 3:
        return 'NO'
    else:
        return 'SI'

def encontrar_similitudes(primer_token, otros_nombres):
    return primer_token in otros_nombres

def nuevo_estan_cruzados(datos):
    fuente_de_busqueda = "routers/Nombres y apellidos.xlsx"
    df = pd.read_excel(fuente_de_busqueda)

    datos['NOMBRES'] = datos["NOMBRES"].str.strip().apply(unidecode.unidecode).str.upper()
    datos['vector_nombres'] = datos['NOMBRES'].apply(word_tokenize)
    datos['primer_nombre'] = datos['vector_nombres'].map(lambda x: x[0] if len(x) > 0 else None)
    datos['pimer_nombre_es_apellido'] = datos['primer_nombre'].apply(lambda x: encontrar_similitudes(x, df['Apellido'].tolist()))

    datos['segundo_nombre'] = datos['vector_nombres'].apply(lambda x: x[1] if len(x) >= 2 else None)
    datos['segundo_nombre_es_apellido'] = datos['segundo_nombre'].apply(lambda x: encontrar_similitudes(x, df['Apellido'].tolist()))

    datos['APELLIDOS'] = datos["APELLIDOS"].str.strip().apply(unidecode.unidecode).str.upper()
    datos['vector_apellidos'] = datos['APELLIDOS'].apply(word_tokenize)
    datos['primer_apellido'] = datos['vector_apellidos'].map(lambda x: x[0] if len(x) > 0 else None)
    datos['pimer_apellido_es_nombre'] = datos['primer_apellido'].apply(lambda x: encontrar_similitudes(x, df['Nombre'].tolist()))

    datos['segundo_apellido'] = datos['vector_apellidos'].apply(lambda x: x[1] if len(x) >= 2 else None)
    datos['segundo_apellido_es_nombre'] = datos['segundo_apellido'].apply(lambda x: encontrar_similitudes(x, df['Nombre'].tolist()))

    datos['estan_cruzados'] = datos.apply(verificar_cruzados, axis=1)

    eliminar = ['vector_nombres', 'primer_nombre', 'pimer_nombre_es_apellido', 'segundo_nombre', 'segundo_nombre_es_apellido', 'vector_apellidos', 'primer_apellido', 'pimer_apellido_es_nombre', 'segundo_apellido', 'segundo_apellido_es_nombre']
    datos.drop(columns=eliminar, inplace=True)
    return datos

@validacion_nombres_apellidos_router.post("/validar_nombres_apellidos/", tags=['Validacion_Inicial'])
async def validar_nombres_apellidos():
    try:
        file_path = 'temp_files/validacion_inicial.xlsx'

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"El archivo en la ruta '{file_path}' no fue encontrado.")

        df = pd.read_excel(file_path)

        df['Nombre_Invalido'] = df['NOMBRES'].apply(validar_nombre_apellido).apply(longitud_cadena)
        df['Apellido_Invalido'] = df['APELLIDOS'].apply(validar_nombre_apellido).apply(longitud_cadena)
        df = nuevo_estan_cruzados(df)
        df.to_excel(file_path, index=False)

        si_rows_count = ((df['Nombre_Invalido'] == 'SI') | (df['Apellido_Invalido'] == 'SI') | (df['estan_cruzados'] == 'SI')).sum()
        no_rows_count = ((df['Nombre_Invalido'] == 'NO') & (df['Apellido_Invalido'] == 'NO') & (df['estan_cruzados'] == 'NO')).sum()


        message = (
            f"Validación de nombres y apellidos: \n"
            f"{no_rows_count} Nombres Y Apellidos Correctos. \n"
            f"{si_rows_count} Nombres Y Apellidos Incorrectos. \n"
            
        )

        return PlainTextResponse(content=message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Un error occurrio: {e}")
