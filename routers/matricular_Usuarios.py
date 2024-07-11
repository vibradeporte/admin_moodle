from fastapi import APIRouter, HTTPException, UploadFile, File, FastAPI
from fastapi.responses import JSONResponse
from io import BytesIO
from datetime import datetime, timedelta
import requests
import os
import pandas as pd
import re
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

enrol_manual_enrol_users_router = APIRouter()
ROLEID = 5

load_dotenv()

MOODLE_URL = os.getenv("MOODLE_URL")
MOODLE_TOKEN = os.getenv("MOODLE_TOKEN")
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

def id_estudiante(df): 
    load_dotenv()
    usuario = os.getenv("USER_DB_UL")
    contrasena = os.getenv("PASS_DB_UL")
    host = os.getenv("HOST_DB")
    nombre_base_datos = os.getenv("NAME_DB_UL")
    contrasena_codificada = quote_plus(contrasena)
    DATABASE_URL = f"mysql+mysqlconnector://{usuario}:{contrasena_codificada}@{host}/{nombre_base_datos}"
    engine = create_engine(DATABASE_URL)

    if 'username' not in df.columns:
        raise HTTPException(status_code=400, detail="Missing 'username' column in DataFrame")

    student_ids = []
    with engine.connect() as connection:
        for id_est in df['username']:
            consulta_sql = text("""
                SELECT id
                FROM mdl_user
                WHERE username = :nombre_de_usuario;
            """).params(nombre_de_usuario=id_est)
            result = connection.execute(consulta_sql)
            row = result.fetchone()
            
            if row:
                student_ids.append(row[0])
            else:
                student_ids.append(None)

    df['userid'] = student_ids
    return df


def calcular_fechas_matricula(semanas_inscripcion, dias_curso):
    fecha_actual = datetime.now()
    
    if not semanas_inscripcion:
        semanas_inscripcion = dias_curso // 7
    
    fecha_inicio_matricula = fecha_actual + timedelta(weeks=int(semanas_inscripcion))
    fecha_fin_curso = fecha_inicio_matricula + timedelta(days=dias_curso)

    timestamp_inicio_matricula = int(fecha_inicio_matricula.timestamp())
    timestamp_fin_curso = int(fecha_fin_curso.timestamp())
    
    return timestamp_inicio_matricula, timestamp_fin_curso

def validate_id(value, field_name):
    if not value.isdigit():
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}")
    return int(value)

@enrol_manual_enrol_users_router.post("/enrol_users_from_csv/", tags=['Moodle'], status_code=200)
async def enrol_users_from_csv():
    try:
        # Leer el archivo CSV y especificar las columnas a usar
        df = pd.read_csv('temp_files/estudiantes_validados.csv', usecols=['username', 'CourseId', 'CourseDaysDuration', 'NRO_SEMANAS_DE_MATRICULA'])
        df = id_estudiante(df)
        # Comprobar si hay valores faltantes en las columnas cruciales
        if df['userid'].isnull().any():
            raise HTTPException(status_code=400, detail="Missing values in 'userid' column")
        if df['CourseId'].isnull().any():
            raise HTTPException(status_code=400, detail="Missing values in 'CourseId' column")

        # Manejar los valores faltantes en 'CourseDaysDuration' estableciéndolos a 0 si están vacíos
        df['CourseDaysDuration'] = df['CourseDaysDuration'].fillna(0)

        # Calcular TIMESTART y TIMEEND
        df[['TIMESTART', 'TIMEEND']] = df.apply(
            lambda row: calcular_fechas_matricula(row['NRO_SEMANAS_DE_MATRICULA'], row['CourseDaysDuration']), 
            axis=1,
            result_type='expand'
        )

        df = df.fillna('')
        df = df.astype(str)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    results = []
    for index, row in df.iterrows():
        USERID = row['userid']
        COURSEID = row['CourseId']
        TIMESTART = row['TIMESTART'] if row['TIMESTART'] else None
        TIMEEND = row['TIMEEND'] if row['TIMEEND'] else None
        SUSPEND = None

        if SUSPEND:
            if len(SUSPEND) > 1:
                raise HTTPException(status_code=400, detail=HTTP_MESSAGES['SOBRAN_CARACTERES_1'])
            if not re.match(r'^[0-9]$', SUSPEND):
                raise HTTPException(status_code=400, detail=HTTP_MESSAGES['CARACTER_INVALIDO'])

        url = f"{MOODLE_URL}/webservice/rest/server.php"
        params = {
            "wstoken": MOODLE_TOKEN,
            "wsfunction": WS_FUNCTION,
            "moodlewsrestformat": "json"
        }
        data = {
            "enrolments[0][roleid]": ROLEID,
            "enrolments[0][userid]": USERID,
            "enrolments[0][courseid]": COURSEID,
            "enrolments[0][timestart]": TIMESTART,
            "enrolments[0][timeend]": TIMEEND
        }
        response = requests.post(url, params=params, data=data)
        response_dict = response.json()

        if response_dict is None:
            raise HTTPException(status_code=200, detail=HTTP_MESSAGES['OK'])
        if 'message' in response_dict:
            if response_dict['message'] == 'Detectado un error de codificación, debe ser corregido por un programador: User ID does not exist or is deleted!':
                raise HTTPException(status_code=400, detail=HTTP_MESSAGES['USER_NO_EXISTE'])
            if response_dict['message'] == 'Detectado valor de parámetro no válido':
                raise HTTPException(status_code=400, detail=HTTP_MESSAGES['COURSE_NO_EXISTE'])
        if 'exception' in response_dict and response_dict['exception'] == 'moodle_exception':
            raise HTTPException(status_code=400, detail=HTTP_MESSAGES['NO_MATRICULA_MANUAL'])

        results.append(response_dict)

    return {"results": results}