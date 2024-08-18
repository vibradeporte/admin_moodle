from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.responses import PlainTextResponse
import pandas as pd
import os

verificacion_inicial_archivo = APIRouter()

required_columns = [
    'IDENTIFICACION', 'TIPO_IDENTIFICACION', 'NOMBRES', 'APELLIDOS', 'CORREO',
    'PAIS_DEL_MOVIL', 'NUMERO_MOVIL_WS_SIN_PAIS', 'EMPRESA', 'DESCRIPCIÓN', 
    'PAIS_DE_RESIDENCIA', 'CIUDAD', 'CORREO_SOLICITANTE', 'NRO_SEMANAS_DE_MATRICULA',
    'NOMBRE_LARGO_CURSO', 'NOMBRE_CORTO_CURSO', 'FECHA-HORA_BIENVENIDAS', 
    'DIAS_INFORMADOS_AL_ESTUDIANTE', 'ADVERTENCIA_CURSO_CULMINADO'
]

@verificacion_inicial_archivo.post("/VerificarArchivo/", tags=['Validacion_Inicial'])
async def verificar_archivo():
    ruta = 'temp_files/validacion_archivo.xlsx'
    if not ruta.endswith(('.xlsx', '.xls')):
        return PlainTextResponse(
            "El archivo no es un archivo Excel. Por favor, usa un archivo con extensión .xlsx o .xls.",
            status_code=500
        )
    
    if not os.path.isfile(ruta):
        return PlainTextResponse(
            "El archivo especificado no existe. Por favor, verifica la ruta.",
            status_code=500
        )
    
    try:
        try:
            df = pd.read_excel(ruta, sheet_name='ESTUDIANTES')
        except ValueError:
            return PlainTextResponse(
                "El archivo no contiene la hoja ESTUDIANTES.",
                status_code=500
            )

        df = df.dropna(how='all', axis=0) 

        if df.empty:
            return PlainTextResponse(
                "El archivo no contiene datos, todas las filas están en blanco.",
                status_code=500
            )

        print("Columnas del archivo cargado:", df.columns.tolist())

        missing_columns = [column for column in required_columns if column not in df.columns]
        if missing_columns:
            return PlainTextResponse(
                f"El archivo no contiene las siguientes columnas: {', '.join(missing_columns)}",
                status_code=500
            )
            
        validated_file_path = os.path.join(os.path.dirname(ruta), 'validacion_inicial.xlsx')
        df.to_excel(validated_file_path, index=False)

        return PlainTextResponse(
            f"El archivo cumple con la estructura y tipo deseado. Archivo validado guardado en: {validated_file_path}",
            status_code=200
        )
    except Exception as e:
        return PlainTextResponse(
            f"Ocurrió un error al procesar el archivo: {str(e)}",
            status_code=500
        )

