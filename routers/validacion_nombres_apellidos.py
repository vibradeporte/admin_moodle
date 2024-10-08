from fastapi import FastAPI, File, UploadFile, APIRouter, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
from io import BytesIO
import regex as re
import unidecode
import nltk
from nltk.tokenize import word_tokenize
import os
nltk.download('punkt')

validacion_nombres_apellidos_router = APIRouter()

def verificar_cruzados(row):
    columnas = [
        'pimer_nombre_es_apellido', 'segundo_nombre_es_apellido',
        'primer_apellido_es_nombre', 'segundo_apellido_es_nombre'
    ]

    num_trues = sum(row[col] for col in columnas)
    if num_trues == 0:
        return 'NO'
    elif num_trues >= 3:
        return 'SI'
    else:
        return 'SI'

def validar_nombre_apellido(s):
    # Verificar si la cadena es vacía o solo contiene espacios
    if not s or not s.strip():
        return "SI"
    
    # Verificar si la longitud es menor a 3
    if len(s) < 3:
        return "SI"
    
    # Verificar si la cadena es 'NAN'
    if s.upper() == 'NAN':
        return "SI"
    
    # Verificar si contiene caracteres no permitidos (solo letras y espacios, incluyendo acentos)
    if not re.match(r"^[\p{L}\s]+$", s):
        return "SI"
    
    return "NO"

def encontrar_similitudes(token, lista):
    return token in lista

def nuevo_estan_cruzados(datos):
    fuente_de_busqueda = "routers/Nombres y apellidos.xlsx"
    df = pd.read_excel(fuente_de_busqueda)

    # Normalize names and surnames
    datos['NOMBRES'] = datos["NOMBRES"].str.strip().apply(unidecode.unidecode).str.upper()
    datos['vector_nombres'] = datos['NOMBRES'].apply(word_tokenize)
    datos['primer_nombre'] = datos['vector_nombres'].map(lambda x: x[0] if len(x) > 0 else None)
    datos['pimer_nombre_es_apellido'] = datos['primer_nombre'].apply(lambda x: encontrar_similitudes(x, df['Apellido'].tolist()))

    datos['segundo_nombre'] = datos['vector_nombres'].apply(lambda x: x[1] if len(x) >= 2 else None)
    datos['segundo_nombre_es_apellido'] = datos['segundo_nombre'].apply(lambda x: encontrar_similitudes(x, df['Apellido'].tolist()))

    datos['APELLIDOS'] = datos["APELLIDOS"].str.strip().apply(unidecode.unidecode).str.upper()
    datos['vector_apellidos'] = datos['APELLIDOS'].apply(word_tokenize)
    datos['primer_apellido'] = datos['vector_apellidos'].map(lambda x: x[0] if len(x) > 0 else None)
    datos['primer_apellido_es_nombre'] = datos['primer_apellido'].apply(lambda x: encontrar_similitudes(x, df['Nombre'].tolist()))

    datos['segundo_apellido'] = datos['vector_apellidos'].apply(lambda x: x[1] if len(x) >= 2 else None)
    datos['segundo_apellido_es_nombre'] = datos['segundo_apellido'].apply(lambda x: encontrar_similitudes(x, df['Nombre'].tolist()))

    # Evaluate cross-checking results
    datos['estan_cruzados'] = datos.apply(verificar_cruzados, axis=1)

    # Drop unnecessary columns
    eliminar = ['vector_nombres', 'primer_nombre', 'pimer_nombre_es_apellido', 'segundo_nombre',
                'segundo_nombre_es_apellido', 'vector_apellidos', 'primer_apellido', 
                'primer_apellido_es_nombre', 'segundo_apellido', 'segundo_apellido_es_nombre']
    datos.drop(columns=eliminar, inplace=True)
    return datos

@validacion_nombres_apellidos_router.post("/validar_nombres_apellidos/", tags=['Validacion_Inicial'])
async def validar_nombres_apellidos():
    try:
        file_path = 'temp_files/validacion_inicial.xlsx'

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"El archivo en la ruta '{file_path}' no fue encontrado.")

        df = pd.read_excel(file_path)
        df['NOMBRES'] = df['NOMBRES'].astype(str)
        df['APELLIDOS'] = df['APELLIDOS'].astype(str)
        df['Nombre_Invalido'] = df['NOMBRES'].apply(validar_nombre_apellido)
        df['Apellido_Invalido'] = df['APELLIDOS'].apply(validar_nombre_apellido)
        df = nuevo_estan_cruzados(df)
        df['NOMBRES'] = df['NOMBRES'].replace('NAN', 'SIN NOMBRES')
        df['APELLIDOS'] = df['APELLIDOS'].replace('NAN', 'SIN APELLIDOS')
        df.to_excel(file_path, index=False)

        si_rows_count = ((df['Nombre_Invalido'] == 'SI') | (df['Apellido_Invalido'] == 'SI') | (df['estan_cruzados'] == 'SI')).sum()
        no_rows_count = ((df['Nombre_Invalido'] == 'NO') & (df['Apellido_Invalido'] == 'NO') & (df['estan_cruzados'] == 'NO')).sum()

        response_data = {
        "validacion_nombres_apellidos": {
            "correctos": int(no_rows_count),
            "incorrectos": int(si_rows_count)
        }
        }
    
    # Devuelve la respuesta en formato JSON
        return JSONResponse(content=response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Un error ocurrió: {str(e)}")
