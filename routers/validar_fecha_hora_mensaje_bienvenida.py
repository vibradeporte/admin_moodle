from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import pandas as pd
from datetime import datetime, timedelta, time, date
import numpy as np
import re
from jwt_manager import JWTBearer

validacion_tiempo_mensaje_de_bienvenida = APIRouter()

# Diccionario de meses para convertir nombres de meses a números
meses_diccionario = {
    'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
    'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
    'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
}

def limpiar_fecha(fecha: str) -> date:
    """
    Limpia y normaliza una fecha para convertirla a un objeto de tipo date.

    :param fecha: La fecha en formato cadena.
    :type fecha: str
    :return: La fecha limpia en formato date o None si no es válida.
    :rtype: date
    """
    if pd.isna(fecha):
        return None

    # Asegurarse de que la fecha sea una cadena
    if not isinstance(fecha, str):
        fecha = str(fecha)

    # Normalizar nombres de los meses al formato numérico
    for mes, num in meses_diccionario.items():
        fecha = re.sub(mes, num, fecha, flags=re.IGNORECASE)

    # Remover caracteres no deseados y extraer día, mes, año
    fecha_limpia = re.sub(r'[^0-9\/\-\s]', '', fecha).strip()

    # Eliminar la parte de la hora si está presente
    fecha_limpia = re.sub(r'\s+\d{1,2}:\d{2}:\d{2}', '', fecha_limpia)

    # Tratar de convertir a datetime
    formatos = [
        '%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d', '%d %m %Y',
        '%d-%b-%Y', '%d/%b/%Y', '%d-%B-%Y', '%d/%B/%Y', '%m/%d/%Y', '%b-%d-%Y', '%b/%d/%Y', '%m-%d-%Y'
    ]
    for formato in formatos:
        try:
            return datetime.strptime(fecha_limpia, formato).date()
        except ValueError:
            continue

    # Intentar extraer solo la parte de la fecha si aún hay horas presentes
    fecha_limpia = re.sub(r'\s.*', '', fecha_limpia)
    for formato in formatos:
        try:
            return datetime.strptime(fecha_limpia, formato).date()
        except ValueError:
            continue

    return None

def limpiar_hora(hora: str) -> time:
    """
    Limpia y normaliza una hora para convertirla a un objeto de tipo time.

    :param hora: La hora en formato cadena.
    :type hora: str
    :return: La hora limpia en formato time o None si no es válida.
    :rtype: time
    """
    if pd.isna(hora):
        return None

    # Asegurarse de que la hora sea una cadena
    if not isinstance(hora, str):
        hora = str(hora)

    # Remover caracteres no deseados
    hora = re.sub(r'[^0-9:]', '', hora).strip()

    # Tratar de convertir a datetime.time
    formatos = ['%H:%M:%S', '%H:%M']
    for formato in formatos:
        try:
            return datetime.strptime(hora, formato).time()
        except ValueError:
            continue

    return None

# Definición de horarios válidos
hora_inicio_valida = time(6, 0, 0)
hora_fin_valida = time(18, 0, 0)

def es_fecha_invalida(fila: pd.Series) -> str:
    """
    Verifica si una fecha es inválida.

    :param fila: La fila del DataFrame que contiene la fecha a verificar.
    :type fila: pd.Series
    :return: 'SI' si la fecha es inválida, 'NO' en caso contrario.
    :rtype: str
    """
    fecha_limpia = fila['FECHA_LIMPIA']
    fecha_original = fila['FECHA_MENSAJE_BIENVENIDA']

    if fecha_limpia is None and pd.notna(fecha_original):
        return 'SI'

    if isinstance(fecha_limpia, datetime):
        fecha_limpia = fecha_limpia.date()

    if isinstance(fecha_limpia, date):
        hoy = datetime.now().date()
        if fecha_limpia < hoy or fecha_limpia > hoy + timedelta(days=4):
            return 'SI'

    return 'NO'

