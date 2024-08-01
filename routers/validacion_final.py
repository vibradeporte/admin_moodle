from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import JSONResponse,PlainTextResponse
import pandas as pd
import numpy as np
import Levenshtein
from fuzzywuzzy import fuzz
import re
import unicodedata
import os
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
    return numero_str

def sonMuyParecidos(nombre1, nombre2, threshold=80):
    calculator = StringScoreCalculator()
    nombre1 = str(nombre1).strip()
    nombre2 = str(nombre2).strip()
    similarity = calculator.calculate_similarity_score(nombre1, nombre2)
    return similarity >= threshold

def buscarCedula(cedula, df):
    cedula = str(cedula)
    limiteInferior = 0
    limiteSuperior = len(df) - 1
    while limiteInferior <= limiteSuperior:
        filaUsuarioActual = (limiteInferior + limiteSuperior) // 2
        actual_cedula = str(df.iloc[filaUsuarioActual]['username'])  # Convertir a cadena de caracteres
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

def buscarPorNombresApellidosTelefono(nombre, apellido, telefono, bd_usuarios):
    for index, row in bd_usuarios.iterrows():
        if (sonMuyParecidos(row['firstname'], nombre) and
            sonMuyParecidos(row['lastname'], apellido) and
            sonMuyParecidos(row['phone1'], telefono)):
            return index
    return -1

def procesar_matriculas(estudiantes_matricular, BD_USUARIOS):
    estudiantes_matricular['Estado'] = ''
    
    for index, row in estudiantes_matricular.iterrows():
        # Extraer los datos del estudiante a matricular
        cedulaUsuarioAMatricular = row['username']
        strApellido = row['lastname']
        strNombre = row['firstname']
        correoUsuario = row['email']
        telefonoUsuario = row['phone1']
        
        # Buscar si la cédula del estudiante a matricular existe en la base de datos de usuarios
        filaUsuarioActual = buscarCedula(cedulaUsuarioAMatricular, BD_USUARIOS)
        
        if filaUsuarioActual != -1:
            # Si se encuentra un usuario con la misma cédula
            usuario_encontrado = BD_USUARIOS.iloc[filaUsuarioActual]
            
            # Verificar si el apellido y nombre son muy parecidos
            if sonMuyParecidos(strApellido, usuario_encontrado['lastname']):
                if sonMuyParecidos(strNombre, usuario_encontrado['firstname']):
                    # Si el apellido y nombre son muy similares, se acepta la matrícula
                    estudiantes_matricular.at[index, 'Estado'] = 'SI'
                else:
                    # Si el apellido es similar pero el nombre es diferente
                    datosCompletosUsuarioEnBd = f"Nombre: {usuario_encontrado['firstname']} Apellido: {usuario_encontrado['lastname']} Correo: {usuario_encontrado['email']} Cédula: {usuario_encontrado['username']}"
                    estudiantes_matricular.at[index, 'Estado'] = f"@ID: {datosCompletosUsuarioEnBd} [Apellido SIMILAR y nombre DIFERENTE]"
            else:
                # Si el apellido es diferente
                datosCompletosUsuarioEnBd = f"Nombre: {usuario_encontrado['firstname']} Apellido: {usuario_encontrado['lastname']} Correo: {usuario_encontrado['email']} Cédula: {usuario_encontrado['username']}"
                estudiantes_matricular.at[index, 'Estado'] = f"@ID: {datosCompletosUsuarioEnBd} [Apellido DIFERENTE]"
        else:
            # Si la cédula del estudiante a matricular no se encuentra en la base de datos
            
            # Buscar si hay usuarios con nombres y apellidos similares y mismo correo
            filaConNombresSimilares = buscarPorNombresApellidosCorreo(strNombre, strApellido, correoUsuario, BD_USUARIOS)
            
            if filaConNombresSimilares != -1:
                # Si se encuentra un usuario con nombres y apellidos muy similares y mismo correo
                usuario_encontrado = BD_USUARIOS.iloc[filaConNombresSimilares]
                
                # Si el correo es diferente, buscar por nombres, apellidos y teléfono muy similares
                filaConNombresApellidosTelefonoSimilares = buscarPorNombresApellidosTelefono(strNombre, strApellido, telefonoUsuario, BD_USUARIOS)
                
                if filaConNombresApellidosTelefonoSimilares != -1:
                    # Si se encuentra un usuario con nombres, apellidos y teléfono muy similares
                    usuario_encontrado = BD_USUARIOS.iloc[filaConNombresApellidosTelefonoSimilares]
                    datosCompletosUsuarioEnBd = f"Nombre: {usuario_encontrado['firstname']} Apellido: {usuario_encontrado['lastname']} Correo: {usuario_encontrado['email']} Cédula: {usuario_encontrado['username']} Teléfono: {usuario_encontrado['phone1']}"
                    estudiantes_matricular.at[index, 'Estado'] = f"@ID: {datosCompletosUsuarioEnBd} [Cédula DIFERENTE, nombres, apellidos y teléfono muy SIMILARES]"
                else:
                    # Si no se encuentra ningún usuario con nombres, apellidos y teléfono similares
                    estudiantes_matricular.at[index, 'Estado'] = 'NO está en la BD esa cédula'
            else:
                # Si no se encuentra ningún usuario con esa cédula ni con nombres y apellidos similares
                estudiantes_matricular.at[index, 'Estado'] = 'NO está en la BD esa cédula'
    
    return estudiantes_matricular

