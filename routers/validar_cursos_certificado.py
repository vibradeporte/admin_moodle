from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
import pandas as pd
import numpy as np
import os
from routers.est_matriculados_curso_con_certificados import estudiantes_matriculados_con_cer

validacion_inicial_file_path = 'temp_files/validacion_inicial.xlsx'
validacion_cursos_certificado_router = APIRouter()

def registros_cursos_certificados(curso):
    # Esta función debe ser definida o importada para que el código funcione correctamente.
    # Se supone que devuelve un DataFrame con los certificados del curso dado.
    pass

def validar_existencia_certificado_cursos(datos):
    # Crear un DataFrame vacío para almacenar todos los certificados
    all_cursos_certificado = pd.DataFrame()
    
    # Asegurar que las columnas sean de tipo str
    datos['IDENTIFICACION'] = datos['IDENTIFICACION'].astype(str)
    datos['NOMBRE_CORTO_CURSO'] = datos['NOMBRE_CORTO_CURSO'].astype(str)
    
    # Iterar sobre los cursos únicos
    for curso in set(datos['NOMBRE_CORTO_CURSO']):
        # Obtener los certificados del curso actual
        cursos_certificado = registros_cursos_certificados(curso)
        
        # Asegurarse de que la columna UserCedula no tenga valores NaN y convertir a str
        cursos_certificado = cursos_certificado.dropna(subset=["UserCedula"])
        cursos_certificado['UserCedula'] = cursos_certificado['UserCedula'].astype(str)
        cursos_certificado['CourseShortName'] = cursos_certificado['CourseShortName'].astype(str)
        
        # Añadir los certificados del curso actual al DataFrame total
        all_cursos_certificado = pd.concat([all_cursos_certificado, cursos_certificado], ignore_index=True)
    
    # Realizar el merge entre los datos originales y los certificados
    resultado = pd.merge(datos, all_cursos_certificado, 
                         left_on=['IDENTIFICACION'], 
                         right_on=['UserCedula'], 
                         how='left')
    
    # Crear la columna de advertencia
    resultado['ADVERTENCIA_CURSO_CULMINADO'] = resultado.apply(
        lambda row: f"{row['CourseShortName']},{row['UserCedula']},{row['CertificadoFechaEmision']}" 
                    if not pd.isna(row['UserCedula']) else 'NO', axis=1)
    
    # Eliminar las columnas innecesarias del resultado final
    # resultado = resultado.drop(columns=['CourseShortName', 'UserCedula', 'CertificadoFechaEmision',
    #                                     'CourseFullName', 'UserNombre', 'UserApellido', 'CertificadoCodigo'])
    
    return resultado

@validacion_cursos.post("/validar_cursos_certificado/", tags=['Cursos'])
async def validate_courses():
    try:
        validated_df = pd.read_excel(validacion_inicial_file_path)
        # Validar cursos
        datos = validar_existencia_certificado_cursos(validated_df)

        validos_matricular = datos[datos['ADVERTENCIA_CURSO_CULMINADO'] == 'NO']
        validos_matricular = validos_matricular.drop(columns=['CourseShortName', 'UserCedula', 'CertificadoFechaEmision',
                                        'CourseFullName', 'UserNombre', 'UserApellido', 'CertificadoCodigo'])
        
        no_seran_matriculados = datos[datos['ADVERTENCIA_CURSO_CULMINADO'] != 'NO']

        validos_matricular.to_excel(validacion_inicial_file_path, index=False)
        no_seran_matriculados.to_excel('temp_files/tienen_vertificado_curso.xlsx', index=False)
        
        si_rows_count = len(no_seran_matriculados)
        no_rows_count = len(validos_matricular)

        if not datos.empty:
            message = (
                f"VALIDACIÓN DE CERTIFICADOS DE CURSOS: \n"
                f"{no_rows_count} MATRICULAS VALIDAS \n"
                f"{si_rows_count} MATRICULAS REDUNDANTES \n"
            )
            return PlainTextResponse(content=message)
        else:
            return PlainTextResponse(content="No se encontraron datos para validar.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante la validación de cursos: {e}")
