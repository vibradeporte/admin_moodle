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
    
    # Check if the file is an Excel file
    if not ruta.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=415,
            detail="El archivo no es un archivo Excel. Por favor, usa un archivo con extensión .xlsx o .xls."
        )
    
    # Check if the file exists
    if not os.path.isfile(ruta):
        raise HTTPException(
            status_code=404,
            detail="El archivo especificado no existe. Por favor, verifica la ruta."
        )
    
    try:
        # Attempt to load the Excel file and the specified sheet
        try:
            df = pd.read_excel(ruta, sheet_name='ESTUDIANTES')
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="El archivo no contiene la hoja ESTUDIANTES."
            )

        # Remove completely empty rows
        df = df.dropna(how='all', axis=0)

        # Check if the DataFrame is empty
        if df.empty:
            raise HTTPException(
                status_code=204,
                detail="El archivo no contiene datos, todas las filas están en blanco."
            )

        print("Columnas del archivo cargado:", df.columns.tolist())

        # Check for missing columns
        missing_columns = [column for column in required_columns if column not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"El archivo no contiene las siguientes columnas: {', '.join(missing_columns)}"
            )
        
        # Save the validated file
        validated_file_path = os.path.join(os.path.dirname(ruta), 'validacion_inicial.xlsx')
        df.to_excel(validated_file_path, index=False)

        return PlainTextResponse(
            f"El archivo cumple con la estructura y tipo deseado. Archivo validado guardado en: {validated_file_path}",
            status_code=200
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ocurrió un error al procesar el archivo: {str(e)}"
        )

