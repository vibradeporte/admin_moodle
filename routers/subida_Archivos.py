from fastapi import FastAPI, UploadFile, File, HTTPException, APIRouter
from fastapi.responses import JSONResponse
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

@verificacion_inicial_archivo.post("/SubirArchivo/", tags=['Archivos'])
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))

        # Create a temporary directory to save files
        temp_dir = "temp_files"
        os.makedirs(temp_dir, exist_ok=True)

        # Save the original file
        original_file_path = os.path.join(temp_dir, file.filename)
        with open(original_file_path, 'wb') as f:
            f.write(contents)

        # Check for missing columns
        missing_columns = [column for column in required_columns if column not in df.columns]
        if missing_columns:
            return JSONResponse(
                status_code=400,
                content={"message": f"El archivo no contiene las siguientes columnas: {', '.join(missing_columns)}"}
            )

        # Save the validated file
        validated_file_path = os.path.join(temp_dir, 'validacion_inicial.xlsx')
        df.to_excel(validated_file_path, index=False)

        return JSONResponse(
            status_code=200,
            content={"message": "El archivo cumple con la estructura y tipo deseado."}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


