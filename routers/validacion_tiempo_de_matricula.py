import os
import re
import pandas as pd
from io import BytesIO
from urllib.parse import quote_plus
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from fastapi import APIRouter, HTTPException, FastAPI

validacion_tiempo_de_matricula_router = APIRouter()

def calcular_fechas_matricula(fila):
    """
    Calcula las fechas de inicio y fin de matrícula, así como la duración de la misma, dado un registro (fila) de datos.
    """
    # Extraer semanas de matrícula limpiando la cadena y reemplazando comas por puntos
    semanas_de_matricula = re.sub(r'[^0-9,.]', '', str(fila['NRO_SEMANAS_DE_MATRICULA'])).replace(',', '.')
    
    # Si no hay un valor válido, poner '0'
    if not semanas_de_matricula:
        semanas_de_matricula = '0'
    
    # Convertir semanas a días de inscripción
    dias_inscripcion_matricula = abs(int(float(semanas_de_matricula))) * 7

    # Si no hay duración del curso o es inválida, poner 0
    if pd.isna(fila['CourseDaysDuration']) or fila['CourseDaysDuration'] in ['', None]:
        duracion_curso_dias = 0
    else:
        duracion_curso_dias = int(float(fila['CourseDaysDuration']))

    # Si dias_inscripcion_matricula es 0, usar duracion_curso_dias
    if dias_inscripcion_matricula == 0:
        duracion_matricula = duracion_curso_dias
    else:
        duracion_matricula = dias_inscripcion_matricula

    # Verificar si excede el tiempo permitido de matrícula
    if duracion_curso_dias <= 28 and (duracion_matricula > 4 * duracion_curso_dias):
        excede_tiempo_de_matricula = "SI"
    elif duracion_curso_dias > 28 and (duracion_matricula > 2 * duracion_curso_dias):
        excede_tiempo_de_matricula = "SI"
    else:
        excede_tiempo_de_matricula = "NO"

    # Calcular las fechas de inicio y fin de la matrícula
    fecha_inicio_matricula = datetime.now().replace(hour=4, minute=0, second=0, microsecond=0)
    fecha_fin_matricula = fecha_inicio_matricula + timedelta(days=duracion_matricula)
    fecha_fin_matricula = fecha_fin_matricula.replace(hour=4, minute=0, second=0, microsecond=0)

    # Convertir las fechas a timestamp
    timestart = max(int(fecha_inicio_matricula.timestamp()), 0)
    timeend = max(int(fecha_fin_matricula.timestamp()), 0)

    # Devolver los resultados en un pandas Series
    return pd.Series([timestart, timeend, duracion_matricula, excede_tiempo_de_matricula],
                     index=['timestart', 'timeend', 'NRO_DIAS_DE_MATRICULAS', 'El tiempo de matricula es invalido'])




@validacion_tiempo_de_matricula_router.post("/validacion_tiempo_de_matricula/", tags=['Cursos'], status_code=200)
async def validacion_tiempo_de_matricula():
    # Verificar que el archivo de Excel existe
    archivo_excel = 'temp_files/validacion_inicial.xlsx'
    if not os.path.exists(archivo_excel):
        raise HTTPException(status_code=404, detail="El archivo de validación inicial no se encuentra.")

    try:
        # Leer el archivo Excel
        df_estudiantes = pd.read_excel(archivo_excel)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al leer el archivo Excel: {str(e)}")
    
    # Aplicar la función de cálculo de fechas de matrícula
    try:
        df_estudiantes[['timestart', 'timeend', 'NRO_DIAS_DE_MATRICULAS', 'El tiempo de matricula es invalido']] = df_estudiantes.apply(calcular_fechas_matricula, axis=1)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al aplicar cálculo de fechas: {str(e)}")
    
    # Reemplazar valores no válidos con None para JSON
    df_estudiantes = df_estudiantes.replace({pd.NA: None, pd.NaT: None, float('inf'): None, float('-inf'): None})
    
    # Guardar el archivo actualizado
    try:
        df_estudiantes.to_excel(archivo_excel, index=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar el archivo Excel: {e}")

    return JSONResponse(content='Se realizó la validación de tiempo de matricula en el archivo de Matriculas', status_code=200)
