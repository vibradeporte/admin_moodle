from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import JSONResponse,PlainTextResponse
import pandas as pd
import openpyxl
import os

validacion_cedula_router = APIRouter()
os.makedirs('temp_files', exist_ok=True)

def validacion_cedula(datos):
    datos['IDENTIFICACION'] = datos['IDENTIFICACION'].astype(str)
    datos['IDENTIFICACION'] = datos['IDENTIFICACION'].str.replace(r'\D', '', regex=True)
    datos['cedula_es_invalida'] = ""
    invalid_length_mask = (datos['IDENTIFICACION'].str.len() < 4) | (datos['IDENTIFICACION'].str.len() > 20)
    invalid_mask = invalid_length_mask

    datos.loc[invalid_mask, 'cedula_es_invalida'] = "SI"
    datos.loc[~invalid_mask, 'cedula_es_invalida'] = "NO"

    return datos

def cedula_repetida(row, datos):
    start_index = row.name + 1
    end_index = len(datos)
    dynamic_range = datos.loc[start_index:end_index, ['IDENTIFICACION', 'NOMBRE_CORTO_CURSO']]

    if ((dynamic_range['IDENTIFICACION'] == row['IDENTIFICACION']) &
        (dynamic_range['NOMBRE_CORTO_CURSO'] == row['NOMBRE_CORTO_CURSO'])).any():
        return "SI"
    else:
        return "NO"


def validar_Cedula(datos):
    resultados_1 = validacion_cedula(datos)
    resultados_1['Existen_Mas_Solicitudes_De_Matricula'] = resultados_1.apply(lambda row: cedula_repetida(row, resultados_1), axis=1)
    return resultados_1

@validacion_cedula_router.post("/validar_cedula/", tags=['Validacion_Inicial'])
async def validar_cedula():
    try:
        file_path = 'temp_files/validacion_inicial.xlsx'

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"El archivo en la ruta '{file_path}' no fue encontrado.")

        df = pd.read_excel(file_path)
        df = validar_Cedula(df)
        df.to_excel(file_path, index=False)

        si_rows_count_cedula = (df['cedula_es_invalida'] == 'SI').sum()
        no_rows_count_cedula = (df['cedula_es_invalida'] == 'NO').sum()


        si_rows_count_solicitudes = (df['Existen_Mas_Solicitudes_De_Matricula'] == 'SI').sum()
        no_rows_count_solicitudes = (df['Existen_Mas_Solicitudes_De_Matricula'] == 'NO').sum()


        message = (
            f"Validación de cédulas:\n"
            f"cédulas correctas: {no_rows_count_cedula} \n"
            f"cédulas incorrectas: {si_rows_count_cedula} \n"
            f"Validación de solicitudes de matrícula:\n"
            f"solicitudes de matrícula correctas: {no_rows_count_solicitudes}\n"
            f"solicitudes de matrícula incorrectas: {si_rows_count_solicitudes}\n"
        )

        return PlainTextResponse(content=message)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    
