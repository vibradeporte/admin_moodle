from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse,PlainTextResponse
from dotenv import load_dotenv
import pandas as pd
import requests
import time
import os
import re

load_dotenv()
verificar_correos_router = APIRouter()
api_key = os.getenv("API_KEY_MILLION")

if not api_key:
    raise ValueError("API_KEY_MILLION not found in environment variables")

# File paths
file_path = 'temp_files/correos_validar.csv'
resultado_file_path = 'temp_files/Resultado_Validacion_Correos.csv'
validacion_inicial_file_path = 'temp_files/validacion_inicial.xlsx'

def es_email_invalido(email):    
    # Validar si el email no contiene el carácter @
    if '@' not in email:
        return True
    
    # Separar el correo en la parte local y el dominio
    local_part, domain_part = email.split('@', 1)
    
    # Validar si la parte local está vacía
    if local_part.strip() == '':
        return True
    
    # Validar si el dominio contiene un punto (.) después del @
    if '.' not in domain_part:
        return True
    
    # Validar si hay caracteres antes del último punto en el dominio
    domain_name, domain_extension = domain_part.rsplit('.', 1)
    if domain_name.strip() == '' or domain_extension.strip() == '':
        return True
    
    # Si no cumple ninguna de las condiciones anteriores, el correo es válido
    return False





def limpiar_email(email):
    if pd.isna(email) or email is None:
        return "" 
    try:
        email = str(email)  # Asegurarse de que el correo es una cadena
        email = email.strip().replace("\xa0", "").replace("\t", "")
        email = email.replace(" ", "")  # Eliminar todos los espacios dentro del correo
        return email.lower()
    except Exception as e:
        print(f"Error occurred while cleaning email: {e}")
        return ""


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

@verificar_correos_router.post("/verificar_correos/", tags=["Correo"])
async def verificar_correos():
    """Verificar correos en un archivo Excel y actualizar el archivo con la validación."""

    try:
        df = pd.read_excel(validacion_inicial_file_path)
    except FileNotFoundError as e:
        return PlainTextResponse(
            content=f"El archivo en la ruta '{validacion_inicial_file_path}' no fue encontrado: {e}",
            status_code=404,
        )

    # Limpieza y validación del campo CORREO
    df["CORREO"] = df["CORREO"].apply(limpiar_email)
    df["¿EL email es inválido?"] = df["CORREO"].apply(
        lambda x: "SI" if es_email_invalido(x) or pd.isna(x) or x.strip() == "" else "NO"
    )



    


# Limpieza y validación del campo CORREO_SOLICITANTE`
    # Filtrar para validar solo los correos que no son inválidos
    df_to_validate = df[df["¿EL email es inválido?"] == "NO"]

    # Si no hay correos válidos a validar, terminar el proceso
    if df_to_validate.empty:
        df.to_excel(validacion_inicial_file_path, index=False)
        return PlainTextResponse(
            content="No hay correos válidos a validar en el archivo. Todos los correos se marcaron como inválidos.")

    # Guardar los correos a validar en el archivo CSV
    try:
        df_to_validate["CORREO"].to_csv(file_path, index=False, header=False)
    except Exception as e:
        return PlainTextResponse(
            content=f"Error al guardar el archivo CSV: {e}",
            status_code=500,
        )

    # Proceder con la validación a través del servicio externo
    try:
        response = enviar_archivo_a_validar(api_key, file_path)
        if response.status_code == 200:
            file_id, response_data = obtener_file_id(response)
        else:
            return PlainTextResponse(
                content=f"Error al cargar el archivo: {response.text}",
                status_code=response.status_code,
            )
    except requests.RequestException as e:
        return PlainTextResponse(
            content=f"Error al comunicar con el servicio de verificación: {e}",
            status_code=500,
        )

    # Esperar a que el proceso termine
    while True:
        time.sleep(10)
        try:
            status_response = consultar_status(api_key, file_id)
        except requests.RequestException as e:
            return PlainTextResponse(
                content=f"Error al obtener el estado del archivo: {e}",
                status_code=500,
            )

        status = status_response.get("status")

        if status == "finished":
            break
        elif status in ["error", "failed"]:
            return PlainTextResponse(
                content=f"El procesamiento del archivo falló con el status: {status}",
                status_code=400,
            )

    # Descargar el archivo de resultado
    try:
        descargar_resultado(api_key, file_id)
    except (requests.RequestException, FileNotFoundError) as e:
        return PlainTextResponse(
            content=f"An error occurred: {e}",
            status_code=500,
        )

    # Leer el archivo de resultado
    try:
        quality = pd.read_csv(resultado_file_path)
    except FileNotFoundError as e:
        return PlainTextResponse(
            content=f"El archivo en la ruta '{resultado_file_path}' no fue encontrado: {e}",
            status_code=404,
        )

    # Actualizar la columna de validación solo para los correos que pasaron la validación inicial
    try:
        validated_df = pd.read_excel(validacion_inicial_file_path)
    except FileNotFoundError as e:
        return PlainTextResponse(
            content=f"El archivo en la ruta '{validacion_inicial_file_path}' no fue encontrado: {e}",
            status_code=404,
        )

    if "¿EL email es inválido?" not in validated_df.columns:
        validated_df["¿EL email es inválido?"] = "NO"

    # Primero, mapeamos los resultados de calidad con los correos
    quality_map = dict(zip(quality["email"], quality["quality"]))


    # Luego, aplicamos la actualización de la columna "¿EL email es inválido?"
    validated_df["¿EL email solicitante es inválido?"] = validated_df["CORREO_SOLICITANTE"].apply(
        lambda x: "NO" if pd.isna(x) or x.strip() == "" else ("SI" if es_email_invalido(x) else "NO")
    )


    validated_df["CORREO_SOLICITANTE"] = df["CORREO_SOLICITANTE"].apply(limpiar_email)


    validated_df["¿EL email solicitante es inválido?"] = validated_df["CORREO_SOLICITANTE"].apply(
        lambda x: "SI" if es_email_invalido(x) else "NO"
    )

    try:
        os.remove(resultado_file_path)
    except FileNotFoundError:
        pass  # Ignorar si el archivo ya fue eliminado

    # Guardar el archivo actualizado con la validación
    try:
        validated_df.to_excel(validacion_inicial_file_path, index=False)
    except Exception as e:
        return PlainTextResponse(
            content=f"Error al guardar el archivo Excel: {e}",
            status_code=500,
        )

    # Contar la cantidad de correos válidos e inválidos
    count_si = validated_df[validated_df["¿EL email es inválido?"] == "SI"].shape[0]
    count_no = validated_df[validated_df["¿EL email es inválido?"] == "NO"].shape[0]

    # Mensaje de respuesta
    message = (
        f"Los estudiantes que pasaron exitosamente la verificación fueron: {count_no}.\n"
        f"Los estudiantes que no pasaron exitosamente la verificación fueron: {count_si}.\n"
    )
    return PlainTextResponse(content=message)
