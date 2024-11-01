import os
from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import pandas as pd
from datetime import datetime
from jwt_manager import JWTBearer

validacion_inicial_file_path = 'temp_files/validacion_inicial.xlsx'

validacion_cursos_certificado_router_prueba = APIRouter()

def get_database_url(user: str, password: str, host: str, port: str, db_name: str) -> str:
    """
    Genera la URL de conexión para la base de datos.

    :param user: Usuario de la base de datos.
    :param password: Contraseña del usuario de la base de datos.
    :param host: Host de la base de datos.
    :param port: Puerto de conexión a la base de datos.
    :param db_name: Nombre de la base de datos.
    :return: URL de conexión para la base de datos.
    """
    password_encoded = quote_plus(password)
    return f"mysql+mysqlconnector://{user}:{password_encoded}@{host}:{port}/{db_name}"

def obtener_estudiantes_matriculados_con_certificados(cursos: list, usuario: str, contrasena: str, host: str, port: str, nombre_base_datos: str) -> pd.DataFrame:
    """
    Obtiene información de los estudiantes matriculados con certificados emitidos para los cursos especificados.

    :param cursos: Lista de cursos para verificar los certificados.
    :param usuario: Usuario de la base de datos.
    :param contrasena: Contraseña del usuario de la base de datos.
    :param host: Host de la base de datos.
    :param port: Puerto de conexión a la base de datos.
    :param nombre_base_datos: Nombre de la base de datos.
    :return: DataFrame con la información de los estudiantes y sus certificados.
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

    try:
        with engine.connect() as connection:
            result = connection.execute(consulta_sql)
            rows = result.fetchall()
            column_names = result.keys()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos.")

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
    Valida la existencia de certificados para los cursos y estudiantes especificados.

    :param datos: DataFrame con los datos de los estudiantes y cursos.
    :param usuario: Usuario de la base de datos.
    :param contrasena: Contraseña del usuario de la base de datos.
    :param host: Host de la base de datos.
    :param port: Puerto de conexión a la base de datos.
    :param nombre_base_datos: Nombre de la base de datos.
    :return: DataFrame actualizado con la columna 'ADVERTENCIA_CURSO_CULMINADO'.
    """
    datos['IDENTIFICACION'] = datos['IDENTIFICACION'].astype(str)
    datos['NOMBRE_CORTO_CURSO'] = datos['NOMBRE_CORTO_CURSO'].astype(str)

    cursos_unicos = datos['NOMBRE_CORTO_CURSO'].unique().tolist()
    cursos_certificado_df = obtener_estudiantes_matriculados_con_certificados(cursos_unicos, usuario, contrasena, host, port, nombre_base_datos)
    
    if cursos_certificado_df.empty:
        return datos.assign(ADVERTENCIA_CURSO_CULMINADO='NO')

    expected_columns = ['UserCedula', 'CourseShortName', 'CertificadoFechaEmision']
    for col in expected_columns:
        if col not in cursos_certificado_df.columns:
            raise HTTPException(status_code=500, detail=f"La columna '{col}' no se encontró en el resultado de la base de datos.")

    cursos_certificado_df = cursos_certificado_df.dropna(subset=["UserCedula"])
    cursos_certificado_df['UserCedula'] = cursos_certificado_df['UserCedula'].astype(str)
    cursos_certificado_df['CourseShortName'] = cursos_certificado_df['CourseShortName'].astype(str)

    resultado = pd.merge(datos, cursos_certificado_df, left_on=['IDENTIFICACION', 'NOMBRE_CORTO_CURSO'], right_on=['UserCedula', 'CourseShortName'], how='left')
    resultado['ADVERTENCIA_CURSO_CULMINADO'] = resultado.apply(
        lambda row: f"{row['CourseShortName']},{row['UserCedula']},{row['CertificadoFechaEmision']}" 
        if pd.notna(row['UserCedula']) else 'NO', axis=1
    )

    return resultado

@validacion_cursos_certificado_router_prueba.post("/validar_cursos_certificado/", tags=['Cursos'], dependencies=[Depends(JWTBearer())])
async def validar_cursos_certificado(usuario: str, contrasena: str, host: str, port: str, nombre_base_datos: str):
    """
    Valida la existencia de certificados para los cursos y estudiantes especificados.

    :param usuario: Usuario de la base de datos.
    :param contrasena: Contraseña del usuario de la base de datos.
    :param host: Host de la base de datos.
    :param port: Puerto de conexión a la base de datos.
    :param nombre_base_datos: Nombre de la base de datos.
    :return: JSONResponse con el resultado de la validación.
    """
    try:
        if not os.path.exists(validacion_inicial_file_path):
            raise HTTPException(status_code=404, detail="El archivo de validación no se encontró.")
        
        validated_df = pd.read_excel(validacion_inicial_file_path)

        datos_actualizados = validar_existencia_certificado_cursos(validated_df, usuario, contrasena, host, port, nombre_base_datos)
        datos_actualizados.drop(columns=['CourseFullName', 'UserNombre', 'UserApellido', 'CertificadoFechaEmision', 'CertificadoCodigo', 'CourseShortName', 'UserCedula'], inplace=True, errors='ignore')
        datos_actualizados.to_excel(validacion_inicial_file_path, index=False)

        si_rows_count = (datos_actualizados['ADVERTENCIA_CURSO_CULMINADO'] != 'NO').sum()
        no_rows_count = (datos_actualizados['ADVERTENCIA_CURSO_CULMINADO'] == 'NO').sum()

        if not datos_actualizados.empty:
            message = {
                "message": "Validación de Certificados de Cursos",
                "matriculas_validas": int(no_rows_count),
                "matriculas_redundantes": int(si_rows_count)
            }
        else:
            message = {"message": "No se encontraron datos para validar."}

        return JSONResponse(content=message)
    except KeyError as e:
        return JSONResponse(content={"error": f"Error durante la validación de cursos: {str(e)}"}, status_code=500)
    except Exception as e:
        return JSONResponse(content={"error": f"Error durante la validación de cursos: {str(e)}"}, status_code=500)







