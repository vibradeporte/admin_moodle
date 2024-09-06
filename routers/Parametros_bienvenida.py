import os
import pandas as pd
from fastapi import APIRouter, HTTPException
from sqlalchemy import create_engine, text
from datetime import timedelta
from typing import List, Dict
from utils import meses_espanol, construir_url_mysql

Bienvenida_wapp_estudiantes_router = APIRouter()

def obtener_plantillas_wapp(usuario: str, contrasena: str, host: str, port: str, nombre_base_datos: str) -> pd.DataFrame:
    df_estudiantes = pd.read_csv('temp_files/estudiantes_validados.csv')
    cursos = df_estudiantes['NOMBRE_CORTO_CURSO'].unique().tolist()
    database_url = construir_url_mysql(usuario, contrasena, host, port, nombre_base_datos)
    engine = create_engine(database_url)
    cursos_str = ','.join([f"'{curso.strip()}'" for curso in cursos])

    consulta_sql = text(f"""
                SELECT DISTINCT
                    c.id AS CourseId,
                    c.shortname as NOMBRE_CORTO_CURSO,
                    SUBSTRING(
                        c.idnumber, 
                        LOCATE(':', c.idnumber, LOCATE('PWH:', c.idnumber)) + 1, 
                        LOCATE('>', c.idnumber, LOCATE('PWH:', c.idnumber)) - LOCATE(':', c.idnumber, LOCATE('PWH:', c.idnumber)) - 1
                    ) AS plantilla_whatsapp
                FROM
                    mdl_course AS c
                WHERE
                    c.shortname IN ({cursos_str})
                ORDER BY
                    c.shortname;
        """)

    try:
        with engine.connect() as connection:
            result = connection.execute(consulta_sql)
            rows = result.fetchall()
            column_names = result.keys()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de conexión a la base de datos: {str(e)}")

    if not rows:
        return pd.DataFrame()

    # Convertir los resultados en un DataFrame
    result_dicts = [dict(zip(column_names, row)) for row in rows]
    df_plantilla = pd.DataFrame(result_dicts)

    # Guardar en CSV si es necesario
    temp_dir = 'temp_files'
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    df_plantilla.to_csv(f'{temp_dir}/plantillas_wapp.csv', index=False)

    return df_plantilla


@Bienvenida_wapp_estudiantes_router.post("/Estructura_Wapp_Bienvenida/", tags=['Whatsapp'])
async def csv_to_json(usuario: str, contrasena: str, host: str, port: str, nombre_base_datos: str) -> List[Dict]:
    # Leer y limpiar el archivo CSV
    df_estudiantes = pd.read_csv('temp_files/estudiantes_validados.csv')
    df_plantilla_wapp = obtener_plantillas_wapp(usuario, contrasena, host, port, nombre_base_datos)
    df = pd.merge(df_estudiantes, df_plantilla_wapp[['NOMBRE_CORTO_CURSO', 'plantilla_whatsapp']], on='NOMBRE_CORTO_CURSO', how='left')
    # Filtrar los registros con números de teléfono válidos
    df = df.dropna(subset=['phone1'])
    df = df[df['phone1'].apply(lambda x: str(x).isdigit() and x not in ["none", "null"])]

    # Convertir las columnas timestart y timeend a fechas
    df['timeend'] = pd.to_datetime(df['timeend'], unit='s')

    # Calcular el día anterior al timeend
    df['dia_anterior'] = df['timeend'] - timedelta(days=1)

    # Crear el formato de fecha en español para el día anterior
    df['timeend_str'] = df['dia_anterior'].apply(
        lambda x: f"{x.day} de {meses_espanol[x.month]} de {x.year} a las 11:59 PM hora colombiana"
    )

    # Procesar los datos para generar el JSON
    data = []
    for _, row in df.iterrows():
        parametros = [
            row['firstname'],
            row['NOMBRE_LARGO_CURSO'],
            row['timeend_str'],
            str(row['password']) # Manejo de contraseñas faltantes
        ]
        item = {
            "numero": str(row['phone1']),
            "plantilla": row['plantilla_whatsapp'].strip(),
            "parametros": parametros
        }
        data.append(item)

    return data
