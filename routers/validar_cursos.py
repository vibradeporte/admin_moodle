from fastapi import FastAPI, APIRouter, HTTPException
from sqlalchemy import create_engine
import pandas as pd
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
import mysql.connector

# Create APIRouter instance for validacion_cursos
validacion_cursos = APIRouter()

# Load environment variables from .env file
load_dotenv()

# Load environment variables
usuario = os.getenv("USER_DB_UL")
contrasena = os.getenv("PASS_DB_UL")
host = os.getenv("HOST_DB")
nombre_base_datos = os.getenv("NAME_DB_UL")

# Debugging: Print environment variables to check if they are loaded correctly
print(f"Usuario: {usuario}")
print(f"Contrasena: {contrasena}")
print(f"Host: {host}")
print(f"Nombre Base Datos: {nombre_base_datos}")

# Check if any of the environment variables are None
if None in [usuario, contrasena, host, nombre_base_datos]:
    raise ValueError("One or more environment variables are missing or not set correctly.")

# Encode the password for URL
contrasena_codificada = quote_plus(contrasena)
DATABASE_URL = f"mysql+mysqlconnector://{usuario}:{contrasena_codificada}@{host}/{nombre_base_datos}"

# Define file paths
cursos_file_path = 'temp_files/registros_cursos.csv'
validacion_inicial_file_path = 'temp_files/validacion_inicial.xlsx'
cursos_certificados_file_path = 'temp_files/registros_cursos_certificados.csv'

# SQL queries
consulta_sql_traer_cursos = """
SELECT
c.shortname as CourseShortName,
c.fullname as fullname,
c.visible as visible
FROM
mdl_course as c
JOIN mdl_course_categories as ccat ON (c.category=ccat.id)
WHERE
(c.visible=1) AND (ccat.visible=1)
ORDER BY
c.fullname;
"""

consulta_sql_traer_cursos_certificados = """
SELECT DISTINCT
    c.shortname AS CourseShortName,
    c.fullname AS CourseFullName,
    u.username AS UserCedula,
    u.firstname AS UserNombre,
    u.lastname AS UserApellido,
    FROM_UNIXTIME(ccei.timecreated) AS CertificadoFechaEmision,
    ccei.code AS CertificadoCodigo
FROM
    mdl_course_modules AS cm
    LEFT JOIN mdl_modules AS m ON cm.module = m.id
    LEFT JOIN mdl_course AS c ON cm.course = c.id
    LEFT JOIN mdl_course_categories AS cc ON c.category = cc.id
    LEFT JOIN mdl_customcert AS cce ON cm.instance = cce.id AND c.id = cce.course
    LEFT JOIN mdl_customcert_issues AS ccei ON ccei.customcertid = cce.id
    LEFT JOIN mdl_user AS u ON ccei.userid = u.id
ORDER BY
    cc.name, c.shortname;
"""

def obtener_registros_y_guardar_como_csv(consulta, file_path):
    try:
        engine = create_engine(DATABASE_URL)
        df = pd.read_sql(consulta, engine)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        df.to_csv(file_path, index=False, encoding='utf-8')
        print(f"Los registros se han guardado correctamente en {file_path}.")
    except Exception as e:
        print(f"Error al obtener los registros: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener los registros: {e}")

def validar_cursos(datos):
    try:
        print(f"Reading cursos from: {cursos_file_path}")
        cursos_existentes = pd.read_csv(cursos_file_path)
        print(f"Cursos existentes: {cursos_existentes.head()}")

        existing_courses = cursos_existentes['CourseShortName'].tolist()
        datos['nombre_De_Curso_Invalido'] = datos['NOMBRE_CORTO_CURSO'].apply(
            lambda x: "NO" if x in existing_courses else "SI"
        )
        return datos
    except Exception as e:
        print(f"Error al validar cursos: {e}")
        raise HTTPException(status_code=500, detail=f"Error al validar cursos: {e}")

def validar_existencia_certificado_cursos(datos):
    try:
        print(f"Reading cursos certificados from: {cursos_certificados_file_path}")
        cursos_certificado = pd.read_csv(cursos_certificados_file_path)
        print(f"Cursos certificados: {cursos_certificado.head()}")

        cursos_certificado = cursos_certificado.dropna(subset=["UserCedula"])
        
        datos['IDENTIFICACION'] = datos['IDENTIFICACION'].astype(str)
        datos['NOMBRE_CORTO_CURSO'] = datos['NOMBRE_CORTO_CURSO'].astype(str)
        cursos_certificado['UserCedula'] = cursos_certificado['UserCedula'].astype(str)
        cursos_certificado['CourseShortName'] = cursos_certificado['CourseShortName'].astype(str)
        
        resultado = pd.merge(datos, cursos_certificado, 
                             left_on=['IDENTIFICACION', 'NOMBRE_CORTO_CURSO'], 
                             right_on=['UserCedula', 'CourseShortName'], 
                             how='left')
        
        resultado['ADVERTENCIA_CURSO_CULMINADO'] = resultado.apply(
            lambda row: f"{row['CourseShortName']},{row['UserCedula']},{row['CertificadoFechaEmision']}" 
                        if not pd.isna(row['UserCedula']) else 'NO', axis=1)
        resultado = resultado.drop(columns=['CourseShortName', 'UserCedula', 'CertificadoFechaEmision', "CourseFullName", "UserNombre", "UserApellido", "CertificadoCodigo"])
        
        return resultado
    except Exception as e:
        print(f"Error al validar existencia de certificado de cursos: {e}")
        raise HTTPException(status_code=500, detail=f"Error al validar existencia de certificado de cursos: {e}")

@validacion_cursos.post("/validar_cursos/", tags=['Moodle'])
async def validate_courses():
    try:
        #obtener_registros_y_guardar_como_csv(consulta_sql_traer_cursos, cursos_file_path)
        #obtener_registros_y_guardar_como_csv(consulta_sql_traer_cursos_certificados, cursos_certificados_file_path)
        
        print(f"Reading initial validation data from: {validacion_inicial_file_path}")
        validated_df = pd.read_excel(validacion_inicial_file_path)
        print(f"Initial validation data: {validated_df.head()}")

        # Validar cursos
        validated_df_result = validar_cursos(validated_df)
        validated_df_result = validar_existencia_certificado_cursos(validated_df_result)

        # Guardar resultados
        validated_df_result.to_excel(validacion_inicial_file_path, index=False)
        result = validated_df_result.fillna("").replace([float("inf"), float("-inf")], "").to_dict(orient="records")

        return {"message": "Cursos validados correctamente", "validated_courses": result}
    except Exception as e:
        print(f"Error durante la validación de cursos: {e}")
        raise HTTPException(status_code=500, detail=f"Error durante la validación de cursos: {e}")
