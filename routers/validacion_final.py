from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
import pandas as pd
import numpy as np
import re
import os
import math

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
    if pd.isna(numero) or str(numero).strip() == '':
        return 'SIN NUMERO'
    numero_str = str(numero)
    return re.sub(r'\D', '', numero_str)


def sonMuyParecidos(nombre1, nombre2, threshold=90):
    calculator = StringScoreCalculator()
    nombre1 = str(nombre1).strip().lower()
    nombre2 = str(nombre2).strip().lower()
    similarity = calculator.calculate_similarity_score(nombre1, nombre2)
    return similarity >= threshold

def buscarPorNombresApellidosCorreo(nombre, apellido, correo, bd_usuarios):
    for index, row in bd_usuarios.iterrows():
        if (sonMuyParecidos(row['firstname'], nombre) and
            sonMuyParecidos(row['lastname'], apellido) and
            sonMuyParecidos(row['email'], correo)):
            return index
    return -1


def buscarPorNombresApellidosTelefono(nombre, apellido, telefono, bd_usuarios):
    telefono = solo_numeros(telefono)  # Normalize phone number for comparison
    for index, row in bd_usuarios.iterrows():
        if (sonMuyParecidos(row['firstname'], nombre) and
            sonMuyParecidos(row['lastname'], apellido) and
            sonMuyParecidos(solo_numeros(row['phone1']), telefono)):
            return index
    return -1

def buscarCedula(cedula, bd_usuarios):
    try:
        return bd_usuarios[bd_usuarios['username'] == cedula].index[0]
    except IndexError:
        return -1


def procesar_matriculas(estudiantes_matricular, BD_USUARIOS):
    calculator = StringScoreCalculator()
    estudiantes_matricular['Estado'] = ''

    for index, row in estudiantes_matricular.iterrows():
        cedulaUsuarioAMatricular = row['username']
        strApellido = row['lastname'].strip().upper()
        strNombre = row['firstname'].strip().upper()
        correoUsuario = row['email'].strip().lower()
        telefonoUsuario = solo_numeros(row['phone1'])

        filaUsuarioActual = BD_USUARIOS[BD_USUARIOS['username'] == cedulaUsuarioAMatricular]
        
        if not filaUsuarioActual.empty:
            usuario_encontrado = filaUsuarioActual.iloc[0]
            apellido_similar = calculator.calculate_similarity_score(strApellido, usuario_encontrado['lastname'].strip().upper()) >= 90
            nombre_similar = calculator.calculate_similarity_score(strNombre, usuario_encontrado['firstname'].strip().upper()) >= 90
            correo_similar = calculator.calculate_similarity_score(correoUsuario, usuario_encontrado['email'].strip().lower()) >= 90
            telefono_similar = calculator.calculate_similarity_score(telefonoUsuario, solo_numeros(usuario_encontrado['phone1'])) >= 90

            if apellido_similar and nombre_similar:
                estudiantes_matricular.at[index, 'Estado'] = 'Existe en la BD'
            else:
                datosCompletosUsuarioEnBd = f"Nombre: {usuario_encontrado['firstname']} Apellido: {usuario_encontrado['lastname']} Correo: {usuario_encontrado['email']} Cédula: {usuario_encontrado['username']}"
                if apellido_similar and not nombre_similar:
                    estudiantes_matricular.at[index, 'Estado'] = f"@ID: {datosCompletosUsuarioEnBd} [Apellido SIMILAR y nombre DIFERENTE]"
                elif not apellido_similar:
                    estudiantes_matricular.at[index, 'Estado'] = f"@ID: {datosCompletosUsuarioEnBd} [Apellido DIFERENTE]"
        else:
            filaConNombresSimilares = BD_USUARIOS[
                BD_USUARIOS.apply(
                    lambda x: (
                        calculator.calculate_similarity_score(strNombre, x['firstname'].strip().upper()) >= 90 and
                        calculator.calculate_similarity_score(strApellido, x['lastname'].strip().upper()) >= 90
                    ), axis=1
                )
            ]

            if not filaConNombresSimilares.empty:
                filaConCorreoSimilar = filaConNombresSimilares[
                    filaConNombresSimilares.apply(
                        lambda x: calculator.calculate_similarity_score(correoUsuario, x['email'].strip().lower()) >= 90, axis=1
                    )
                ]
                filaConTelefonoSimilar = filaConNombresSimilares[
                    filaConNombresSimilares.apply(
                        lambda x: calculator.calculate_similarity_score(telefonoUsuario, solo_numeros(x['phone1'])) >= 90, axis=1
                    )
                ]

                if not filaConCorreoSimilar.empty:
                    usuario_encontrado = filaConCorreoSimilar.iloc[0]
                    datosCompletosUsuarioEnBd = f"Nombre: {usuario_encontrado['firstname']} Apellido: {usuario_encontrado['lastname']} Correo: {usuario_encontrado['email']} Cédula: {usuario_encontrado['username']} Teléfono: {usuario_encontrado['phone1']}"
                    estudiantes_matricular.at[index, 'Estado'] = f"@ID: {datosCompletosUsuarioEnBd} [Cédula DIFERENTE, nombres, apellidos y correo SIMILARES]"
                elif not filaConTelefonoSimilar.empty:
                    usuario_encontrado = filaConTelefonoSimilar.iloc[0]
                    datosCompletosUsuarioEnBd = f"Nombre: {usuario_encontrado['firstname']} Apellido: {usuario_encontrado['lastname']} Correo: {usuario_encontrado['email']} Cédula: {usuario_encontrado['username']} Teléfono: {usuario_encontrado['phone1']}"
                    estudiantes_matricular.at[index, 'Estado'] = f"@ID: {datosCompletosUsuarioEnBd} [Cédula DIFERENTE, nombres, apellidos y teléfono SIMILARES]"
                else:
                    estudiantes_matricular.at[index, 'Estado'] = 'NO está en la BD esa cédula'
            else:
                estudiantes_matricular.at[index, 'Estado'] = 'NO está en la BD esa cédula'
    
    return estudiantes_matricular

