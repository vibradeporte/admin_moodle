from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse,PlainTextResponse
from dotenv import load_dotenv
import pandas as pd
import requests
import time
import os


load_dotenv()
verificar_correos = APIRouter()
api_key = os.getenv("API_KEY_MILLION")

if not api_key:
    raise ValueError("API_KEY_MILLION not found in environment variables")

# File paths
file_path = 'temp_files/correos_validar.csv'
resultado_file_path = 'temp_files/Resultado_Validacion_Correos.csv'
validacion_inicial_file_path = 'temp_files/validacion_inicial.xlsx'

def limpiar_email(email):
    email = email.strip()
    email = email.replace('\t', '').replace('\xa0', '')
    email = ' '.join(email.split())
    email = email.lower()
    return email

def enviar_archivo_a_validar(api_key, file_path):
    url = f"https://bulkapi.millionverifier.com/bulkapi/v2/upload?key={api_key}"
    with open(file_path, 'rb') as file:
        files = [('file_contents', (file.name, file, 'text/plain'))]
        response = requests.post(url, files=files)
    response.raise_for_status()
    return response

def obtener_file_id(response):
    response_data = response.json()
    file_id = response_data.get("file_id")
    return file_id, response_data

def consultar_status(api_key, file_id):
    url = f"https://bulkapi.millionverifier.com/bulkapi/v2/fileinfo?key={api_key}&file_id={file_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def descargar_resultado(api_key, file_id):
    url = f"https://bulkapi.millionverifier.com/bulkapi/v2/download?key={api_key}&file_id={file_id}&filter=all"
    response = requests.get(url)
    response.raise_for_status()
    with open(resultado_file_path, 'wb') as file:
        file.write(response.content)
    print(f"Results have been saved to {resultado_file_path}")

@verificar_correos.post("/verificar_correos/", tags=['Correo'])
async def verificar_correos_endpoint():
    try:

        df = pd.read_excel(validacion_inicial_file_path)
        correos_validar = df['CORREO'].apply(limpiar_email)
        correos_validar.to_csv(file_path, index=False, header=False)


        response = enviar_archivo_a_validar(api_key, file_path)
        if response.status_code == 200:
            print("File uploaded successfully!")
            file_id, response_data = obtener_file_id(response)
            print(response_data)
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Error al cargar el archivo. {response.text}")

        if not file_id:
            raise HTTPException(status_code=400, detail="File ID no encontrado.")

        print(f"File ID: {file_id}")

        while True:
            time.sleep(10)
            status_response = consultar_status(api_key, file_id)
            status = status_response.get("status")
            print(f"Current status: {status}")

            if status == "finished":
                break
            elif status in ["error", "failed"]:
                raise HTTPException(status_code=400, detail=f"El procesamiento del archivo falló con el status: {status}")

        descargar_resultado(api_key, file_id)

        quality = pd.read_csv(resultado_file_path)
        validated_df = pd.read_excel(validacion_inicial_file_path)
        validated_df['¿EL email es inválido?'] = quality['quality']
        os.remove(resultado_file_path)
        validated_df['¿EL email es inválido?'] = validated_df['¿EL email es inválido?'].apply(lambda x: 'SI' if x == 'bad' else 'NO')
        validated_df.to_excel(validacion_inicial_file_path, index=False)

        count_si = validated_df[validated_df['¿EL email es inválido?'] == 'SI'].shape[0]
        count_no = validated_df[validated_df['¿EL email es inválido?'] == 'NO'].shape[0]
        message = (
            
            f"Los estudiantes que pasaron exitosamente la verificación fueron: {count_no}.\n"
            f"Los estudiantes que no pasaron exitosamente la verificación fueron: {count_si}.\n"
            
        )
        return PlainTextResponse(content=message)

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"El archivo en la ruta '{file_path}' no fue encontrado.")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error al comunicar con el servicio de verificación: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

