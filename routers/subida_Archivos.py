from fastapi import FastAPI, UploadFile, File, HTTPException, APIRouter
from fastapi.responses import PlainTextResponse
import pandas as pd
import io
import os

verificacion_inicial_archivo = APIRouter()

required_columns = [
    'IDENTIFICACION', 'TIPO_IDENTIFICACION', 'NOMBRES', 'APELLIDOS', 'CORREO',
    'PAIS_DEL_MOVIL', 'NUMERO_MOVIL_WS_SIN_PAIS', 'EMPRESA', 'DESCRIPCIÓN', 
    'PAIS_DE_RESIDENCIA', 'CIUDAD', 'CORREO_SOLICITANTE', 'NRO_SEMANAS_DE_MATRICULA',
    'NOMBRE_LARGO_CURSO', 'NOMBRE_CORTO_CURSO', 'FECHA-HORA_BIENVENIDAS', 
    'DIAS_INFORMADOS_AL_ESTUDIANTE', 'ADVERTENCIA_CURSO_CULMINADO'
]

@verificacion_inicial_archivo.post("/SubirArchivo/", tags=['Validacion_Inicial'])
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        return PlainTextResponse(
            "El archivo no es un archivo Excel. Por favor, sube un archivo con extensión .xlsx o .xls.",
            status_code=400
        )
    
    try:
        contents = await file.read()
        try:
            df = pd.read_excel(io.BytesIO(contents), sheet_name='ESTUDIANTES')
        except ValueError:
            return PlainTextResponse(
                "El archivo no contiene la hoja ESTUDIANTES.",
                status_code=400
            )

        if df.dropna(how='all').empty:
            return PlainTextResponse(
                "El archivo no contiene datos, todas las filas están en blanco.",
                status_code=400
            )
        
        temp_dir = "temp_files"
        os.makedirs(temp_dir, exist_ok=True)

        original_file_path = os.path.join(temp_dir, file.filename)
        with open(original_file_path, 'wb') as f:
            f.write(contents)
        
        print("Columnas del archivo cargado:", df.columns.tolist())
        
        missing_columns = [column for column in required_columns if column not in df.columns]
        if missing_columns:
            return PlainTextResponse(
                f"El archivo no contiene las siguientes columnas: {', '.join(missing_columns)}",
                status_code=400
            )
            
        validated_file_path = os.path.join(temp_dir, 'validacion_inicial.xlsx')
        df.to_excel(validated_file_path, index=False)

        return PlainTextResponse(
            "El archivo cumple con la estructura y tipo deseado.",
            status_code=200
        )
    except Exception as e:
        return PlainTextResponse(
            f"Ocurrió un error al procesar el archivo: {str(e)}",
            status_code=500
        )




