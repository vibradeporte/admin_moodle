from fastapi import FastAPI, APIRouter, HTTPException,Depends
from fastapi.responses import JSONResponse,PlainTextResponse
from jwt_manager import JWTBearer
import pandas as pd
import openpyxl
import os
import re

validacion_cedula_router = APIRouter()
os.makedirs('temp_files', exist_ok=True)


def verificar_tipo_identificacion(df: pd.DataFrame) -> pd.DataFrame:
    """
    Verifica si el tipo de identificación en la columna 'tipo_identificacion' 
    se encuentra en la lista de tipos permitidos, limpiando la columna.

    :param df: pd.DataFrame
    :return: pd.DataFrame
    """
    def limpiar_tipo_identificacion(tipo_identificacion):
        """
        Limpia el tipo de identificación quitando espacios y caracteres no alfabéticos,
        y quitando el punto al final si lo hay.

        :param tipo_identificacion: str
        :return: str o None
        """
        if not tipo_identificacion:
            return None

        tipo_identificacion = str(tipo_identificacion).strip().upper()
        tipo_identificacion = re.sub(r'[^a-zA-Z.]', '', tipo_identificacion)
        if tipo_identificacion.endswith('.'):
            tipo_identificacion = tipo_identificacion[:-1]
        return tipo_identificacion

    # Aplicar la función a la columna 'tipo_identificacion'
    df['TIPO_IDENTIFICACION'] = df['TIPO_IDENTIFICACION'].apply(limpiar_tipo_identificacion)
    
    return df

def validacion_tipo_identificacion(tipo_identificacion):
    """
    Verifica si el tipo de identificación se encuentra en la lista de tipos permitidos.

    :param tipo_identificacion: str
    :return: str
    """
    tipos_permitidos = {'C.C', 'C.E', 'C.I', 'CURP', 'DNI', 'DPI', 'ID', 'INE', 'PAS'}
    return "SI" if tipo_identificacion not in tipos_permitidos else "NO"

def validacion_cedula(datos):
    """
    Valida la cédula de los estudiantes en la columna 'IDENTIFICACION' en el DataFrame 'datos'.
    
    La validación consiste en verificar que la cédula tenga entre 4 y 20 caracteres y no contenga
    caracteres no numéricos.
    
    Agrega una columna 'cedula_es_invalida' al DataFrame con el resultado de la validación.
    
    :param datos: pd.DataFrame
    :return: pd.DataFrame
    """
    datos['IDENTIFICACION'] = datos['IDENTIFICACION'].astype(str)
    datos['IDENTIFICACION'] = datos['IDENTIFICACION'].str.replace(r'\D', '', regex=True)
    datos['cedula_es_invalida'] = ""
    invalid_length_mask = (datos['IDENTIFICACION'].str.len() < 4) | (datos['IDENTIFICACION'].str.len() > 20)
    invalid_mask = invalid_length_mask

    datos.loc[invalid_mask, 'cedula_es_invalida'] = "SI"
    datos.loc[~invalid_mask, 'cedula_es_invalida'] = "NO"

    return datos

def _tiene_registros_duplicados_con_mismo_curso(registros_con_misma_cedula, nombre_curso):
    """Verifica si hay registros duplicados con el mismo curso"""
    return len(registros_con_misma_cedula[registros_con_misma_cedula['NOMBRE_CORTO_CURSO'] == nombre_curso]) > 1


def _es_la_primera_entrada_del_curso(registros_con_misma_cedula, nombre_curso, indice_registro):
    """Verifica si el registro es la primera entrada del curso"""
    return indice_registro == registros_con_misma_cedula[registros_con_misma_cedula['NOMBRE_CORTO_CURSO'] == nombre_curso].index[0]


