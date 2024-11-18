from fastapi import FastAPI, APIRouter, HTTPException,Depends
from fastapi.responses import JSONResponse
from jwt_manager import JWTBearer
import pandas as pd
import numpy as np
import re
import os
import math

validacion_final = APIRouter()

class StringScoreCalculator:
    def __init__(self):
        """
        Inicializa el objeto StringScoreCalculator.

        Crea un arreglo bidimensional de ceros de tama o 256x256, donde cada
        elemento en la posici n [i][j] representa la cantidad de veces que se
        observ  el bigrama formado por el byte i y el byte j en el conjunto de
        datos de entrenamiento.
        """
        self.bag = np.zeros((256, 256))

    def calculate_similarity_score(self, array1, array2):
        """Calcula la similitud entre dos strings.

        Si los strings no son de tipo str, devuelve 0.0.

        Convierte los strings a bytes y llama a _calculate_similarity_score
        para calcular la similitud.

        :param array1: primer string
        :param array2: segundo string
        :return: similitud entre los dos strings
        :rtype: float
        """
        if not isinstance(array1, str) or not isinstance(array2, str):
            return 0.0

        byte_array1 = array1.encode('utf-8')
        byte_array2 = array2.encode('utf-8')

        return self._calculate_similarity_score(byte_array1, byte_array2)

    def _calculate_similarity_score(self, byte_array1, byte_array2):
        """
        Calcula la similitud entre dos arrays de bytes.

        La similitud se calcula como la cardinalidad de la diferencia sim trica
        entre los bigramas de los dos arrays de bytes. Primero, se cuentan los
        bigramas en cada array y se almacenan en el arreglo self.bag. Luego, se
        resta la cantidad de bigramas en com n entre los dos arrays y se
        devuelve el resultado como un porcentaje.

        :param byte_array1: primer array de bytes
        :param byte_array2: segundo array de bytes
        :return: similitud entre los dos arrays de bytes
        :rtype: float
        """
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
    """
    Limpia un string de todos los caracteres que no sean n meros.

    :param numero: string a limpiar
    :return: string con solo n meros
    """
    if pd.isna(numero):
        return ''
    numero_str = str(numero)
    return re.sub(r'\D', '', numero_str)

def sonMuyParecidos(nombre1, nombre2, threshold=80):
    """
    Compara la similitud entre dos nombres y determina si son 
    suficientemente parecidos según un umbral dado.

    :param nombre1: Primer nombre a comparar
    :param nombre2: Segundo nombre a comparar
    :param threshold: Umbral de similitud mínimo para considerar 
                      que los nombres son parecidos (por defecto es 80)
    :return: True si la similitud es mayor o igual al umbral, de lo 
             contrario False
    """
    calculator = StringScoreCalculator()
    nombre1 = str(nombre1).strip()
    nombre2 = str(nombre2).strip()
    similarity = calculator.calculate_similarity_score(nombre1, nombre2)
    return similarity >= threshold

def buscarCedula(cedula, df):
    """
    Busca una c dula en un DataFrame ordenado por la columna 'username'.
    
    :param cedula: c dula a buscar
    :param df: DataFrame ordenado por la columna 'username'
    :return: la fila en la que se encuentra la c dula si se encuentra, -1 si no se encuentra
    """
    cedula = str(cedula)
    limiteInferior = 0
    limiteSuperior = len(df) - 1
    while limiteInferior <= limiteSuperior:
        filaUsuarioActual = (limiteInferior + limiteSuperior) // 2
        actual_cedula = str(df.iloc[filaUsuarioActual]['username'])
        if cedula == actual_cedula:
            return filaUsuarioActual
        elif cedula < actual_cedula:
            limiteSuperior = filaUsuarioActual - 1
        else:
            limiteInferior = filaUsuarioActual + 1
    return -1

def buscarPorNombresApellidosCorreo(nombre, apellido, correo, bd_usuarios):
    """
    Busca un usuario en un DataFrame de usuarios por su nombre, apellido y correo
    electr nico.

    :param nombre: nombre del usuario a buscar
    :param apellido: apellido del usuario a buscar
    :param correo: correo electr nico del usuario a buscar
    :param bd_usuarios: DataFrame de usuarios
    :return: la fila en la que se encuentra el usuario si se encuentra, -1 si no se encuentra
    """
    for index, row in bd_usuarios.iterrows():
        if (sonMuyParecidos(row['firstname'], nombre) and
            sonMuyParecidos(row['lastname'], apellido) and
            row['email'].lower() == correo.lower()):
            return index
    return -1

