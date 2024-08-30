from fastapi import FastAPI, APIRouter, HTTPException
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import pandas as pd
from datetime import datetime , timedelta
import html
import re
Bienvenida_correo_estudiantes_router = APIRouter()

def get_database_url(user: str, password: str, host: str, port: str, db_name: str) -> str:
    password_encoded = quote_plus(password)
    return f"mysql+mysqlconnector://{user}:{password_encoded}@{host}:{port}/{db_name}"

def obtener_plantillas_correos(cursos: list, usuario: str, contrasena: str, host: str, port: str, nombre_base_datos: str) -> pd.DataFrame:
    database_url = get_database_url(usuario, contrasena, host, port, nombre_base_datos)
    engine = create_engine(database_url)
    cursos_str = ','.join([f"'{curso.strip()}'" for curso in cursos])

    consulta_sql = text(f"""
        SELECT 
            shortname as NOMBRE_CORTO_CURSO,
            summary as plantilla_Html
        FROM mdl_course 
        WHERE 
            shortname IN ({cursos_str})
            AND summaryformat = 1;
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
    df_plantilla.to_csv('temp_files/plantillas_correos.csv', index=False)

    return df_plantilla


def transformar_datos_bienvenida(datos: pd.DataFrame, plantilla: pd.DataFrame, correo_matriculas: str, correo_envio_bienvenidas: str):
    meses_espanol = {
        1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
        5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
        9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
    }
    
    estructura_deseada = []

    # Unir los datos de los estudiantes con las plantillas de correo
    datos = datos.merge(plantilla, on='NOMBRE_CORTO_CURSO', how='left')
    
    for _, fila in datos.iterrows():
        # Verifica que la plantilla HTML no esté vacía
        if pd.notna(fila['plantilla_Html']):
            try:
                # Convertir timestamp Unix a datetime
                timestart_dt = datetime.fromtimestamp(fila['timestart'])
                timeend_dt = datetime.fromtimestamp(fila['timeend'])
                dia_anterior = timeend_dt - timedelta(days=1)
                
                # Formatear las fechas con el nombre del mes en español
                timeend_str = f"{dia_anterior.day} de {meses_espanol[dia_anterior.month]} de {dia_anterior.year} 11:59 PM"

                
                # Calcular enrolperiod (diferencia en días)
                enrolperiod = (timeend_dt - timestart_dt).days
                
            except (ValueError, TypeError, OSError):  # Capturar cualquier error en la conversión
                timeend_str = "Fecha no disponible"
                enrolperiod = "Periodo no disponible"

            # Rellenar la plantilla con los valores de la fila
            html_content_with_entities = fila['plantilla_Html'].format(
                firstname=fila['firstname'],
                lastname=fila['lastname'],
                username=fila['username'],
                timestart_dt=timestart_dt,
                timeend=timeend_str,
                enrolperiod=enrolperiod  # Usar el valor calculado de enrolperiod
            )

            # Convertir las entidades HTML a caracteres
            html_content = html.unescape(html_content_with_entities)

            # Buscar el contenido dentro de los comentarios
            match = re.search(r'<!--(.*?)-->', html_content, re.DOTALL)
            if match:
                # Extraer el contenido dentro de los comentarios
                html_content = match.group(1).strip()

            # Remover los comentarios HTML
            html_content = html_content.replace("<!--", "").replace("-->", "").strip()

            # Crear el diccionario con la estructura deseada
            item = {
                "from_e": correo_envio_bienvenidas,
                "to": fila['email'],
                "subject": f"Bienvenida al Curso {fila['NOMBRE_LARGO_CURSO']}",
                "cc": correo_matriculas,  # Valor predeterminado en caso de que no haya 'CORREO_SOLICITANTE'
                "html_content": html_content,
                "content": ""
            }

            # Verifica si existe 'CORREO_SOLICITANTE' y no es nulo
            if pd.notna(fila.get('CORREO_SOLICITANTE')):
                item['cc'] = f"{fila['CORREO_SOLICITANTE']}, {correo_matriculas}"

            # Añadir a la lista estructura_deseada
            estructura_deseada.append(item)

    return estructura_deseada





@Bienvenida_correo_estudiantes_router.post("/Estructura_Correo_Bienvenida/", tags=['Correo'])
async def Estructura_Correo_Bienvenida(usuario: str, contrasena: str, host: str, port: str, nombre_base_datos: str, correo_matriculas: str, correo_envio_bienvenidas: str):
    try:
        df = pd.read_csv('temp_files/estudiantes_validados.csv')
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="El archivo 'estudiantes_validados.csv' no fue encontrado.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer el archivo CSV: {str(e)}")

    cursos_unicos = df['NOMBRE_CORTO_CURSO'].unique().tolist()
    print(df)
    try:
        df_plantilla = obtener_plantillas_correos(cursos_unicos, usuario, contrasena, host, port, nombre_base_datos)
    except HTTPException as e:
        raise e
    
    if df_plantilla.empty:
        raise HTTPException(status_code=404, detail="No se encontraron plantillas de correo para los cursos especificados.")
    plantilla = pd.read_csv('temp_files/plantillas_correos.csv')
    # Transformar los datos para el envío de correos
    estructura_correo = transformar_datos_bienvenida(df, plantilla, correo_matriculas, correo_envio_bienvenidas)
    
    return estructura_correo