@validacion_final.post("/validacion_final/", tags=['Moodle'])
async def validate_students():
    try:
        validacion = 'temp_files/validacion_inicial.xlsx'
        matriculas_aceptadas = pd.read_excel(validacion)
        user_db_path = 'temp_files/usuarios_completos.csv'
        if not os.path.exists(user_db_path):
            empty_df = pd.DataFrame(columns=['username', 'firstname', 'lastname', 'email', 'phone1'])
            empty_df.to_csv(user_db_path, index=False)
        estudiantes_matricular = pd.DataFrame({
            'username': matriculas_aceptadas['IDENTIFICACION'].fillna('NO IDENTIFICACION'),
            'TIPO_IDENTIFICACION': matriculas_aceptadas['TIPO_IDENTIFICACION'].astype(str).fillna('SIN TIPO DE IDENTIFICACION'),
            'email': matriculas_aceptadas['CORREO'].astype(str).fillna('NO CORREO'),
            'firstname': matriculas_aceptadas['NOMBRES'].astype(str).str.upper().fillna('SIN NOMBRES'),
            'lastname': matriculas_aceptadas['APELLIDOS'].astype(str).str.upper().fillna('SIN APELLIDOS'),
            'phone1': matriculas_aceptadas['Numero_Con_Prefijo'].astype(str).apply(solo_numeros),
            'city': matriculas_aceptadas['CIUDAD'].astype(str).str.upper().fillna('SIN CIUDAD'),
            'country': matriculas_aceptadas['PAIS_DE_RESIDENCIA'].astype(str).str.upper().fillna('SIN PAÍS'),
            'address': matriculas_aceptadas.apply(lambda row: f"{row['TIPO_IDENTIFICACION']}{row['IDENTIFICACION']}", axis=1),
            'description': matriculas_aceptadas['DESCRIPCIÓN'],
            'lastnamephonetic': matriculas_aceptadas['lastnamephonetic'],
            'EMPRESA': matriculas_aceptadas['EMPRESA'].astype(str).fillna(' '),
            'CORREO_SOLICITANTE': matriculas_aceptadas['CORREO_SOLICITANTE'].astype(str).fillna(' '),
            'NRO_SEMANAS_DE_MATRICULA': matriculas_aceptadas['NRO_SEMANAS_DE_MATRICULA'],
            'NOMBRE_CORTO_CURSO': matriculas_aceptadas['NOMBRE_CORTO_CURSO'].astype(str).fillna('SIN NOMBRE CORTO CURSO'),
            'NOMBRE_LARGO_CURSO': matriculas_aceptadas['NOMBRE_LARGO_CURSO'].astype(str).fillna('SIN NOMBRE LARGO'),
            '¿EL email es inválido?': matriculas_aceptadas['¿EL email es inválido?'],
            '¿La cédula es inválida?': matriculas_aceptadas['cedula_es_invalida'],
            '¿Hay más de una solicitud de matrícula?': matriculas_aceptadas['Existen_Mas_Solicitudes_De_Matricula'],
            '¿El nombre es inválido?': matriculas_aceptadas['Nombre_Invalido'],
            '¿El apellido es inválido?': matriculas_aceptadas['Apellido_Invalido'],
            '¿Hay apellidos y nombres invertidos?': matriculas_aceptadas['estan_cruzados'],
            '¿El número de whatsapp es invalido?': matriculas_aceptadas['Numero_Wapp_Incorrecto'],
            '¿Hay nombres inválidos de cursos?': matriculas_aceptadas['nombre_De_Curso_Invalido'],
            '¿Tiene matrícula activa?': matriculas_aceptadas['Esta_activo_estudiante'],
            'Advertencia de curso culminado': matriculas_aceptadas['ADVERTENCIA_CURSO_CULMINADO'],
            'MOVIL': matriculas_aceptadas['NUMERO_MOVIL_WS_SIN_PAIS']
        })
        
        BD_USUARIOS = pd.read_csv('temp_files/usuarios_completos.csv')
        BD_USUARIOS['username'] = BD_USUARIOS['username'].astype(str)
        estudiantes_matricular['username'] = estudiantes_matricular['username'].astype(str)
        BD_USUARIOS.sort_values('username', inplace=True)
        
        resultado = procesar_matriculas(estudiantes_matricular, BD_USUARIOS)
        
        otras_columnas_con_si = resultado.drop(columns=['Estado']).apply(lambda x: x == 'SI', axis=1)

        estudiantes_a_matricular = resultado[
            ((resultado['Estado'] == 'NO está en la BD esa cédula') | (resultado['Estado'] == 'Existe en la BD')) &
            (~otras_columnas_con_si.any(axis=1)) & (resultado['Advertencia de curso culminado'] == 'NO')
        ]

        estudiantes_a_matricular.to_csv('temp_files/estudiantes_validados.csv', index=False)

        estudiantes_que_no_seran_matriculados = resultado[
            ((resultado['Estado'] != 'NO está en la BD esa cédula') &
            (resultado['Estado'] != 'Existe en la BD')) |
            otras_columnas_con_si.any(axis=1) | (resultado['Advertencia de curso culminado'] != 'NO')
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}") 

