from fastapi import APIRouter, HTTPException, FastAPI
from fastapi.responses import JSONResponse
import pandas as pd
from sqlalchemy import create_engine, text
import os
from datetime import datetime
from urllib.parse import quote_plus

conseguir_id_grupo = APIRouter()

def get_database_url(user: str, password: str, host: str, port: str, db_name: str) -> str:
    password_encoded = quote_plus(password)
    return f"mysql+mysqlconnector://{user}:{password_encoded}@{host}:{port}/{db_name}"

@conseguir_id_grupo.post("/conseguir_id_grupo/", tags=['Moodle'], status_code=200)
async def id_grupo(usuario: str, contrasena: str, host: str, port: str, nombre_base_datos: str):
    database_url = get_database_url(usuario, contrasena, host, port, nombre_base_datos)
    engine = create_engine(database_url)
    
    file_path = 'temp_files/estudiantes_validados.csv'
    
    # Check if the file exists
    if not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="File not found")
    
    try:
        df = pd.read_csv(file_path)
        df = df.astype(str)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid file format or content")

    if 'username' not in df.columns or 'NOMBRE_CORTO_CURSO' not in df.columns:
        raise HTTPException(status_code=400, detail="Missing 'username' or 'NOMBRE_CORTO_CURSO' column in CSV")

    ids_curso = df['NOMBRE_CORTO_CURSO'].unique().tolist()
    ids_str = ', '.join([f':NOMBRE_CORTO_CURSO{i}' for i in range(len(ids_curso))])
    

    fecha = datetime.now().strftime('%B_%d_%Y')

# Diccionario para traducir meses de inglés a español
    meses_en_espanol = {
        'January': 'Enero',
        'February': 'Febrero',
        'March': 'Marzo',
        'April': 'Abril',
        'May': 'Mayo',
        'June': 'Junio',
        'July': 'Julio',
        'August': 'Agosto',
        'September': 'Septiembre',
        'October': 'Octubre',
        'November': 'Noviembre',
        'December': 'Diciembre'
    }

    # Extrae el nombre del mes en inglés
    mes_ingles = datetime.now().strftime('%B')

    # Reemplaza el mes en inglés con el equivalente en español
    today_str = fecha.replace(mes_ingles, meses_en_espanol[mes_ingles])

    consulta_sql = text(f"""
        SELECT g.id AS groupid, g.name AS groupname, c.id AS courseid, c.shortname AS coursename
        FROM mdl_groups g
        JOIN mdl_course c ON g.courseid = c.id
        WHERE c.shortname IN ({ids_str})
        AND g.name = :today
        ORDER BY c.id, g.id;
    """)
    
    parameters = {f'NOMBRE_CORTO_CURSO{i}': ids_curso[i] for i in range(len(ids_curso))}
    parameters['today'] = today_str

    group_ids = []
    try:
        with engine.connect() as connection:
            result = connection.execute(consulta_sql, parameters)
            rows = result.fetchall()
            keys = list(result.keys())
            course_groups = {row[keys.index('coursename')]: row[keys.index('groupid')] for row in rows}
            for curso in df['NOMBRE_CORTO_CURSO']:
                group_ids.append(course_groups.get(curso, ''))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

    df['groupid'] = group_ids

    try:
        df_cleaned = df.replace({pd.NA: None, pd.NaT: None, float('inf'): None, float('-inf'): None})
        df_cleaned.to_csv(file_path, index=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clean and save the DataFrame: {str(e)}")

    try:
        json_response = df_cleaned.to_dict(orient='records')
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Error converting DataFrame to JSON: {str(e)}")

    return JSONResponse(content=json_response)