@validacion_final.post("/validacion_final/", tags=['Moodle'])
async def validate_students():
    validacion = 'temp_files/validacion_inicial.xlsx'
    matriculas_aceptadas = pd.read_excel(validacion)
    
    estudiantes_matricular = pd.DataFrame()
    estudiantes_matricular['username'] = matriculas_aceptadas['IDENTIFICACION']
    estudiantes_matricular['TIPO_IDENTIFICACION'] = matriculas_aceptadas['TIPO_IDENTIFICACION']
    estudiantes_matricular['email'] = matriculas_aceptadas['CORREO']
    estudiantes_matricular['firstname'] = matriculas_aceptadas['NOMBRES'].str.upper()
    estudiantes_matricular['lastname'] = matriculas_aceptadas['APELLIDOS'].str.upper()
    estudiantes_matricular['phone1'] = matriculas_aceptadas['Numero_Con_Prefijo'].apply(solo_numeros)
    estudiantes_matricular['city'] = matriculas_aceptadas['CIUDAD'].str.upper()
    estudiantes_matricular['country'] = matriculas_aceptadas['PAIS_DE_RESIDENCIA'].str.upper()
    estudiantes_matricular['address'] = matriculas_aceptadas.apply(lambda row: f"{row['TIPO_IDENTIFICACION']}{row['IDENTIFICACION']}", axis=1)
    estudiantes_matricular['description'] = matriculas_aceptadas['DESCRIPCIÓN']
    estudiantes_matricular['lastnamephonetic'] = matriculas_aceptadas['lastnamephonetic']
    estudiantes_matricular['EMPRESA'] = matriculas_aceptadas['EMPRESA']
    estudiantes_matricular['CORREO_SOLICITANTE'] = matriculas_aceptadas['CORREO_SOLICITANTE']
    estudiantes_matricular['NRO_SEMANAS_DE_MATRICULA'] = matriculas_aceptadas['NRO_SEMANAS_DE_MATRICULA']
    estudiantes_matricular['NOMBRE_CORTO_CURSO'] = matriculas_aceptadas['NOMBRE_CORTO_CURSO']
    estudiantes_matricular['NOMBRE_LARGO_CURSO'] = matriculas_aceptadas['NOMBRE_LARGO_CURSO']
    estudiantes_matricular['¿EL email es inválido?'] = matriculas_aceptadas['QUALITY']
    estudiantes_matricular['¿La cédula es inválida?'] = matriculas_aceptadas['cedula_es_invalida']
    estudiantes_matricular['¿Hay más de una solicitud de matrícula?'] = matriculas_aceptadas['Existen_Mas_Solicitudes_De_Matricula']
    estudiantes_matricular['¿El nombre es inválido?'] = matriculas_aceptadas['Nombre_Invalido']
    estudiantes_matricular['¿El apellido es inválido?'] = matriculas_aceptadas['Apellido_Invalido']
    estudiantes_matricular['¿Hay apellidos y nombres invertidos?'] = matriculas_aceptadas['estan_cruzados']
    estudiantes_matricular['¿El número de whatsapp es invalido?'] = matriculas_aceptadas['Numero_Wapp_Incorrecto']
    estudiantes_matricular['¿Hay nombres inválidos de cursos?'] = matriculas_aceptadas['nombre_De_Curso_Invalido']
    estudiantes_matricular['¿Tiene matrícula activa?'] = matriculas_aceptadas['Esta_activo_estudiante']
    estudiantes_matricular['Advertencia de curso culminado'] = matriculas_aceptadas['ADVERTENCIA_CURSO_CULMINADO']
    estudiantes_matricular['MOVIL'] = matriculas_aceptadas['NUMERO_MOVIL_WS_SIN_PAIS']

    
    BD_USUARIOS = pd.read_csv('temp_files/usuarios_completos.csv')
    BD_USUARIOS['username'] = BD_USUARIOS['username'].astype(str)
    estudiantes_matricular['username'] = estudiantes_matricular['username'].astype(str)
    BD_USUARIOS.sort_values('username', inplace=True)
    

    resultado = procesar_matriculas(estudiantes_matricular, BD_USUARIOS)
  


    otras_columnas_con_si = resultado.drop(columns=['Estado']).apply(lambda x: x == 'SI', axis=1)


    estudiantes_a_matricular = resultado[
    ((resultado['Estado'] == 'NO está en la BD esa cédula') | (resultado['Estado'] == 'SI')) &
    (~otras_columnas_con_si.any(axis=1)) & (resultado['ADVERTENCIA_CURSO_CULMINADO'] == 'NO')
    ]

    estudiantes_a_matricular.to_csv('temp_files/estudiantes_validados.csv', index=False)

    estudiantes_con_si_en_otras_columnas = resultado[otras_columnas_con_si.any(axis=1)]

    estudiantes_que_no_seran_matriculados = resultado[
    ((resultado['Estado'] != 'NO está en la BD esa cédula') &
     (resultado['Estado'] != 'SI')) |
    otras_columnas_con_si.any(axis=1) | (resultado['ADVERTENCIA_CURSO_CULMINADO'] != 'NO')
    ]

    estudiantes_que_no_seran_matriculados.to_excel('temp_files/estudiantes_invalidos.xlsx', index=False)


    inconsistencias = len(estudiantes_que_no_seran_matriculados)
    correctos = len(estudiantes_a_matricular)
    message = (
            f"Verificación de inconsistencias:\n"
            f"{correctos} Estudiantes correctos\n"
            f"{inconsistencias} Estudiantes con inconsistencias\n"
        )

    return PlainTextResponse(content=message)


