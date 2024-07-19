import os
from fastapi import FastAPI, APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import pandas as pd
from datetime import datetime

validacion_inicial_file_path = 'temp_files/validacion_inicial.xlsx'
validacion_cursos_certificado_router_prueba = APIRouter()

def get_database_url(user: str, password: str, host: str, port: str, db_name: str) -> str:
    password_encoded = quote_plus(password)
    return f"mysql+mysqlconnector://{user}:{password_encoded}@{host}:{port}/{db_name}"

def estudiantes_matriculados_con_certificados(cursos: list, usuario: str, contrasena: str, host: str, port: str, nombre_base_datos: str) -> pd.DataFrame:
    """
    Retorna la lista de estudiantes matriculados en varios cursos específicos que han obtenido certificados.
    """
    database_url = get_database_url(usuario, contrasena, host, port, nombre_base_datos)
    engine = create_engine(database_url)

    cursos_str = ','.join([f"'{curso.strip()}'" for curso in cursos])
    consulta_sql = text(f"""
        SELECT DISTINCT
            c.shortname as CourseShortName,
            c.fullname as CourseFullName,
            u.username as UserCedula,
            u.firstname as UserNombre,
            u.lastname as UserApellido,
            FROM_UNIXTIME(ccei.timecreated) as CertificadoFechaEmision,
            ccei.code as CertificadoCodigo
        FROM
            mdl_course_modules as cm
            LEFT JOIN mdl_modules as m ON (cm.module=m.id)
            LEFT JOIN mdl_course as c ON (cm.course=c.id)
            LEFT JOIN mdl_course_categories as cc ON (c.category=cc.id)
            LEFT JOIN mdl_customcert as cce ON (cm.instance=cce.id) and (c.id=cce.course)
            LEFT JOIN mdl_customcert_issues as ccei ON (ccei.customcertid=cce.id)
            LEFT JOIN mdl_user as u ON (ccei.userid=u.id)
        WHERE
            (m.name='customcert') AND (cc.visible>=0) AND
            (u.username REGEXP '^[0-9]+$') AND
            c.shortname IN ({cursos_str})
        ORDER BY cc.name, c.shortname;
    """)
    with engine.connect() as connection:
        result = connection.execute(consulta_sql)
        rows = result.fetchall()
        column_names = result.keys()

    if not rows:
        return pd.DataFrame()

    result_dicts = [
        dict(zip(column_names, row))
        for row in rows
    ]

    for row_dict in result_dicts:
        if isinstance(row_dict['CertificadoFechaEmision'], datetime):
            row_dict['CertificadoFechaEmision'] = row_dict['CertificadoFechaEmision'].strftime('%Y-%m-%d %H:%M:%S')

    return pd.DataFrame(result_dicts)

def validar_existencia_certificado_cursos(datos: pd.DataFrame, usuario: str, contrasena: str, host: str, port: str, nombre_base_datos: str) -> pd.DataFrame:
    """
    Valida la existencia de certificados para varios cursos específicos y retorna un DataFrame con los resultados.
    """
    datos['IDENTIFICACION'] = datos['IDENTIFICACION'].astype(str)
    datos['NOMBRE_CORTO_CURSO'] = datos['NOMBRE_CORTO_CURSO'].astype(str)

    cursos_unicos = datos['NOMBRE_CORTO_CURSO'].unique().tolist()
    cursos_certificado = estudiantes_matriculados_con_certificados(cursos_unicos, usuario, contrasena, host, port, nombre_base_datos)
    
    if cursos_certificado.empty:
        return pd.DataFrame()

    expected_columns = ['UserCedula', 'CourseShortName', 'CertificadoFechaEmision']
    for col in expected_columns:
        if col not in cursos_certificado.columns:
            raise KeyError(f"Column '{col}' not found in the result from the database.")

    cursos_certificado = cursos_certificado.dropna(subset=["UserCedula"])
    cursos_certificado['UserCedula'] = cursos_certificado['UserCedula'].astype(str)
    cursos_certificado['CourseShortName'] = cursos_certificado['CourseShortName'].astype(str)

    resultado = pd.merge(datos, cursos_certificado, left_on=['IDENTIFICACION', 'NOMBRE_CORTO_CURSO'], right_on=['UserCedula', 'CourseShortName'], how='left')
    resultado['ADVERTENCIA_CURSO_CULMINADO'] = resultado.apply(
        lambda row: f"{row['CourseShortName']},{row['UserCedula']},{row['CertificadoFechaEmision']}" 
        if pd.notna(row['UserCedula']) else 'NO', axis=1
    )

    return resultado

@validacion_cursos_certificado_router_prueba.post("/validar_cursos_certificado/", tags=['Cursos'])
async def validate_courses(usuario: str, contrasena: str, host: str, port: str, nombre_base_datos: str):
    try:
        if not os.path.exists(validacion_inicial_file_path):
            raise HTTPException(status_code=404, detail="El archivo de validación no se encontró.")
        
        validated_df = pd.read_excel(validacion_inicial_file_path)
        if validated_df.empty:
            return PlainTextResponse(content="El archivo de validación está vacío.")

        datos = validar_existencia_certificado_cursos(validated_df, usuario, contrasena, host, port, nombre_base_datos)
        datos.drop(columns=['CourseFullName', 'UserNombre', 'UserApellido', 'CertificadoFechaEmision', 'CertificadoCodigo','CourseShortName','UserCedula'], inplace=True)
        datos.to_excel(validacion_inicial_file_path, index=False)

        si_rows_count = (datos['ADVERTENCIA_CURSO_CULMINADO'] != 'NO').sum()
        no_rows_count = (datos['ADVERTENCIA_CURSO_CULMINADO'] == 'NO').sum()

        message = (
            f"VALIDACIÓN DE CERTIFICADOS DE CURSOS: \n"
            f"{no_rows_count} MATRICULAS VALIDAS \n"
            f"{si_rows_count} MATRICULAS REDUNDANTES \n"
        ) if not datos.empty else "No se encontraron datos para validar."

        return PlainTextResponse(content=message)
    except KeyError as e:
        raise HTTPException(status_code=500, detail=f"Error durante la validación de cursos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante la validación de cursos: {str(e)}")





