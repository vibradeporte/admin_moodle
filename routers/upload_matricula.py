from fastapi import FastAPI, File, UploadFile,APIRouter
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

upload_file_matricula = APIRouter()

"""##CEDULA"""
def validacion_cedula(datos):
    datos['IDENTIFICACION'] = datos['IDENTIFICACION'].astype(str)
    datos['IDENTIFICACION'] = datos['IDENTIFICACION'].str.replace(r'\D', '', regex=True)
    datos['cedula_es_invalida'] = ""
    invalid_length_mask = (datos['IDENTIFICACION'].str.len() < 4) | (datos['IDENTIFICACION'].str.len() > 20)
    #match_mask = datos['cedula_solo_num'] != datos['cedula'].str.replace('.', '').str.replace(',', '')
    invalid_mask = invalid_length_mask #| match_mask

    datos.loc[invalid_mask, 'cedula_es_invalida'] = "SI"
    datos.loc[~invalid_mask, 'cedula_es_invalida'] = "NO"

    return datos
    
def cedula_repetida(row, datos):
    start_index = row.name + 1
    end_index = len(datos)
    dynamic_range = datos.loc[start_index:end_index, 'IDENTIFICACION']

    if row['IDENTIFICACION'] in dynamic_range.values:
        return "SI"
    else:
        return "NO"
    
def validar_Cedula(datos):
  resultados_1 =  validacion_cedula(datos)
  resultados_1['Existen_Mas_Solicitudes_De_Matricula'] = resultados_1.apply(lambda row: cedula_repetida(row,resultados_1), axis=1)
  return resultados_1

"""##NOMBRE Y APELLIDO"""

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

  eliminar = ['vector_nombres', 'primer_nombre',
  'pimer_nombre_es_apellido', 'segundo_nombre',
  'segundo_nombre_es_apellido', 'vector_apellidos', 'primer_apellido',
  'pimer_apellido_es_nombre', 'segundo_apellido',
  'segundo_apellido_es_nombre']
  datos.drop(columns = eliminar, inplace=True)
  return datos

"""##EMAIL"""

def limpiar_email(email):
    email = email.strip()
    email = email.replace('\t', '').replace('\xa0', '')
    email = ' '.join(email.split())
    email = email.lower()
    return email




def evaluar_validaciones(df_prueba):
  #Cedula
    df_prueba = validar_Cedula(df_prueba)

  #Nombre Y Apellidos
    df_prueba['Nombre_Invalido'] = df_prueba['NOMBRES'].apply(validar_nombre_apellido)
    df_prueba['Apellido_Invalido'] = df_prueba['APELLIDOS'].apply(validar_nombre_apellido)
    df_prueba = nuevo_estan_cruzados(df_prueba)

  #EMAIL
    df_prueba['CORREO'] = df_prueba['CORREO'].apply(limpiar_email)


  #EMPRESA

  #df_prueba = validar_cursos(df_prueba)

    return df_prueba

@upload_file_matricula.post("/uploadfile/", tags=['Moodle'])

def upload_file(file: UploadFile = File(...)):
    
    #Directorio para archivos temporales
    temp_dir = "temp_files"
    os.makedirs(temp_dir, exist_ok=True)
    #Leer archivo Excel
    df = pd.read_excel(file.file, engine = 'openpyxl')
    file.file.close()
    #Primera Validacion
    validated_df = evaluar_validaciones(df)
    correos_validar = validated_df['CORREO']
    si_rows_count = (validated_df == 'SI').any(axis=1).sum()
    total_rows = len(validated_df)
    matriculated_students = total_rows - si_rows_count
    #print("Estudiantes que serán Matriculados:", matriculated_students)
    #print("Estudiantes que NO serán Matriculados:", si_rows_count)
    correos_validar.to_csv('temp_files/correos_validar.csv',index = False,header = False)
    validated_df.to_excel('temp_files/validacion_inicial.xlsx',index = False)

    return {"filename": file.filename,"validation": "success","Número de Estudiantes que no seran aprobados": si_rows_count, "Estudiantes a matricular": matriculated_students}
    #return {"filename": file.filename, , "data": validated_df.to_dict(orient="records")}
