from fastapi import FastAPI, ApiRouter, File, HTTPException
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

validacion_tiempo_mensaje_de_bienvenida = APIRouter()

@validacion_tiempo_mensaje_de_bienvenida.post("/validar_tiempo_mensaje_de_bienvenida/",tags=["validar_tiempo_mensaje_de_bienvenida"])
async def validacion_fecha_hora_mensaje_de_bienvenida():
    try:
        df = pd.read_excel('temp_files/validacion_inicial.xlsx')


        if 'FECHA_MENSAJE_BIENVENIDA' not in df.columns or 'HORA_MENSAJE_BIENVENIDAS' not in df.columns:
            raise HTTPException(status_code=400, detail="El archivo debe contener las columnas 'FECHA_MENSAJE_BIENVENIDA' y 'HORA_MENSAJE_BIENVENIDAS'.")

        df['FECHA_MENSAJE_BIENVENIDA'] = pd.to_datetime(df['FECHA_MENSAJE_BIENVENIDA'], errors='coerce')
        df['FECHA_MENSAJE_BIENVENIDA'] = df['FECHA_MENSAJE_BIENVENIDA'].fillna(pd.Timestamp(datetime.now().date()))
        df['HORA_MENSAJE_BIENVENIDAS'] = pd.to_datetime(df['HORA_MENSAJE_BIENVENIDAS'], format='%H:%M:%S', errors='coerce').dt.time

        fecha_actual = pd.Timestamp(datetime.now().date())
        fecha_limite_superior = fecha_actual + pd.Timedelta(days=4)


        df['Fecha de envio del mensaje de bienvenida es invalido?'] = np.where(
            (df['FECHA_MENSAJE_BIENVENIDA'] >= fecha_actual) & (df['FECHA_MENSAJE_BIENVENIDA'] <= fecha_limite_superior),
            'NO',
            'SI' 
        )


        def ajustar_hora(row):
            if pd.isna(row['HORA_MENSAJE_BIENVENIDAS']):
                # Si la hora está vacía, usar la hora actual más 5 horas y 3 minutos
                return (datetime.now() - timedelta(hours=5, minutes=3)).time()
            else:

                return (datetime.combine(datetime.today(), row['HORA_MENSAJE_BIENVENIDAS']) - timedelta(hours=5)).time()


        df['HORA_MENSAJE_BIENVENIDAS'] = df.apply(ajustar_hora, axis=1)
        hora_inicio_valida = datetime.strptime('01:00:00', '%H:%M:%S').time()
        hora_fin_valida = datetime.strptime('13:00:00', '%H:%M:%S').time()

        # Función para verificar si la hora es válida
        def es_hora_invalida(row):
            hora = row['HORA_MENSAJE_BIENVENIDAS']
            if hora < hora_inicio_valida or hora > hora_fin_valida:
                return 'SI'
            return 'NO' 

        df['Es la hora de mensaje de bienvenida invalida?'] = df.apply(es_hora_invalida, axis=1)

        def combinar_fecha_hora(row):
            if pd.isna(row['FECHA_MENSAJE_BIENVENIDA']):
                return pd.NaT 
            else:
                return datetime.combine(row['FECHA_MENSAJE_BIENVENIDA'], row['HORA_MENSAJE_BIENVENIDAS'])

        df['send_time'] = df.apply(combinar_fecha_hora, axis=1)

        return df.to_dict(orient='records')

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

