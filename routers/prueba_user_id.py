from fastapi import APIRouter, HTTPException, UploadFile, File, FastAPI
from fastapi.responses import JSONResponse
from io import BytesIO
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from urllib.parse import quote_plus

prueba_conseguir_id = APIRouter()

load_dotenv()
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
    dias_curso = row['CourseDaysDuration']
    semanas_inscripcion = int(float(semanas_inscripcion))
    dias_curso = int(float(dias_curso))
    fecha_actual = datetime.now()
    
    if semanas_inscripcion is None or semanas_inscripcion == "":
        semanas_inscripcion = dias_curso // 7
    
    fecha_inicio_matricula = fecha_actual + timedelta(weeks=int(semanas_inscripcion))
    
    fecha_fin_curso = fecha_inicio_matricula + timedelta(days=dias_curso)
    
    timestart = int(fecha_inicio_matricula.timestamp())
    timeend = int(fecha_fin_curso.timestamp())
    
    return pd.Series([timestart, timeend])

@prueba_conseguir_id.post("/prueba_conseguir_id/", tags=['Moodle'], status_code=200)
async def id_estudiante():
    USER_DB_UL = os.getenv("USER_DB_UL")
    PASS_DB_UL = os.getenv("PASS_DB_UL")
    HOST_DB = os.getenv("HOST_DB")
    NAME_DB_UL = os.getenv("NAME_DB_UL")
    contrasena_codificada = quote_plus(PASS_DB_UL)
    DATABASE_URL = f"mysql+mysqlconnector://{USER_DB_UL}:{contrasena_codificada}@{HOST_DB}/{NAME_DB_UL}"
    engine = create_engine(DATABASE_URL)

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
    df[['timestart', 'timeend']] = df.apply(calcular_fechas_matricula, axis=1)
    df_cleaned = df.replace({pd.NA: None, pd.NaT: None, float('inf'): None, float('-inf'): None})
    df.to_csv('temp_files/estudiantes_validados.csv', index=False)
    try:
        json_response = df_cleaned.to_dict(orient='records')
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Error converting DataFrame to JSON: {str(e)}")

    return JSONResponse(content=json_response)


