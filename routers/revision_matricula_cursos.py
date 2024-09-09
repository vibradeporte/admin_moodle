from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import os

revision_matricula_cursos_router = APIRouter()

@revision_matricula_cursos_router.post("/revision_matricula_cursos/", tags=['Cursos'], status_code=200)
async def revision_matricula_cursos(mismo_curso: bool = False):

    # Verificar que el archivo de Excel existe
    archivo_excel = 'temp_files/validacion_inicial.xlsx'
    if not os.path.exists(archivo_excel):
        raise HTTPException(status_code=404, detail="El archivo de validación inicial no se encuentra.")

    try:
        # Leer el archivo Excel
        df_estudiantes = pd.read_excel(archivo_excel)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al leer el archivo Excel: {str(e)}")
    
    # Verificar los cursos de los estudiantes
    try:
        num_cursos_unicos = df_estudiantes['NOMBRE_CORTO_CURSO'].nunique()

        if mismo_curso and num_cursos_unicos == 1:
            message = "Todos los estudiantes tienen el mismo curso."
            status = 200
        elif not mismo_curso and num_cursos_unicos > 1:
            message = "Los estudiantes están en diferentes cursos."
            status = 200
        else:
            message = "Error: La condición del curso no se cumple."
            status = 400

        response_data = {"message": message}
        return JSONResponse(content=response_data, status_code=status)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al verificar los cursos: {str(e)}")






