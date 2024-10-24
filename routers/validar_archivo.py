import os
import pandas as pd
import requests
from fastapi import HTTPException, APIRouter
from fastapi.responses import JSONResponse
from io import BytesIO

verificacion_inicial_archivo = APIRouter()

columnas_requeridas = [
    'IDENTIFICACION', 'TIPO_IDENTIFICACION', 'NOMBRES', 'APELLIDOS', 'CORREO',
    'PAIS_DEL_MOVIL', 'NUMERO_MOVIL_WS_SIN_PAIS', 'EMPRESA', 'DESCRIPCIÓN',
    'PAIS_DE_RESIDENCIA', 'CIUDAD', 'CORREO_SOLICITANTE', 'NRO_SEMANAS_DE_MATRICULA',
    'NOMBRE_LARGO_CURSO', 'NOMBRE_CORTO_CURSO',
    'DIAS_INFORMADOS_AL_ESTUDIANTE', 'ADVERTENCIA_CURSO_CULMINADO'
]

@verificacion_inicial_archivo.post("/Validar_archivo/", tags=['Validacion Archivo'])
def verificar_archivo(nombre_archivo: str):
    ruta = f'https://ulapi-production.up.railway.app/static/temp_files/{nombre_archivo}'
    
    if not ruta.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=415,
            detail="El archivo no es un archivo Excel. Por favor, usa un archivo con extensión .xlsx o .xls."
        )
    
    try:
        response = requests.get(ruta)
        response.raise_for_status()  # Verifica si hubo algún error en la solicitud
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=404,
            detail=f"No se pudo descargar el archivo: {str(e)}"
        )
    
    try:
        contenido_archivo = BytesIO(response.content)
        try:
            df = pd.read_excel(contenido_archivo, sheet_name='ESTUDIANTES')
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="El archivo no contiene la hoja ESTUDIANTES."
            )


        df = df.dropna(how='all', axis=0)


        if df.empty:
            raise HTTPException(
                status_code=204,  # No Content
                detail="El archivo no contiene datos, todas las filas están en blanco."
            )

        print("Columnas del archivo cargado:", df.columns.tolist())


        columnas_faltantes = [columna for columna in columnas_requeridas if columna not in df.columns]
        if columnas_faltantes:
            raise HTTPException(
                status_code=401,
                detail=f"El archivo no contiene las siguientes columnas: {', '.join(columnas_faltantes)}"
            )


        ruta_archivo_validado = os.path.join('temp_files/', 'validacion_inicial.xlsx')  # Ajusta la ruta si es necesario
        df['CORREO_SOLICITANTE'] = df['CORREO_SOLICITANTE'].fillna('').str.lower()
        df['CORREO'] = df['CORREO'].fillna('').str.lower()
        df.to_excel(ruta_archivo_validado, index=False)

        return JSONResponse(
            content={"Exito": True, "message": "El archivo cumple con la estructura y tipo deseado."},
            status_code=200
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ocurrió un error al procesar el archivo: {str(e)}"
        )
