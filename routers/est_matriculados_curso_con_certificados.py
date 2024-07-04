import os
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from return_codes import *

# Longitud máxima del nombre corto del curso
max_length_courseshortname = 37

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

# Crear el enrutador de FastAPI
est_matriculados_curso_con_certificados_router = APIRouter()


@est_matriculados_curso_con_certificados_router.get("/estudiantes_matriculados_en_curso_con_certificados", tags=['Funciones_Moodle'], status_code=200)
def estudiantes_matriculados_con_certificados(curso: str = Query(max_length=max_length_courseshortname)):
    """
    ## **Descripción:**
    Esta función retorna la lista de estudiantes matriculados en un curso en específico que han obtenido certificados.

    ## **Parámetros obligatorios:**
        - curso -> Nombre corto del curso.
        
    ## **Códigos retornados:**
        - 200 -> Registros encontrados.
        - 452 -> No se encontró información sobre ese curso en la base de datos.

    ## **Campos retornados:**
        - CourseShortName -> Nombre corto del curso.
        - CourseFullName -> Nombre largo del curso.
        - UserCedula -> Cédula del usuario.
        - UserNombre -> Nombres del usuario.
        - UserApellido -> Apellidos del usuario.
        - CertificadoFechaEmision -> Fecha de emisión del certificado.
        - CertificadoCodigo -> código del certificado.
    """
    with engine.connect() as connection:
        consulta_sql = text("""
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
                c.shortname IN (:curso)

                ORDER BY cc.name, c.shortname;
        """).params(curso=curso)
        result = connection.execute(consulta_sql)
        rows = result.fetchall()
        column_names = result.keys()

        # Convertir las filas a una lista de diccionarios, manejando la conversión de datetime
        result_dicts = []
        for row in rows:
            row_dict = dict(zip(column_names, row))
            # Convertir datetime a string
            if 'CertificadoFechaEmision' in row_dict and isinstance(row_dict['CertificadoFechaEmision'], datetime):
                row_dict['CertificadoFechaEmision'] = row_dict['CertificadoFechaEmision'].strftime('%Y-%m-%d %H:%M:%S')
            result_dicts.append(row_dict)

        if result_dicts:
            df = pd.DataFrame(result_dicts)
            return JSONResponse(content=df.to_dict(orient="records"))
        else:
            codigo = SIN_INFORMACION
            mensaje = HTTP_MESSAGES.get(codigo)
            raise HTTPException(codigo, mensaje)

        