def _verificar_si_hay_duplicados_con_distintos_nombres_o_apellidos(registros_con_misma_cedula):
    """Verifica si los registros duplicados tienen nombres o apellidos diferentes"""
    return (registros_con_misma_cedula['NOMBRES'] != registros_con_misma_cedula.iloc[0]['NOMBRES']).any() or \
           (registros_con_misma_cedula['APELLIDOS'] != registros_con_misma_cedula.iloc[0]['APELLIDOS']).any()


def cedula_repetida(registro, datos):
    """Verifica si una cédula se ha repetido"""
    registros_con_misma_cedula = datos[datos['IDENTIFICACION'] == registro['IDENTIFICACION']]
    
    if len(registros_con_misma_cedula) > 1:
        # Verificar si hay registros duplicados exactos (mismo nombre y apellido)
        duplicados_exactos = registros_con_misma_cedula[
            (registros_con_misma_cedula['NOMBRES'] == registro['NOMBRES']) &
            (registros_con_misma_cedula['APELLIDOS'] == registro['APELLIDOS'])&
            (registros_con_misma_cedula['NOMBRE_CORTO_CURSO'] == registro['NOMBRE_CORTO_CURSO'])
        ]
        
        if len(duplicados_exactos) > 1:
            # Marcar todos como 'SI' excepto el último, que se marca como 'NO'
            if registro.name == duplicados_exactos.index[-1]:
                return "NO"
            else:
                return "SI"
        
        # Verificar si hay duplicados con diferentes nombres o apellidos
        if _verificar_si_hay_duplicados_con_distintos_nombres_o_apellidos(registros_con_misma_cedula):
            return "SI"
        
        # Verificar si hay duplicados en el mismo curso
        if _tiene_registros_duplicados_con_mismo_curso(registros_con_misma_cedula, registro['NOMBRE_CORTO_CURSO']):
            if registro['Existen_Mas_Solicitudes_De_Matricula'] == "SI":
                if _es_la_primera_entrada_del_curso(registros_con_misma_cedula, registro['NOMBRE_CORTO_CURSO'], registro.name):
                    return "SI"
                else:
                    return "NO"
    
    return "NO"






def validar_Cedula(datos):
    resultados_1 = validacion_cedula(datos)
    resultados_1['Existen_Mas_Solicitudes_De_Matricula'] = resultados_1.apply(lambda row: cedula_repetida(row, resultados_1), axis=1)
    return resultados_1



@validacion_cedula_router.post("/api2/validar_cedula/", tags=['Validacion_Inicial'],dependencies=[Depends(JWTBearer())])
async def validar_cedula():
    try:
        file_path = 'temp_files/validacion_inicial.xlsx'

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"El archivo en la ruta '{file_path}' no fue encontrado.")

        df = pd.read_excel(file_path)
        df['Existen_Mas_Solicitudes_De_Matricula'] = ''
        df = validar_Cedula(df)
        df = verificar_tipo_identificacion(df)
        df['¿El tipo de identificación es incorrecto?'] = df['TIPO_IDENTIFICACION'].apply(validacion_tipo_identificacion)
        df['IDENTIFICACION'] = df['IDENTIFICACION'].fillna('SIN IDENTIFICACIÓN')
        df.to_excel(file_path, index=False)

        si_rows_count_cedula = (df['cedula_es_invalida'] == 'SI').sum()
        no_rows_count_cedula = (df['cedula_es_invalida'] == 'NO').sum()


        si_rows_count_solicitudes = (df['Existen_Mas_Solicitudes_De_Matricula'] == 'SI').sum()
        no_rows_count_solicitudes = (df['Existen_Mas_Solicitudes_De_Matricula'] == 'NO').sum()


        message = {
        "validacion_cedulas": {
            "cedulas_correctas": int(no_rows_count_cedula),
            "cedulas_incorrectas": int(si_rows_count_cedula)
        },
        "validacion_solicitudes_matricula": {
            "solicitudes_correctas": int(no_rows_count_solicitudes),
            "solicitudes_incorrectas": int(si_rows_count_solicitudes)
        }
    }

        return JSONResponse(content=message)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



