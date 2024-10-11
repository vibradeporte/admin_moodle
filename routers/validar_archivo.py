import os
import pandas as pd
import requests
from fastapi import HTTPException, APIRouter
from fastapi.responses import JSONResponse
from io import BytesIO

verificacion_inicial_archivo = APIRouter()

required_columns = [
    'IDENTIFICACION', 'TIPO_IDENTIFICACION', 'NOMBRES', 'APELLIDOS', 'CORREO',
    'PAIS_DEL_MOVIL', 'NUMERO_MOVIL_WS_SIN_PAIS', 'EMPRESA', 'DESCRIPCIÓN', 
    'PAIS_DE_RESIDENCIA', 'CIUDAD', 'CORREO_SOLICITANTE', 'NRO_SEMANAS_DE_MATRICULA',
    'NOMBRE_LARGO_CURSO', 'NOMBRE_CORTO_CURSO','FECHA-HORA_BIENVENIDAS', 
    'DIAS_INFORMADOS_AL_ESTUDIANTE', 'ADVERTENCIA_CURSO_CULMINADO'
]

@verificacion_inicial_archivo.post("/Validar_archivo/", tags=['Validacion Archivo'])
def verificar_archivo(nombre_archivo: str):
    ruta = f'https://ulapi-production.up.railway.app/static/temp_files/{nombre_archivo}'
    
    # Verificar si el archivo tiene la extensión correcta
    if not ruta.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=415,
            detail="El archivo no es un archivo Excel. Por favor, usa un archivo con extensión .xlsx o .xls."
        )
    
    # Intentar descargar el archivo desde la URL
    try:
        response = requests.get(ruta)
        response.raise_for_status()  # Verifica si hubo algún error en la solicitud
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=404,
            detail=f"No se pudo descargar el archivo: {str(e)}"
        )
    
    try:
        # Leer el archivo Excel descargado usando pandas
        file_content = BytesIO(response.content)
        try:
            df = pd.read_excel(file_content, sheet_name='ESTUDIANTES')
        except ValueError:
            raise HTTPException(
                status_code=422,  # Unprocessable Entity
                detail="El archivo no contiene la hoja ESTUDIANTES."
            )

        # Eliminar filas completamente vacías
        df = df.dropna(how='all', axis=0)

        # Verificar si el DataFrame está vacío
        if df.empty:
            raise HTTPException(
                status_code=204,  # No Content
                detail="El archivo no contiene datos, todas las filas están en blanco."
            )

        print("Columnas del archivo cargado:", df.columns.tolist())

        # Verificar si faltan columnas requeridas
        missing_columns = [column for column in required_columns if column not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=401,
                detail=f"El archivo no contiene las siguientes columnas: {', '.join(missing_columns)}"
            )

        # Guardar el archivo validado
        validated_file_path = os.path.join('temp_files/', 'validacion_inicial.xlsx')  # Ajusta la ruta si es necesario
        df['CORREO_SOLICITANTE'] = df['CORREO_SOLICITANTE'].fillna('').str.lower()
        df['CORREO'] = df['CORREO'].fillna('').str.lower()
        df.to_excel(validated_file_path, index=False)

        return JSONResponse(
            content={"Exito": True, "message": "El archivo cumple con la estructura y tipo deseado."},
            status_code=200
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ocurrió un error al procesar el archivo: {str(e)}"
        )

