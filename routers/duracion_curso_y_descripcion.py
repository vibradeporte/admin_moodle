import os
from fastapi import APIRouter, HTTPException,Depends
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from jwt_manager import JWTBearer
import pandas as pd
from fastapi.responses import JSONResponse

# Longitud máxima del nombre corto del curso
max_length_courseshortname = 37

# Crear el enrutador de FastAPI
duracion_curso_y_descripcion_router = APIRouter()

def construir_url_mysql(usuario_base_datos: str, contrasena_base_datos: str, host_base_datos: str, puerto_base_datos: str, nombre_base_datos: str) -> str:
    """
    Construye la URL de conexión a la base de datos.

    Args:
        usuario_base_datos (str): Usuario de la base de datos.
        contrasena_base_datos (str): Contraseña del usuario de la base de datos.
        host_base_datos (str): Host de la base de datos.
        puerto_base_datos (str): Puerto de la base de datos.
        nombre_base_datos (str): Nombre de la base de datos.

    Returns:
        str: URL de conexión a la base de datos.
    """
    contrasena_codificada = quote_plus(contrasena_base_datos)
    return f"mysql+mysqlconnector://{usuario_base_datos}:{contrasena_codificada}@{host_base_datos}:{puerto_base_datos}/{nombre_base_datos}"

def obtener_plantillas_wapp(database_url,engine,cursos):
    """
    Obtiene las plantillas de Whatsapp para cada uno de los cursos 
    especificados en la lista de cursos.

    Args:
        database_url (str): URL de la base de datos.
        engine: Engine de la base de datos.
        cursos (list): Lista de cursos.

    Returns:
        pd.DataFrame: Un DataFrame con las plantillas de Whatsapp para
        cada curso. El DataFrame tendrá las siguientes columnas:

        * CourseId: ID del curso.
        * NOMBRE_CORTO_CURSO: Nombre corto del curso.
        * plantilla_whatsapp: ID de la plantilla de Whatsapp.
        * ¿El ID de mensajes de bienvenida de Whatsapp es INVALIDO?: 
            Indica si el campo 'plantilla_whatsapp' es inválido.

    Raises:
        HTTPException: Si hay un error de conexión a la base de datos.
    """
    cursos_str = ','.join([f"'{curso.strip()}'" for curso in cursos])
    consulta_sql = text(f"""
        SELECT DISTINCT
            c.id AS CourseId,
            c.shortname AS NOMBRE_CORTO_CURSO,
            SUBSTRING(
                c.idnumber, 
                LOCATE(':', c.idnumber, LOCATE('PWH:', c.idnumber)) + 1, 
                LOCATE('>', c.idnumber, LOCATE('PWH:', c.idnumber)) - LOCATE(':', c.idnumber, LOCATE('PWH:', c.idnumber)) - 1
            ) AS plantilla_whatsapp
        FROM
            mdl_course AS c
        WHERE
            c.shortname IN ({cursos_str})
        ORDER BY
            c.shortname;
    """)

    try:
        with engine.connect() as connection:
            result = connection.execute(consulta_sql)
            rows = result.fetchall()
            column_names = result.keys()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de conexión a la base de datos: {str(e)}")

    # Verificar si hay resultados
    if not rows:
        return pd.DataFrame()

    else:
    # Convertir los resultados en un DataFrame
        result_dicts = [dict(zip(column_names, row)) for row in rows]
        df_plantilla = pd.DataFrame(result_dicts)

        # Verificar si el campo 'plantilla_whatsapp' es inválido
        df_plantilla['¿El ID de mensajes de bienvenida de Whatsapp es INVALIDO?'] = df_plantilla.apply(
            lambda row: "SI" if row['plantilla_whatsapp'] is None or len(row['plantilla_whatsapp']) == 0 or len(row['plantilla_whatsapp']) <= 15 else "NO", axis=1
        )

        # Guardar el DataFrame en un archivo CSV
        temp_dir = 'temp_files'
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        df_plantilla.to_csv(f'{temp_dir}/plantillas_wapp.csv', index=False)

    return df_plantilla

