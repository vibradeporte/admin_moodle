from fastapi import FastAPI, APIRouter, HTTPException
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
import re
import unicodedata
from urllib.parse import quote_plus
import os
from dotenv import load_dotenv
import math
import unidecode


validacion_final = APIRouter()


class StringScoreCalculator:
    def __init__(self):
        self.bag = np.zeros((256, 256))

    def calculate_similarity_score(self, array1, array2):
        if not isinstance(array1, str) or not isinstance(array2, str):
            return 0.0

        byte_array1 = array1.encode('utf-8')
        byte_array2 = array2.encode('utf-8')

        return self._calculate_similarity_score(byte_array1, byte_array2)

    def _calculate_similarity_score(self, byte_array1, byte_array2):
        length1 = len(byte_array1)
        length2 = len(byte_array2)
        minLength = min(length1, length2)
        maxLength = max(length1, length2)

        if minLength == 0 or maxLength <= 1:
            return 0.0

        symmetricDifferenceCardinality = 0

        for i in range(1, length1):
            self.bag[byte_array1[i-1] & 0xFF][byte_array1[i] & 0xFF] += 1
            symmetricDifferenceCardinality += 1

        for j in range(1, length2):
            bigram_count = self.bag[byte_array2[j-1] & 0xFF][byte_array2[j] & 0xFF] - 1
            self.bag[byte_array2[j-1] & 0xFF][byte_array2[j] & 0xFF] = bigram_count

            if bigram_count >= 0:
                symmetricDifferenceCardinality -= 1
            else:
                symmetricDifferenceCardinality += 1

        for i in range(1, length1):
            self.bag[byte_array1[i-1] & 0xFF][byte_array1[i] & 0xFF] = 0
        for j in range(1, length2):
            self.bag[byte_array2[j-1] & 0xFF][byte_array2[j] & 0xFF] = 0

        rabbit_score = max(1.0 - math.pow(1.2 * symmetricDifferenceCardinality / maxLength, 5.0 / math.log10(maxLength + 1)), 0)
        return rabbit_score * 100

def solo_numeros(numero):
    if pd.isna(numero):
        return ''
    numero_str = str(numero)
    numero_str = re.sub(r'\D', '', numero_str)
    if numero_str == '':
        return ''
    return int(numero_str)

validacion = 'temp_files/validacion_inicial.xlsx'
prueba = pd.read_excel(validacion)
prueba['Hay_Datos_Invalidos'] = prueba.apply(lambda row: 'SI' in row.values, axis=1)
matriculas_aceptadas = prueba[~prueba['Hay_Datos_Invalidos']]
calculator = StringScoreCalculator()

# NORMALIZACION DE ESTUDIANTES A MATRICULAR
estudiantes_matricular = pd.DataFrame()
estudiantes_matricular['username'] = matriculas_aceptadas['IDENTIFICACION']
estudiantes_matricular['email'] = matriculas_aceptadas['CORREO']
estudiantes_matricular['firstname'] = matriculas_aceptadas['NOMBRES'].str.upper()
estudiantes_matricular['lastname'] = matriculas_aceptadas['APELLIDOS'].str.upper()
estudiantes_matricular['phone1'] = matriculas_aceptadas['NUMERO_MOVIL_WS_SIN_PAIS'].apply(solo_numeros)
estudiantes_matricular['city'] = matriculas_aceptadas['CIUDAD'].astype(str).str.upper().str.strip().apply(unidecode.unidecode)
estudiantes_matricular = estudiantes_matricular.astype(str)

# NUMERO DE MATRICULAS QUE SON VALIDAS
print(estudiantes_matricular.shape[0])

# BUSCAR CEDULA DE ESTUDIANTE NUEVO EN LA BASE DE DATOS DE TODOS LOS ESTUDIANTES
BD_USUARIOS = pd.read_csv('temp_files/BD_USUARIOS.csv')
BD_USUARIOS['username'] = BD_USUARIOS['username'].astype(str)
estudiantes_matricular['username'] = estudiantes_matricular['username'].astype(str)
BD_USUARIOS.sort_values('username', inplace=True)