def buscarPorNombresApellidosTelefono(nombre, apellido, telefono, bd_usuarios):
    """
    Busca un usuario en un DataFrame de usuarios por su nombre, apellido y telfono.
    
    :param nombre: nombre del usuario a buscar
    :param apellido: apellido del usuario a buscar
    :param telefono: telfono del usuario a buscar
    :param bd_usuarios: DataFrame de usuarios
    :return: la fila en la que se encuentra el usuario si se encuentra, -1 si no se encuentra
    """
    for index, row in bd_usuarios.iterrows():
        if (sonMuyParecidos(row['firstname'], nombre) and
            sonMuyParecidos(row['lastname'], apellido) and
            sonMuyParecidos(row['phone1'], telefono)):
            return index
    return -1

def procesar_matriculas(estudiantes_matricular, BD_USUARIOS):
    """
    Procesa un DataFrame de estudiantes para determinar su estado de matriculación 
    en base a una base de datos de usuarios existente.

    El estado se asigna a cada estudiante en función de la similitud de sus datos 
    personales (nombre, apellido, correo, teléfono) con los datos en la base de 
    datos de usuarios. Los estados posibles incluyen 'Existe en la BD', 
    'Apellido SIMILAR y nombre DIFERENTE', 'Apellido DIFERENTE', y 
    'NO está en la BD esa cédula'.

    :param estudiantes_matricular: DataFrame con los datos de los estudiantes a 
                                   matricular, incluyendo las columnas 'username', 
                                   'lastname', 'firstname', 'email', y 'phone1'.
    :param BD_USUARIOS: DataFrame que representa la base de datos de usuarios 
                        existente, ordenado por la columna 'username'.
    :return: DataFrame actualizado con una columna 'Estado' que indica el estado 
             de matriculación de cada estudiante.
    """
    estudiantes_matricular['Estado'] = ''
    
    for index, row in estudiantes_matricular.iterrows():
        cedulaUsuarioAMatricular = row['username']
        strApellido = row['lastname']
        strNombre = row['firstname']
        correoUsuario = row['email']
        telefonoUsuario = row['phone1']
        
        filaUsuarioActual = buscarCedula(cedulaUsuarioAMatricular, BD_USUARIOS)
        
        if filaUsuarioActual != -1:
            usuario_encontrado = BD_USUARIOS.iloc[filaUsuarioActual]
            if sonMuyParecidos(strApellido, usuario_encontrado['lastname']):
                if sonMuyParecidos(strNombre, usuario_encontrado['firstname']):
                    estudiantes_matricular.at[index, 'Estado'] = 'Existe en la BD'
                else:
                    datosCompletosUsuarioEnBd = f"Nombre: {usuario_encontrado['firstname']} Apellido: {usuario_encontrado['lastname']} Correo: {usuario_encontrado['email']} Cédula: {usuario_encontrado['username']}"
                    estudiantes_matricular.at[index, 'Estado'] = f"@ID: {datosCompletosUsuarioEnBd} [Apellido SIMILAR y nombre DIFERENTE]"
            else:
                datosCompletosUsuarioEnBd = f"Nombre: {usuario_encontrado['firstname']} Apellido: {usuario_encontrado['lastname']} Correo: {usuario_encontrado['email']} Cédula: {usuario_encontrado['username']}"
                estudiantes_matricular.at[index, 'Estado'] = f"@ID: {datosCompletosUsuarioEnBd} [Apellido DIFERENTE]"
        else:
            filaConNombresSimilares = buscarPorNombresApellidosCorreo(strNombre, strApellido, correoUsuario, BD_USUARIOS)
            if filaConNombresSimilares != -1:
                usuario_encontrado = BD_USUARIOS.iloc[filaConNombresSimilares]
                filaConNombresApellidosTelefonoSimilares = buscarPorNombresApellidosTelefono(strNombre, strApellido, telefonoUsuario, BD_USUARIOS)
                
                if filaConNombresApellidosTelefonoSimilares != -1:
                    usuario_encontrado = BD_USUARIOS.iloc[filaConNombresApellidosTelefonoSimilares]
                    datosCompletosUsuarioEnBd = f"Nombre: {usuario_encontrado['firstname']} Apellido: {usuario_encontrado['lastname']} Correo: {usuario_encontrado['email']} Cédula: {usuario_encontrado['username']} Teléfono: {usuario_encontrado['phone1']}"
                    estudiantes_matricular.at[index, 'Estado'] = f"@ID: {datosCompletosUsuarioEnBd} [Cédula DIFERENTE, nombres, apellidos y teléfono muy SIMILARES]"
                else:
                    estudiantes_matricular.at[index, 'Estado'] = 'NO está en la BD esa cédula'
            else:
                estudiantes_matricular.at[index, 'Estado'] = 'NO está en la BD esa cédula'
    
    return estudiantes_matricular


