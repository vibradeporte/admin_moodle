from fastapi import APIRouter, HTTPException, UploadFile, File, FastAPI
from fastapi.responses import JSONResponse
from io import BytesIO
import pandas as pd
from sqlalchemy import create_engine, text
import os
from datetime import datetime, timedelta
from urllib.parse import quote_plus

prueba_conseguir_id = APIRouter()

def get_database_url(user: str, password: str, host: str, port: str, db_name: str) -> str:
    password_encoded = quote_plus(password)
    return f"mysql+mysqlconnector://{user}:{password_encoded}@{host}:{port}/{db_name}"

WS_FUNCTION = "enrol_manual_enrol_users"
HTTP_MESSAGES = {
    'FALTAN_CARACTERES': "Missing characters",
    'CARACTER_INVALIDO_ID': "Invalid character in ID",
    'SOBRAN_CARACTERES_10': "More than 10 characters",
    'SOBRAN_CARACTERES_1': "More than 1 character",
    'CARACTER_INVALIDO': "Invalid character",
    'OK': "Operation successful",
    'USER_NO_EXISTE': "User does not exist",
    'COURSE_NO_EXISTE': "Course does not exist",
    'NO_MATRICULA_MANUAL': "Manual enrolment not allowed"
}

def calcular_fechas_matricula(row):
    semanas_inscripcion = row['NRO_SEMANAS_DE_MATRICULA']
    dias_curso = int(float(row['CourseDaysDuration']))
    
    # Convertir semanas_inscripcion a numérico, coaccionando errores a NaN
    semanas_inscripcion = pd.to_numeric(semanas_inscripcion, errors='coerce')
    
    if pd.isna(semanas_inscripcion):
        semanas_inscripcion = None
        
    if semanas_inscripcion is None:
        duracion_matricula = dias_curso
    else:
        duracion_matricula = int(semanas_inscripcion * 7)

    fecha_inicio_matricula = datetime.now() 
    fecha_inicio_matricula = fecha_inicio_matricula.replace(hour=0, minute=0, second=0, microsecond=0)
    fecha_fin_matricula = fecha_inicio_matricula + timedelta(days=int(duracion_matricula))
    fecha_fin_matricula = fecha_fin_matricula.replace(hour=23, minute=59, second=0, microsecond=0)
    
    ajuste_por_diferencia_horario = 5 * 60 * 60
    
    timestart = int(fecha_inicio_matricula.timestamp()) + ajuste_por_diferencia_horario
    timeend = int(fecha_fin_matricula.timestamp()) + ajuste_por_diferencia_horario
    
    return pd.Series([timestart, timeend, duracion_matricula], index=['timestart', 'timeend', 'NRO_DIAS_DE_MATRICULAS'])

@prueba_conseguir_id.post("/prueba_conseguir_id/", tags=['Moodle'], status_code=200)
async def id_estudiante(usuario: str,contrasena: str,host: str,port: str,nombre_base_datos: str):
    database_url = get_database_url(usuario, contrasena, host, port, nombre_base_datos)
    engine = create_engine(database_url)

    try:
        df = pd.read_csv('temp_files/estudiantes_validados.csv')
        df = df.astype(str)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid file format or content")

    if 'username' not in df.columns:
        raise HTTPException(status_code=400, detail="Missing 'username' column in CSV")

    student_ids = []
    with engine.connect() as connection:
        ids = df['username'].values
        ids_str = ', '.join([':username' + str(i) for i in range(len(ids))])
        consulta_sql = text(f"""
            SELECT
                u.id, u.username, u.firstname, u.lastname
            FROM
                mdl_user u
            WHERE
                u.username IN ({ids_str});
        """)
        parameters = {f'username{i}': ids[i] for i in range(len(ids))}
        result = connection.execute(consulta_sql, parameters)

        user_data = {row[1]: row[0] for row in result}  # row[1] is username, row[0] is id
        for username in df['username']:
            student_ids.append(user_data.get(username, ''))

    df['userid'] = student_ids
    df[['timestart', 'timeend', 'NRO_DIAS_DE_MATRICULAS']] = df.apply(calcular_fechas_matricula, axis=1)
    df_cleaned = df.replace({pd.NA: None, pd.NaT: None, float('inf'): None, float('-inf'): None})
    df.to_csv('temp_files/estudiantes_validados.csv', index=False)
    try:
        json_response = df_cleaned.to_dict(orient='records')
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Error converting DataFrame to JSON: {str(e)}")

    return JSONResponse(content=json_response)


