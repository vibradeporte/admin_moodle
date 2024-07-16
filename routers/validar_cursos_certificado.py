import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import pandas as pd
from datetime import datetime

# Cargar variables de entorno
load_dotenv()
usuario = os.getenv("USER_DB_UL")
contrasena = os.getenv("PASS_DB_UL")
host = os.getenv("HOST_DB")
nombre_base_datos = os.getenv("NAME_DB_UL")

# Codificar la contraseña para la URL de conexión
contrasena_codificada = quote_plus(contrasena)
DATABASE_URL = f"mysql+mysqlconnector://{usuario}:{contrasena_codificada}@{host}/{nombre_base_datos}"
engine = create_engine(DATABASE_URL)

# Ruta para el archivo de validación inicial
validacion_inicial_file_path = 'temp_files/validacion_inicial.xlsx'
validacion_cursos_certificado_router_prueba = APIRouter()

def estudiantes_matriculados_con_certificados(cursos: list) -> pd.DataFrame:
    """
    Retorna la lista de estudiantes matriculados en varios cursos específicos que han obtenido certificados.
    """
    cursos_str = '/'.join([f"'{curso.strip()}'" for curso in cursos])
    print(f"Consulting courses: {cursos_str}")
    with engine.connect() as connection:
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
        result = connection.execute(consulta_sql)
        rows = result.fetchall()
        column_names = result.keys()

        if not rows:
            print("No data found for the specified courses.")
            return pd.DataFrame()

        result_dicts = [
            {
                **dict(zip(column_names, row)),
                'CertificadoFechaEmision': row['CertificadoFechaEmision'].strftime('%Y-%m-%d %H:%M:%S')
                if isinstance(row['CertificadoFechaEmision'], datetime) else row['CertificadoFechaEmision']
            }
            for row in rows
        ]

        df_result = pd.DataFrame(result_dicts)
        if 'UserCedula' not in df_result.columns:
            print("UserCedula column not found in the result DataFrame.")
        return df_result

def validar_existencia_certificado_cursos(datos: pd.DataFrame) -> pd.DataFrame:
    """
    Valida la existencia de certificados para varios cursos específicos y retorna un DataFrame con los resultados.
    """
    all_cursos_certificado = pd.DataFrame()

    datos['IDENTIFICACION'] = datos['IDENTIFICACION'].astype(str)
    datos['NOMBRE_CORTO_CURSO'] = datos['NOMBRE_CORTO_CURSO'].astype(str)

    cursos_unicos = datos['NOMBRE_CORTO_CURSO'].unique().tolist()
    print(f"Cursos únicos: {cursos_unicos}")
    cursos_certificado = estudiantes_matriculados_con_certificados(cursos_unicos)
    
    if cursos_certificado.empty:
        print("No certificates found for any course.")
    else:
        cursos_certificado = cursos_certificado.dropna(subset=["UserCedula"])
        cursos_certificado['UserCedula'] = cursos_certificado['UserCedula'].astype(str)
        cursos_certificado['CourseShortName'] = cursos_certificado['CourseShortName'].astype(str)
        all_cursos_certificado = pd.concat([all_cursos_certificado, cursos_certificado], ignore_index=True)

    if all_cursos_certificado.empty:
        print("All courses certificates DataFrame is empty.")
    else:
        print("All courses certificates DataFrame is not empty.")
        print(all_cursos_certificado.head())

    resultado = pd.merge(datos, all_cursos_certificado, left_on=['IDENTIFICACION', 'NOMBRE_CORTO_CURSO'], right_on=['UserCedula', 'CourseShortName'], how='left')
    resultado['ADVERTENCIA_CURSO_CULMINADO'] = resultado.apply(
        lambda row: f"{row['CourseShortName']},{row['UserCedula']},{row['CertificadoFechaEmision']}" 
        if pd.notna(row['UserCedula']) else 'NO', axis=1
    )

    return resultado

@validacion_cursos_certificado_router_prueba.post("/validar_cursos_certificado/", tags=['Cursos'])
async def validate_courses():
    try:
        # Verificar que la carpeta temp_files existe
        os.makedirs(os.path.dirname(validacion_inicial_file_path), exist_ok=True)

        validated_df = pd.read_excel(validacion_inicial_file_path)
        if validated_df.empty:
            return PlainTextResponse(content="El archivo de validación está vacío.")

        print("Validated DataFrame loaded successfully.")
        print(validated_df.head())

        datos = validar_existencia_certificado_cursos(validated_df)

        datos.to_excel(validacion_inicial_file_path, index=False)

        si_rows_count = (datos['ADVERTENCIA_CURSO_CULMINADO'] != 'NO').sum()
        no_rows_count = (datos['ADVERTENCIA_CURSO_CULMINADO'] == 'NO').sum()

        message = (
            f"VALIDACIÓN DE CERTIFICADOS DE CURSOS: \n"
            f"{no_rows_count} MATRICULAS VALIDAS \n"
            f"{si_rows_count} MATRICULAS REDUNDANTES \n"
        ) if not datos.empty else "No se encontraron datos para validar."

        return PlainTextResponse(content=message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante la validación de cursos: {str(e)}")