@validacion_final.post("/api2/validacion_final/", tags=['Moodle'],dependencies=[Depends(JWTBearer())])
async def validate_students():
    """
    Valida los estudiantes que se van a matricular en el curso.
    Toma un archivo Excel con los estudiantes y sus datos,
    y verifica que no haya inconsistencias en los datos
    (como cédulas repetidas, correos inválidos, etc).
    Guarda los estudiantes que no presentan inconsistencias
    en un archivo Excel, y los que presentan inconsistencias
    en otro archivo Excel.
    Además, verifica que el curso no tenga inconsistencias
    en la información de bienvenida (como plantilla HTML
    inválida, ID de mensajes de bienvenida inválido, etc).
    Si el curso no cumple con los requisitos, se guardan
    los cursos que no cumplen con los requisitos en un
    archivo Excel.
    Devuelve un JSON con la cantidad de estudiantes correctos,
    la cantidad de estudiantes con inconsistencias y un mensaje
    que indica si el curso cumple con los requisitos o no.
    """
    try:
        validacion = 'temp_files/validacion_inicial.xlsx'
        matriculas_aceptadas = pd.read_excel(validacion)
        matriculas_aceptadas = matriculas_aceptadas.drop_duplicates()
        matriculas_aceptadas = matriculas_aceptadas.reset_index(drop=True)
        matriculas_aceptadas['IDENTIFICACION'] = matriculas_aceptadas['IDENTIFICACION'].apply(lambda x: str(x).replace('.0', '') if '.0' in str(x) else str(x))
        user_db_path = 'temp_files/usuarios_completos.csv'
        if not os.path.exists(user_db_path):
            empty_df = pd.DataFrame(columns=['username', 'firstname', 'lastname', 'email', 'phone1'])
            empty_df.to_csv(user_db_path, index=False)
        estudiantes_matricular = pd.DataFrame({
            'username': matriculas_aceptadas['IDENTIFICACION'].fillna('NO IDENTIFICACION').astype(str),
            'TIPO_IDENTIFICACION': matriculas_aceptadas['TIPO_IDENTIFICACION'].fillna('SIN TIPO DE IDENTIFICACION').astype(str),
            'email': matriculas_aceptadas['CORREO'].fillna('NO CORREO').astype(str),
            'firstname': matriculas_aceptadas['NOMBRES'].fillna('SIN NOMBRES').astype(str).str.upper(),
            'lastname': matriculas_aceptadas['APELLIDOS'].fillna('SIN APELLIDOS').astype(str).str.upper(),
            'timestart': matriculas_aceptadas['timestart'].fillna('SIN FECHA').astype(str),
            'timeend': matriculas_aceptadas['timeend'].fillna('SIN FECHA').astype(str),
            'PAIS_DEL_MOVIL': matriculas_aceptadas['PAIS_DEL_MOVIL'].fillna('SIN PAÍS').astype(str).str.upper(),
            'MOVIL': matriculas_aceptadas['NUMERO_MOVIL_WS_SIN_PAIS'].apply(lambda x: str(x).replace('.0', '') if '.0' in str(x) else str(x)),
            'phone1': matriculas_aceptadas['Numero_Con_Prefijo'].apply(solo_numeros).fillna(' '),
            'city': matriculas_aceptadas['CIUDAD'].fillna('SIN CIUDAD').astype(str).str.upper(),
            'country': matriculas_aceptadas['PAIS_DE_RESIDENCIA'].fillna('SIN PAÍS').astype(str).str.upper(),
            'address': matriculas_aceptadas.apply(lambda row: f"{row['TIPO_IDENTIFICACION']} {row['IDENTIFICACION']}" if pd.notna(row['TIPO_IDENTIFICACION']) and pd.notna(row['IDENTIFICACION']) else "SIN DIRECCIÓN", axis=1),
            'description': matriculas_aceptadas['DESCRIPCIÓN'].fillna(' '),
            'CourseId': matriculas_aceptadas['CourseId'].fillna(''),
            'CourseDaysDuration': matriculas_aceptadas['CourseDaysDuration'].fillna(''),
            'lastnamephonetic': matriculas_aceptadas['lastnamephonetic'].fillna(' '),
            'EMPRESA': matriculas_aceptadas['EMPRESA'].fillna('SIN EMPRESA').astype(str).str.upper(),
            'CORREO_SOLICITANTE': matriculas_aceptadas['CORREO_SOLICITANTE'].fillna(''),
            'NRO_DIAS_DE_MATRICULAS': matriculas_aceptadas['NRO_DIAS_DE_MATRICULAS'].fillna(''),
            'NRO_SEMANAS_DE_MATRICULA': matriculas_aceptadas['NRO_SEMANAS_DE_MATRICULA'].fillna(''),
            'NOMBRE_CORTO_CURSO': matriculas_aceptadas['NOMBRE_CORTO_CURSO'].fillna('SIN NOMBRE CORTO CURSO'),
            'NOMBRE_LARGO_CURSO': matriculas_aceptadas['NOMBRE_LARGO_CURSO'].fillna('SIN NOMBRE LARGO'),
            'FECHA_MENSAJE_BIENVENIDA': matriculas_aceptadas['FECHA_MENSAJE_BIENVENIDA'].fillna('SIN FECHA').astype(str),
            'HORA_MENSAJE_BIENVENIDAS': matriculas_aceptadas['HORA_MENSAJE_BIENVENIDAS'].fillna('SIN FECHA').astype(str),
            'FECHA_HORA_ENVIO_BIENVENIDAS':matriculas_aceptadas['FECHA_HORA_COMBINADA'].fillna('').astype(str),
            'DIAS_INFORMADOS_AL_ESTUDIANTE': matriculas_aceptadas['DIAS_INFORMADOS_AL_ESTUDIANTE'].fillna('SIN DIAS').astype(str),
            '¿El formato de la fecha de envio de mensajes de bienvenida es invalido?': matriculas_aceptadas['FECHA_INVALIDA'],
            '¿El formato de la hora de envio de mensajes de bienvenida es invalido?': matriculas_aceptadas['HORA_INVALIDA'],
            '¿Hace falta fecha u hora de envio de mensajes de bienvenida?': matriculas_aceptadas['FECHA_HORA_INCOMPLETA'],
            '¿El tiempo de matricula es invalido?': matriculas_aceptadas['El tiempo de matricula es invalido'],
            '¿Días informados a estudiante supera los días de matrícula?': matriculas_aceptadas['¿Dias informados a estudiante supero los días de matrícula?'],
            '¿EL email es inválido?': matriculas_aceptadas['¿EL email es inválido?'],
            '¿EL email solicitante es inválido?': matriculas_aceptadas['¿EL email solicitante es inválido?'],
            '¿La cédula es inválida?': matriculas_aceptadas['cedula_es_invalida'],
            '¿El tipo de identificación es incorrecto?': matriculas_aceptadas['¿El tipo de identificación es incorrecto?'],
            '¿Hay más de una solicitud de matrícula?': matriculas_aceptadas['Existen_Mas_Solicitudes_De_Matricula'],
            '¿El nombre es inválido?': matriculas_aceptadas['Nombre_Invalido'],
            '¿El apellido es inválido?': matriculas_aceptadas['Apellido_Invalido'],
            '¿Hay apellidos y nombres invertidos?': matriculas_aceptadas['estan_cruzados'],
            '¿El número de whatsapp es invalido?': matriculas_aceptadas['Numero_Wapp_Incorrecto'],
            '¿Hay nombres inválidos de cursos?': matriculas_aceptadas['nombre_De_Curso_Invalido'],
            '¿El curso está deshabilitado para matrículas?': matriculas_aceptadas['¿El curso está deshabilitado para matrículas?'],
            '¿La plantilla HTML de correos de bienvenida es INVALIDA?': matriculas_aceptadas['¿La plantilla HTML de correos de bienvenida es INVALIDA?'],
            '¿El ID de mensajes de bienvenida de Whatsapp es INVALIDO?': matriculas_aceptadas['¿El ID de mensajes de bienvenida de Whatsapp es INVALIDO?'],
            '¿El Curso NO contiene dias de duracion de matrícula?': matriculas_aceptadas['¿El Curso NO contiene dias de duracion de matrícula?'],
            '¿Tiene matrícula activa?': matriculas_aceptadas['Esta_activo_estudiante'],
            '¿El campo del pais esta vacío?': matriculas_aceptadas['El campo del pais esta vacío'],
            'Advertencia de curso culminado': matriculas_aceptadas['ADVERTENCIA_CURSO_CULMINADO']
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
        if os.path.exists(validacion):
            os.remove(validacion)
        estudiantes_que_no_seran_matriculados_correo = estudiantes_que_no_seran_matriculados.copy()
        estudiantes_que_no_seran_matriculados_correo = estudiantes_que_no_seran_matriculados_correo.drop(columns=['timestart', 'timeend', 'lastnamephonetic', 'CourseId', 
                      'CourseDaysDuration', 'address', 'NRO_DIAS_DE_MATRICULAS', 'phone1','FECHA_HORA_ENVIO_BIENVENIDAS'])
        estudiantes_que_no_seran_matriculados_correo = estudiantes_que_no_seran_matriculados_correo.rename(columns={
            'email': 'CORREO',
            'username': 'IDENTIFICACION',
            'firstname': 'NOMBRES',
            'lastname': 'APELLIDOS',
            'MOVIL': 'NUMERO_MOVIL_WS_SIN_PAIS',
            'city': 'CIUDAD',
            'country': 'PAIS_DE_RESIDENCIA',
            'ESTADO': 'ESTADO DEL USUARIO EN LA BASE DE DATOS',
            'description': 'DESCRIPCIÓN'
        })

        estudiantes_que_no_seran_matriculados_correo.to_excel('temp_files/estudiantes_invalidos_correo.xlsx', index=False)

        if (estudiantes_que_no_seran_matriculados_correo[['¿El curso está deshabilitado para matrículas?',
                                                        '¿La plantilla HTML de correos de bienvenida es INVALIDA?',
                                                        '¿El ID de mensajes de bienvenida de Whatsapp es INVALIDO?',
                                                        '¿El Curso NO contiene dias de duracion de matrícula?']] == "SI").any().any():
            # Si alguna columna contiene "SI", seleccionar las columnas y eliminar duplicados
            estudiantes_que_no_seran_matriculados_curso_no_cumple_requisitos = estudiantes_que_no_seran_matriculados_correo[
                ['NOMBRE_CORTO_CURSO', '¿El curso está deshabilitado para matrículas?',
                '¿La plantilla HTML de correos de bienvenida es INVALIDA?',
                '¿El ID de mensajes de bienvenida de Whatsapp es INVALIDO?',
                '¿El Curso NO contiene dias de duracion de matrícula?']
            ].drop_duplicates(subset='NOMBRE_CORTO_CURSO')
            
            # Guardar en un archivo Excel
            estudiantes_que_no_seran_matriculados_curso_no_cumple_requisitos = estudiantes_que_no_seran_matriculados_curso_no_cumple_requisitos[estudiantes_que_no_seran_matriculados_curso_no_cumple_requisitos['NOMBRE_CORTO_CURSO'] != 'SINNOMBRECORTOCURSO']
            estudiantes_que_no_seran_matriculados_curso_no_cumple_requisitos.to_excel('temp_files/curso_no_cumple_requisitos.xlsx', index=False)
            
            Curso_es_invalido = "Hay cursos que no cumplen con las validaciones para matricular estudiantes"
        else:
            Curso_es_invalido = "Los cursos cumplen con los requisitos para matricular estudiantes"

        inconsistencias = len(estudiantes_que_no_seran_matriculados)
        correctos = len(estudiantes_a_matricular)
        message = {
            "verificacion": "Verificación de inconsistencias",
            "estudiantes_correctos": correctos,
            "estudiantes_inconsistencias": inconsistencias,
            "cursos": Curso_es_invalido
        }

        
        return JSONResponse(content=message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