def es_hora_invalida(fila: pd.Series) -> str:
    """
    Verifica si una hora es inválida.

    :param fila: La fila del DataFrame que contiene la hora a verificar.
    :type fila: pd.Series
    :return: 'SI' si la hora es inválida, 'NO' en caso contrario.
    :rtype: str
    """
    hora = fila['HORA_MENSAJE_BIENVENIDAS_LIMPIA']
    hora_original = fila['HORA_MENSAJE_BIENVENIDAS']
    fecha = fila['FECHA_LIMPIA']

    if hora is None and pd.notna(hora_original):
        return 'SI'

    if isinstance(hora, time) and fecha is not None:
        hoy = datetime.now().date()
        if fecha == hoy:
            hora_actual = datetime.now().time()
            if hora <= hora_actual:
                return 'SI'
        if hora_inicio_valida <= hora <= hora_fin_valida:
            return 'NO'
        else:
            return 'SI'

    return ''

def combinar_fecha_hora(fila: pd.Series) -> datetime:
    """
    Combina la fecha y la hora en un objeto datetime.

    :param fila: La fila del DataFrame que contiene la fecha y hora a combinar.
    :type fila: pd.Series
    :return: La combinación de fecha y hora en formato datetime o None si alguno es inválido.
    :rtype: datetime
    """
    fecha = fila['FECHA_LIMPIA']
    hora = fila['HORA_MENSAJE_BIENVENIDAS_LIMPIA']

    if pd.isna(fecha) or pd.isna(hora):
        return None

    return datetime.combine(fecha, hora)

def es_fecha_hora_incompleta(fila: pd.Series) -> str:
    """
    Verifica si la fecha y la hora están incompletas.

    :param fila: La fila del DataFrame que contiene la fecha y hora a verificar.
    :type fila: pd.Series
    :return: 'SI' si la fecha o la hora están incompletas, 'NO' en caso contrario.
    :rtype: str
    """
    fecha = fila['FECHA_LIMPIA']
    hora = fila['HORA_MENSAJE_BIENVENIDAS_LIMPIA']

    if (fecha is not None and hora is None) or (fecha is None and hora is not None):
        return 'SI'

    return 'NO'

@validacion_tiempo_mensaje_de_bienvenida.post("/validar_tiempo_mensaje_de_bienvenida/", tags=["validar_tiempo_mensaje_de_bienvenida"], dependencies=[Depends(JWTBearer())])
async def validacion_fecha_hora_mensaje_de_bienvenida():
    """
    Valida las fechas y horas de los envíos programados de mensajes de bienvenida.

    :return: Mensaje indicando el resultado de la validación.
    :rtype: JSONResponse
    """
    try:
        try:
            df = pd.read_excel('temp_files/validacion_inicial.xlsx')
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error al leer el archivo: {str(e)}")

        # Verificar si las columnas necesarias existen
        if 'FECHA_MENSAJE_BIENVENIDA' not in df.columns or 'HORA_MENSAJE_BIENVENIDAS' not in df.columns:
            raise HTTPException(status_code=400, detail="El archivo debe contener las columnas 'FECHA_MENSAJE_BIENVENIDA' y 'HORA_MENSAJE_BIENVENIDAS'.")

        df['FECHA_LIMPIA'] = df['FECHA_MENSAJE_BIENVENIDA'].apply(limpiar_fecha)
        df['HORA_MENSAJE_BIENVENIDAS_LIMPIA'] = df['HORA_MENSAJE_BIENVENIDAS'].apply(limpiar_hora)
        df['FECHA_INVALIDA'] = df.apply(es_fecha_invalida, axis=1)
        df['HORA_INVALIDA'] = df.apply(es_hora_invalida, axis=1)
        df['FECHA_HORA_INCOMPLETA'] = df.apply(es_fecha_hora_incompleta, axis=1)
        df['FECHA_HORA_COMBINADA'] = df.apply(combinar_fecha_hora, axis=1)

        df.replace({np.nan: None, np.inf: None, -np.inf: None}, inplace=True)
        df.to_excel('temp_files/validacion_inicial.xlsx', index=False)

        message = {
            "message": "Validación fecha y hora de envíos programados de mensajes de bienvenida terminada."
        }
        return JSONResponse(content=message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
