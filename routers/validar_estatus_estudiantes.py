import os
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import pandas as pd
from datetime import datetime

# Define file paths and router
validacion_inicial_file_path = 'temp_files/validacion_inicial.xlsx'
validacion_estudiantes_estatus_router = APIRouter()

# Function to construct the database URL
def get_database_url(user: str, password: str, host: str, db_name: str, port: int = None) -> str:
    password_encoded = quote_plus(password)
    if port:
        return f"mysql+mysqlconnector://{user}:{password_encoded}@{host}:{port}/{db_name}"
    else:
        return f"mysql+mysqlconnector://{user}:{password_encoded}@{host}/{db_name}"

# Function to fetch student enrollment status from the database
def estudiantes_estatus(cursos: list, usuario: str, contrasena: str, host: str, port: str, nombre_base_datos: str) -> pd.DataFrame:

    database_url = get_database_url(usuario, contrasena, host, nombre_base_datos, port)
    engine = create_engine(database_url)

    cursos_str = ','.join([f"'{curso.strip()}'" for curso in cursos])
    consulta_sql = text(f"""
    SELECT
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

@validacion_estudiantes_estatus_router.post("/validar_estatus/", tags=['Validacion_Final'])
async def validacion_estudiantes_estatus_final(usuario: str, contrasena: str, host: str, port: str, nombre_base_datos: str):
    try:
        datos_df = pd.read_excel(validacion_inicial_file_path)
        datos_df['IDENTIFICACION'] = datos_df['IDENTIFICACION'].astype(str)
        datos_df['NOMBRE_CORTO_CURSO'] = datos_df['NOMBRE_CORTO_CURSO'].astype(str)

        cursos_unicos = datos_df['NOMBRE_CORTO_CURSO'].unique().tolist()
        estudiantes_estatus_df = estudiantes_estatus(cursos_unicos, usuario, contrasena, host, port, nombre_base_datos)


        # Merge the dataframes
        resultado = datos_df.merge(estudiantes_estatus_df, left_on='IDENTIFICACION', right_on='username', how='left', suffixes=('', '_estatus'))

        # Create the Esta_activo_estudiante column
        resultado['Esta_activo_estudiante'] = resultado['ESTA_ACTIVO'].apply(lambda x: 'SI' if x == 1 else 'NO')

        # Create the lastnamephonetic column only if enrolment_status is 0
        resultado['lastnamephonetic'] = resultado.apply(
            lambda row: f"{row['courseshortname']}|{row['enrolment_start_date'].strftime('%d/%m/%Y')}|{row['enrolment_end_date'].strftime('%d/%m/%Y')}" if row['ESTA_ACTIVO'] == 0 else '', axis=1)

        # Replace NaN and infinite values before converting to JSON
        resultado = resultado.replace({pd.NA: None, float('inf'): None, float('-inf'): None})

        columns_to_drop = [
            'CourseShortName_estatus.1', 'CourseFullName_estatus.1', 'UserCedula_estatus.1', 
            'UserNombre_estatus.1', 'UserApellido_estatus.1', 'CertificadoFechaEmision_estatus.1', 
            'CertificadoCodigo_estatus.1','CourseShortName_estatus', 'CourseFullName_estatus', 'UserCedula_estatus', 
            'UserNombre_estatus', 'UserApellido_estatus', 'CertificadoFechaEmision_estatus', 
            'CertificadoCodigo_estatus','courseshortname','username','first_name','last_name','enrolment_status',
            'enrolment_start_date','enrolment_end_date','ESTA_ACTIVO'

        ]
        resultado.drop(columns=columns_to_drop, inplace=True, errors='ignore')
        # Save the result to an Excel file
        resultado.to_excel(validacion_inicial_file_path, index=False)


        message = (
            f"Verificación de estatus Terminada\n"
            
        )

        return PlainTextResponse(content=message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")













