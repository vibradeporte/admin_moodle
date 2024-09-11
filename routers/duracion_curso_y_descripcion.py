import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import pandas as pd
from fastapi.responses import JSONResponse

# Longitud máxima del nombre corto del curso
max_length_courseshortname = 37

# Crear el enrutador de FastAPI
duracion_curso_y_descripcion_router = APIRouter()

def construir_url_mysql(usuario_base_datos: str, contrasena_base_datos: str, host_base_datos: str, puerto_base_datos: str, nombre_base_datos: str) -> str:
    contrasena_codificada = quote_plus(contrasena_base_datos)
    return f"mysql+mysqlconnector://{usuario_base_datos}:{contrasena_codificada}@{host_base_datos}:{puerto_base_datos}/{nombre_base_datos}"

@duracion_curso_y_descripcion_router.post("/duracion_curso_y_descripcion/", tags=['Cursos'], status_code=200)
async def duracion_curso_y_descripcion(
    usuario_base_datos: str,
    contrasena_base_datos: str,
    host_base_datos: str,
    puerto_base_datos: str,
    nombre_base_datos: str
):
    """
    ## **Descripción:**
    Esta función lee un archivo excel con una columna 'NOMBRE_CORTO_CURSO', realiza la búsqueda de cada curso
    en la base de datos y agrega las columnas 'CourseId' y 'CourseDaysDuration' al mismo excel.
    """
    url_base_datos = construir_url_mysql(usuario_base_datos, contrasena_base_datos, host_base_datos, puerto_base_datos, nombre_base_datos)
    motor_base_datos = create_engine(url_base_datos)

    archivo_de_entrada = 'temp_files/validacion_inicial.xlsx'
    if not os.path.exists(archivo_de_entrada):
        raise HTTPException(status_code=404, detail="El archivo estudiantes_validados.xlsx no existe.")

    df_estudiantes = pd.read_excel(archivo_de_entrada)

    if 'NOMBRE_CORTO_CURSO' not in df_estudiantes.columns:
        raise HTTPException(status_code=400, detail="El archivo Excel no contiene la columna 'NOMBRE_CORTO_CURSO'.")

    course_ids = []
    course_durations = []

    try:
        with motor_base_datos.connect() as connection:
            for curso in df_estudiantes['NOMBRE_CORTO_CURSO']:
                consulta_sql = text("""
                    SELECT DISTINCT
                        c.id as CourseId,
                        SUBSTRING(c.idnumber, LOCATE('[', c.idnumber) + 1, LOCATE(']', c.idnumber) - LOCATE('[', c.idnumber) - 1) as CourseDaysDuration
                    FROM
                        mdl_course as c
                    WHERE
                        c.shortname = :curso
                    ORDER BY c.shortname;
                """).params(curso=curso)
                result = connection.execute(consulta_sql)
                row = result.fetchone()

                if row:
                    course_ids.append(row[0])
                    course_durations.append(row[1])
                else:
                    course_ids.append(None)
                    course_durations.append(None)

        df_estudiantes['CourseId'] = course_ids
        df_estudiantes['CourseDaysDuration'] = course_durations

        # Verificar si el directorio temp_files existe
        if not os.path.exists('temp_files'):
            os.makedirs('temp_files')

        df_estudiantes.to_excel(archivo_de_entrada, index=False)

        return JSONResponse(content='Registros encontrados y Excel actualizado.')

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la consulta: {str(e)}")