def sonMuyParecidos(nombre1, nombre2, threshold=80):
    similarity = calculator.calculate_similarity_score(nombre1.strip(), nombre2.strip())
    return similarity >= threshold

def buscarCedula(cedula, df):
    limiteInferior = 0
    limiteSuperior = len(df) - 1
    while limiteInferior <= limiteSuperior:
        filaUsuarioActual = (limiteInferior + limiteSuperior) // 2
        actual_cedula = df.iloc[filaUsuarioActual]['username']
        if cedula == actual_cedula:
            return filaUsuarioActual
        elif cedula < actual_cedula:
            limiteSuperior = filaUsuarioActual - 1
        else:
            limiteInferior = filaUsuarioActual + 1
    return -1

def buscarPorNombresApellidosCorreo(nombre, apellido, correo, bd_usuarios):
    for index, row in bd_usuarios.iterrows():
        if (sonMuyParecidos(row['firstname'], nombre) and
            sonMuyParecidos(row['lastname'], apellido) and
            row['email'].lower() == correo.lower()):
            return index
    return -1

nombreColumnaQueRegistraSiElEstudEstaEnLaBD = 'Estado'
estudiantes_matricular[nombreColumnaQueRegistraSiElEstudEstaEnLaBD] = 'NO está en la BD esa cédula'

@validacion_final.post("/validacion_final/", tags=['Moodle'])
async def validate_students():
    for index, row in estudiantes_matricular.iterrows():
        cedulaUsuarioAMatricular = row['username']
        strApellido = row['lastname']
        strNombre = row['firstname']
        correoUsuario = row['email']
        filaUsuarioActual = buscarCedula(cedulaUsuarioAMatricular, BD_USUARIOS)

        if filaUsuarioActual != -1:
            usuario_encontrado = BD_USUARIOS.iloc[filaUsuarioActual]
            if sonMuyParecidos(strApellido, usuario_encontrado['lastname']):
                if sonMuyParecidos(strNombre, usuario_encontrado['firstname']):
                    if usuario_encontrado['email'].lower() == correoUsuario.lower():
                        estudiantes_matricular.at[index, nombreColumnaQueRegistraSiElEstudEstaEnLaBD] = 'SI'
                    else:
                        datosCompletosUsuarioEnBd = f"Nombre: {usuario_encontrado['firstname']} Apellido: {usuario_encontrado['lastname']} Correo: {usuario_encontrado['email']} Cédula: {usuario_encontrado['username']}"
                        estudiantes_matricular.at[index, nombreColumnaQueRegistraSiElEstudEstaEnLaBD] = f"@ID: {datosCompletosUsuarioEnBd} [Apellido y nombre SIMILARES, correo DIFERENTE]"
                else:
                    datosCompletosUsuarioEnBd = f"Nombre: {usuario_encontrado['firstname']} Apellido: {usuario_encontrado['lastname']} Correo: {usuario_encontrado['email']} Cédula: {usuario_encontrado['username']}"
                    estudiantes_matricular.at[index, nombreColumnaQueRegistraSiElEstudEstaEnLaBD] = f"@ID: {datosCompletosUsuarioEnBd} [Apellido SIMILAR y nombre DIFERENTE]"
            else:
                datosCompletosUsuarioEnBd = f"Nombre: {usuario_encontrado['firstname']} Apellido: {usuario_encontrado['lastname']} Correo: {usuario_encontrado['email']} Cédula: {usuario_encontrado['username']}"
                estudiantes_matricular.at[index, nombreColumnaQueRegistraSiElEstudEstaEnLaBD] = f"@ID: {datosCompletosUsuarioEnBd} [Apellido DIFERENTE]"
        else:
            estudiantes_matricular.at[index, nombreColumnaQueRegistraSiElEstudEstaEnLaBD] = 'NO está en la BD esa cédula'
    
    return estudiantes_matricular.to_dict(orient='records')



