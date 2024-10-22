from fastapi import FastAPI, APIRouter, HTTPException
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import pandas as pd
from datetime import datetime , timedelta
import html
import re
Bienvenida_correo_estudiantes_router = APIRouter()

def transformar_datos_bienvenida(datos: pd.DataFrame, plantilla: pd.DataFrame, correo_matriculas: str, correo_envio_bienvenidas: str, correo_envio_copia_matriculas: str):
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

                # Verificar si 'DIAS_INFORMADOS_AL_ESTUDIANTE' es distinto de "SIN DIAS"
                if pd.notna(fila.get('DIAS_INFORMADOS_AL_ESTUDIANTE')) and fila['DIAS_INFORMADOS_AL_ESTUDIANTE'] != 'SIN DIAS' :
                    dias_informados = int(fila['DIAS_INFORMADOS_AL_ESTUDIANTE'])  # Asegúrate de que es un entero
                    print(f"Sumando {dias_informados} días informados al estudiante")  # LOG DE VERIFICACIÓN
                    # Usar la fecha actual y sumarle los días informados al estudiante
                    timeend_dt = datetime.now() + timedelta(days=dias_informados)
                else:
                    # Usar 'timeend' de la fila si no hay 'DIAS_INFORMADOS_AL_ESTUDIANTE'
                    timeend_dt = datetime.fromtimestamp(fila['timeend'])

                # Calcular la fecha final
                dia_anterior = timeend_dt - timedelta(days=1)
                
                # Formatear las fechas con el nombre del mes en español
                timeend_str = f"{dia_anterior.day} de {meses_espanol[dia_anterior.month]} de {dia_anterior.year} a las 11:59 PM hora colombiana"
                print(f"Fecha calculada: {timeend_str}")  # LOG DE VERIFICACIÓN

                # Calcular enrolperiod (diferencia en días)
                enrolperiod = (timeend_dt - timestart_dt).days

            except (ValueError, TypeError, OSError) as e:  # Capturar cualquier error en la conversión
                print(f"Error en el cálculo de fechas: {e}")  # LOG DE ERRORES
                timeend_str = "Fecha no disponible"
                enrolperiod = "Periodo no disponible"

            # Rellenar la plantilla con los valores de la fila
            html_content_with_entities = fila['plantilla_Html'].format(
                firstname=fila['firstname'],
                lastname=fila['lastname'],
                username=fila['username'],
                password=fila['password'],
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
                "cc": [correo_matriculas, correo_envio_copia_matriculas],  # Lista con valor predeterminado
                "html_content": html_content,
                "content": "",
                "send_time": fila['send_time']
            }

            # Verifica si existe 'CORREO_SOLICITANTE' y no es nulo
            if pd.notna(fila.get('CORREO_SOLICITANTE')):
                item['cc'].append(fila['CORREO_SOLICITANTE'])

            # Convertir la lista de correos en una cadena separada por comas
            item['cc'] = ', '.join(item['cc'])

            # Añadir a la lista estructura_deseada
            estructura_deseada.append(item)


    return estructura_deseada






@Bienvenida_correo_estudiantes_router.post("/Estructura_Correo_Bienvenida/", tags=['Correo'])
async def Estructura_Correo_Bienvenida(correo_matriculas: str, correo_envio_bienvenidas: str,correo_envio_copia_matriculas: str):
    try:
        df = pd.read_csv('temp_files/estudiantes_validados.csv')
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="El archivo 'estudiantes_validados.csv' no fue encontrado.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer el archivo CSV: {str(e)}")

    cursos_unicos = df['NOMBRE_CORTO_CURSO'].unique().tolist()
    print(df)
    df_plantilla = pd.read_csv('temp_files/plantillas_correos.csv')

    if df_plantilla.empty:
        raise HTTPException(status_code=404, detail="No se encontraron plantillas de correo para los cursos especificados.")
    plantilla = pd.read_csv('temp_files/plantillas_correos.csv')
    # Transformar los datos para el envío de correos
    estructura_correo = transformar_datos_bienvenida(df, plantilla, correo_matriculas, correo_envio_bienvenidas,correo_envio_copia_matriculas)
    
    return estructura_correo