def obtener_plantillas_correos(database_url,engine,cursos) -> pd.DataFrame:
    """
    Obtiene las plantillas de correos de bienvenida de los cursos

    Esta función devuelve un DataFrame con las plantillas de correos de bienvenida de los cursos
    especificados en la variable 'cursos'. La plantilla se encuentra en la columna 'plantilla_Html'.
    La función verifica si la plantilla HTML contiene los placeholders '{username}', '{firstname}', '{lastname}', '{password}'.
    Si contiene todos los placeholders, se considera que la plantilla es válida. En caso contrario, se considera
    inválida y se indica en la columna '¿La plantilla HTML de correos de bienvenida es INVALIDA?'.
    
    Parameters:
        database_url (str): URL de la base de datos.
        engine (Engine): motor de la base de datos.
        cursos (list): lista de nombres cortos de los cursos.
    
    Returns:
        pd.DataFrame: DataFrame con las plantillas de correos de bienvenida de los cursos.
    """
    cursos_str = ','.join([f"'{curso.strip()}'" for curso in cursos])

    consulta_sql = text(f"""
        SELECT 
            shortname as NOMBRE_CORTO_CURSO,
            summary as plantilla_Html
        FROM mdl_course 
        WHERE 
            shortname IN ({cursos_str})
            AND summaryformat = 1;
        """)

    try:
        with engine.connect() as connection:
            result = connection.execute(consulta_sql)
            rows = result.fetchall()
            column_names = result.keys()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de conexión a la base de datos: {str(e)}")

    if not rows:
        return pd.DataFrame()
    else:
    # Convertir los resultados en un DataFrame
        result_dicts = [dict(zip(column_names, row)) for row in rows]
        df_plantilla = pd.DataFrame(result_dicts)
        df_plantilla['¿La plantilla HTML de correos de bienvenida es INVALIDA?'] = df_plantilla['plantilla_Html'].astype(str).apply(
            lambda texto: "NO" if all(placeholder in texto for placeholder in ['{username}', '{firstname}', '{lastname}', '{password}']) else "SI"
        )
        df_plantilla.to_csv('temp_files/plantillas_correos.csv', index=False)

    return df_plantilla

@duracion_curso_y_descripcion_router.post("/duracion_curso_y_descripcion/", tags=['Cursos'], status_code=200,dependencies=[Depends(JWTBearer())])
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
    archivo_de_entrada = 'temp_files/validacion_inicial.xlsx'
    if not os.path.exists(archivo_de_entrada):
        raise HTTPException(status_code=404, detail="El archivo estudiantes_validados.xlsx no existe.")
    df_estudiantes = pd.read_excel(archivo_de_entrada)
    if 'NOMBRE_CORTO_CURSO' not in df_estudiantes.columns:
        raise HTTPException(status_code=400, detail="El archivo Excel no contiene la columna 'NOMBRE_CORTO_CURSO'.")

    cursos = df_estudiantes['NOMBRE_CORTO_CURSO'].unique().tolist()

    # Conectar a la base de datos
    url_base_datos = construir_url_mysql(usuario_base_datos, contrasena_base_datos, host_base_datos, puerto_base_datos, nombre_base_datos)
    motor_base_datos = create_engine(url_base_datos)

    # Obtener las plantillas de Whatsapp y correos
    df_plantlina_wapp = obtener_plantillas_wapp(url_base_datos,motor_base_datos,cursos)
    df_plantilla_wapp = df_plantlina_wapp.drop(columns=['plantilla_whatsapp','CourseId'])
    df_plantilla_correos = obtener_plantillas_correos(url_base_datos,motor_base_datos,cursos)
    df_plantilla_correos = df_plantilla_correos.drop(columns=['plantilla_Html'])

    # Unir las plantillas
    df_plantillas = df_plantilla_correos.merge(df_plantilla_wapp, on='NOMBRE_CORTO_CURSO', how='left')

    # Unir las plantillas con los estudiantes
    df_estudiantes = df_estudiantes.merge(df_plantillas, on='NOMBRE_CORTO_CURSO', how='left')

    # Obtener los IDs de los cursos y sus duraciones
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

        # Asignar los IDs y duraciones a los estudiantes
        df_estudiantes['CourseId'] = course_ids
        df_estudiantes['CourseDaysDuration'] = course_durations
        df_estudiantes['¿El Curso NO contiene dias de duracion de matrícula?'] = df_estudiantes.apply(lambda row: 'SI' if row['CourseDaysDuration'] is None or row['CourseDaysDuration'] == '' else 'NO', axis=1)

        # Verificar si el directorio temp_files existe
        if not os.path.exists('temp_files'):
            os.makedirs('temp_files')
        df_estudiantes.to_excel(archivo_de_entrada, index=False)

        return JSONResponse(content='Registros encontrados y Excel actualizado.')

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la consulta: {str(e)}")






