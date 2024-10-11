from fastapi import FastAPI, APIRouter, File, HTTPException
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

validacion_tiempo_mensaje_de_bienvenida = APIRouter()

@validacion_tiempo_mensaje_de_bienvenida.post("/validar_tiempo_mensaje_de_bienvenida/", tags=["validar_tiempo_mensaje_de_bienvenida"])
async def validacion_fecha_hora_mensaje_de_bienvenida():
    try:
        # Leer el archivo Excel
        try:
            df = pd.read_excel('temp_files/validacion_inicial.xlsx')
        except FileNotFoundError:
            raise HTTPException(status_code=400, detail="El archivo no fue encontrado. Asegúrate de que exista en la ruta especificada.")

        # Verificar si las columnas necesarias existen
        if 'FECHA_MENSAJE_BIENVENIDA' not in df.columns or 'HORA_MENSAJE_BIENVENIDAS' not in df.columns:
            raise HTTPException(status_code=400, detail="El archivo debe contener las columnas 'FECHA_MENSAJE_BIENVENIDA' y 'HORA_MENSAJE_BIENVENIDAS'.")

        # Convertir la columna de fechas
        df['FECHA_MENSAJE_BIENVENIDA'] = pd.to_datetime(df['FECHA_MENSAJE_BIENVENIDA'], errors='coerce')
        df['FECHA_MENSAJE_BIENVENIDA'] = df['FECHA_MENSAJE_BIENVENIDA'].fillna(pd.Timestamp(datetime.now().date()))

        # Convertir la columna de horas
        df['HORA_MENSAJE_BIENVENIDAS'] = pd.to_timedelta(df['HORA_MENSAJE_BIENVENIDAS'], errors='coerce')

        # Obtener la fecha actual y límite
        fecha_actual = pd.Timestamp(datetime.now().date())
        fecha_limite_superior = fecha_actual + pd.Timedelta(days=4)

        # Verificar si la fecha está dentro del rango
        df['¿Fecha de envio del mensaje de bienvenida es invalido?'] = np.where(
            (df['FECHA_MENSAJE_BIENVENIDA'] >= fecha_actual) & (df['FECHA_MENSAJE_BIENVENIDA'] <= fecha_limite_superior),
            'NO', 'SI'
        )

        # Función para ajustar la hora
        def ajustar_hora(row):
            if pd.isna(row['HORA_MENSAJE_BIENVENIDAS']):
                # Si la hora está vacía, usar la hora actual más 3 minutos
                return (datetime.now() + timedelta(minutes=3)).time()
            else:
                # Ajustar hora sin sumar más horas si no es necesario
                return (datetime.combine(datetime.today(), (datetime.min + row['HORA_MENSAJE_BIENVENIDAS']).time())).time()

        df['HORA_MENSAJE_BIENVENIDAS'] = df.apply(ajustar_hora, axis=1)

        # Verificar si la hora está dentro del rango permitido
        hora_inicio_valida = datetime.strptime('06:00:00', '%H:%M:%S').time()
        hora_fin_valida = datetime.strptime('17:00:00', '%H:%M:%S').time()

        def es_hora_invalida(row):
            hora = row['HORA_MENSAJE_BIENVENIDAS']
            if hora < hora_inicio_valida or hora > hora_fin_valida:
                return 'SI'
            return 'NO'

        df['¿Es la hora de mensaje de bienvenida invalida?'] = df.apply(es_hora_invalida, axis=1)

        # Combinar la fecha y hora en una sola columna
        def combinar_fecha_hora(row):
            if pd.isna(row['FECHA_MENSAJE_BIENVENIDA']):
                return pd.NaT
            else:
                return datetime.combine(row['FECHA_MENSAJE_BIENVENIDA'], row['HORA_MENSAJE_BIENVENIDAS'])

        df['send_time'] = df.apply(combinar_fecha_hora, axis=1)

        # Reemplazar valores NaN o infinitos antes de convertir a JSON
        df.replace({np.nan: None, np.inf: None, -np.inf: None}, inplace=True)
        
        # Guardar el archivo actualizado
        df.to_excel('temp_files/validacion_inicial.xlsx', index=False)

        # Retornar el resultado
        return df.to_dict(orient='records')

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


