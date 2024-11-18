from fastapi import APIRouter, HTTPException,Depends
from fastapi.responses import JSONResponse
from jwt_manager import JWTBearer
import pandas as pd
import os

revision_matricula_cursos_router = APIRouter()

@revision_matricula_cursos_router.post("/api2/revision_matricula_cursos/", tags=['Cursos'], status_code=200,dependencies=[Depends(JWTBearer())])
async def revision_matricula_cursos(mismo_curso: bool = False):

    # Verificar que el archivo de Excel existe
    """
    Verifica que todos los estudiantes estén en el mismo curso, o que cada estudiante esté en un curso diferente.

    Args:
        mismo_curso (bool, optional): Indica si todos los estudiantes deben estar en el mismo curso. Defaults to False.

    Returns:
        JSONResponse: Un objeto JSON con información sobre el estado de la verificación.
    """
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

        # Estructura del mensaje y código de estado basado en la lógica
        if mismo_curso and num_cursos_unicos == 1:
            response_data = {
                "success": True,
                "message": "Todos los estudiantes tienen el mismo curso.",
                "num_cursos_unicos": num_cursos_unicos
            }
            status = 200
        elif not mismo_curso and num_cursos_unicos > 1:
            response_data = {
                "success": True,
                "message": "Los estudiantes están en diferentes cursos.",
                "num_cursos_unicos": num_cursos_unicos
            }
            status = 200
        else:
            response_data = {
                "success": False,
                "message": "Error: La condición del curso no se cumple.",
                "num_cursos_unicos": num_cursos_unicos
            }
            status = 400

        # Devolver respuesta con JSON estructurado
        return JSONResponse(content=response_data, status_code=status)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al verificar los cursos: {str(e)}")







