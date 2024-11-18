import os
from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import pandas as pd
from datetime import datetime
from jwt_manager import JWTBearer

validacion_inicial_file_path = 'temp_files/validacion_inicial.xlsx'
validacion_estudiantes_estatus_router = APIRouter()

def get_database_url(user: str, password: str, host: str, db_name: str, port: int = None) -> str:
    """
    Genera la URL de conexión para la base de datos.

    :param user: Usuario de la base de datos.
    :param password: Contraseña del usuario de la base de datos.
    :param host: Host de la base de datos.
    :param db_name: Nombre de la base de datos.
    :param port: Puerto de conexión a la base de datos.
    :return: URL de conexión para la base de datos.
    """
    password_encoded = quote_plus(password)
    return f"mysql+mysqlconnector://{user}:{password_encoded}@{host}:{port}/{db_name}"

def obtener_estatus_estudiantes(cursos: list, usuario: str, contrasena: str, host: str, puerto: str, nombre_base_datos: str) -> pd.DataFrame:
    """
    Obtiene el estatus de los estudiantes para los cursos especificados.

    :param cursos: Lista de cursos para verificar el estatus.
    :param usuario: Usuario de la base de datos.
    :param contrasena: Contraseña del usuario de la base de datos.
    :param host: Host de la base de datos.
    :param puerto: Puerto de conexión a la base de datos.
    :param nombre_base_datos: Nombre de la base de datos.
    :return: DataFrame con la información de estatus de los estudiantes.
    """
    database_url = get_database_url(usuario, contrasena, host, nombre_base_datos, puerto)
    engine = create_engine(database_url)

    cursos_str = ','.join([f"'{curso.strip()}'" for curso in cursos])
    consulta_sql = text(f"""
    SELECT DISTINCT
        c.shortname AS courseshortname,
        u.username AS username,
        u.firstname AS first_name,
        u.lastname AS last_name,
        ue.status AS enrolment_status,
        FROM_UNIXTIME(ue.timestart) AS enrolment_start_date,
        FROM_UNIXTIME(ue.timeend) AS enrolment_end_date,
        CASE
            WHEN ue.status = 0 AND FROM_UNIXTIME(ue.timeend) > NOW() THEN 1
            ELSE 0
        END AS ESTA_ACTIVO
    FROM
        mdl_user_enrolments ue
    JOIN
        mdl_enrol e ON ue.enrolid = e.id
    JOIN
        mdl_user u ON ue.userid = u.id
    JOIN
        mdl_course c ON e.courseid = c.id
    JOIN
        mdl_role_assignments ra ON ra.userid = u.id
    JOIN
        mdl_context ctx ON ra.contextid = ctx.id AND ctx.contextlevel = 50
    JOIN
        mdl_role r ON ra.roleid = r.id
    WHERE
        c.shortname IN ({cursos_str})
        AND r.shortname = 'student'
        AND u.username REGEXP '^[0-9]+$';
    """)

    with engine.connect() as connection:
        result = connection.execute(consulta_sql)
        rows = result.fetchall()
        column_names = result.keys()

    if not rows:
        return pd.DataFrame()

    result_dicts = [dict(zip(column_names, row)) for row in rows]
    return pd.DataFrame(result_dicts)

@validacion_estudiantes_estatus_router.post("/api2/validar_estatus/", tags=['Validacion_Final'], dependencies=[Depends(JWTBearer())])
async def validacion_estudiantes_estatus_final(usuario: str, contrasena: str, host: str, port: str, nombre_base_datos: str):
    """
    Valida el estatus de los estudiantes en los cursos especificados.

    :param usuario: Usuario de la base de datos.
    :param contrasena: Contraseña del usuario de la base de datos.
    :param host: Host de la base de datos.
    :param port: Puerto de conexión a la base de datos.
    :param nombre_base_datos: Nombre de la base de datos.
    :return: JSONResponse con el estado de la verificación.
    """
    try:
        # Leer datos iniciales desde el archivo Excel
        datos_df = pd.read_excel(validacion_inicial_file_path)
        
        # Convertir la columna IDENTIFICACION a string y eliminar '.0' si está presente
        datos_df['IDENTIFICACION'] = datos_df['IDENTIFICACION'].apply(lambda x: str(x).replace('.0', '') if '.0' in str(x) else str(x))
        datos_df['NOMBRE_CORTO_CURSO'] = datos_df['NOMBRE_CORTO_CURSO'].astype(str)

        # Obtener los cursos únicos de los datos
        cursos_unicos = datos_df['NOMBRE_CORTO_CURSO'].unique().tolist()
        
        # Obtener el estatus de los estudiantes desde la base de datos
        estudiantes_estatus_df = obtener_estatus_estudiantes(cursos_unicos, usuario, contrasena, host, port, nombre_base_datos)
        
        if estudiantes_estatus_df.empty:
            # Si no hay datos de estudiantes, agregar columnas predeterminadas
            datos_df['Esta_activo_estudiante'] = 'NO'
            datos_df['lastnamephonetic'] = ' '
            datos_df.to_excel(validacion_inicial_file_path, index=False)
            return JSONResponse(status_code=200, content={"status": "Verificación de estatus Terminada"})
        else:
            # Realizar el merge de los DataFrames
            resultado = datos_df.merge(estudiantes_estatus_df, left_on=['IDENTIFICACION', 'NOMBRE_CORTO_CURSO'], right_on=['username', 'courseshortname'], how='left', suffixes=('', '_estatus'))

            # Actualizar la columna 'Esta_activo_estudiante'
            resultado['Esta_activo_estudiante'] = resultado['ESTA_ACTIVO'].apply(lambda x: 'SI' if x == 1 else 'NO')

            # Actualizar la columna 'lastnamephonetic'
            resultado['lastnamephonetic'] = resultado.apply(
                lambda row: f"{row['courseshortname']}|{row['enrolment_start_date'].strftime('%d/%m/%Y')}|{row['enrolment_end_date'].strftime('%d/%m/%Y')}" if row['ESTA_ACTIVO'] == 0 else '', axis=1
            )

            # Reemplazar valores NaN e infinitos con None
            resultado = resultado.replace({pd.NA: None, float('inf'): None, float('-inf'): None})

            # Eliminar columnas innecesarias
            columns_to_drop = [
                'courseshortname', 'username', 'first_name', 'last_name', 'enrolment_status',
                'enrolment_start_date', 'enrolment_end_date', 'ESTA_ACTIVO'
            ]
            resultado.drop(columns=columns_to_drop, inplace=True, errors='ignore')
            
            # Guardar los resultados en el archivo Excel
            resultado.to_excel(validacion_inicial_file_path, index=False)

            message = {
                "status": "Verificación de estatus Terminada",
                "estudiantes_validados": len(resultado)
            }

        return JSONResponse(content=message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ocurrió un error: {e}")







