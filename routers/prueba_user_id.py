from fastapi import APIRouter, HTTPException, UploadFile, FastAPI,Depends
from fastapi.responses import JSONResponse
from io import BytesIO
import pandas as pd
from utils import construir_url_mysql
from sqlalchemy import create_engine, text
from jwt_manager import JWTBearer
import os
import re

prueba_conseguir_id = APIRouter()

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


@prueba_conseguir_id.post("/prueba_conseguir_id/", tags=['Moodle'], status_code=200,dependencies=[Depends(JWTBearer())])
async def id_estudiante(usuario: str,contrasena: str,host: str,port: str,nombre_base_datos: str):
    database_url = construir_url_mysql(usuario, contrasena, host, port, nombre_base_datos)
    engine = create_engine(database_url)

    try:
        df = pd.read_csv('temp_files/estudiantes_validados.csv')
        df['username'] = df['username'].apply(lambda x: str(x).replace('.0', '') if '.0' in str(x) else str(x))
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
    df_cleaned = df.replace({pd.NA: None, pd.NaT: None, float('inf'): None, float('-inf'): None})
    df.to_csv('temp_files/estudiantes_validados.csv', index=False)
    try:
        json_response = df_cleaned.to_dict(orient='records')
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Error converting DataFrame to JSON: {str(e)}")

    return JSONResponse(content=json_response)

