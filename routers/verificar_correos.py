from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from jwt_manager import JWTBearer
from dotenv import load_dotenv
import pandas as pd
import requests
import time
import os

load_dotenv()
verificar_correos_router = APIRouter()
api_key = os.getenv("API_KEY_MILLION")

if not api_key:
    raise ValueError("API_KEY_MILLION no encontrado en las variables de entorno")

# Rutas de archivos
file_path = 'temp_files/correos_validar.csv'
resultado_file_path = 'temp_files/Resultado_Validacion_Correos.csv'
validacion_inicial_file_path = 'temp_files/validacion_inicial.xlsx'

def es_email_invalido(email: str) -> bool:
    """
    Verifica si un correo electrónico es inválido.

    Un correo electrónico se considera inválido si:
    - No contiene el carácter '@'.
    - La parte local está vacía.
    - La parte del dominio no contiene un punto ('.') después del '@'.
    - No hay caracteres antes del último punto en el dominio.

    :param email: El correo electrónico a verificar.
    :type email: str
    :return: True si el correo es inválido, False en caso contrario.
    :rtype: bool
    """
    if '@' not in email:
        return True
    
    local_part, domain_part = email.split('@', 1)
    
    if local_part.strip() == '':
        return True
    
    if '.' not in domain_part:
        return True
    
    domain_name, domain_extension = domain_part.rsplit('.', 1)
    if domain_name.strip() == '' or domain_extension.strip() == '':
        return True
    
    return False

def limpiar_email(email: str) -> str:
    """
    Limpia un correo electrónico eliminando espacios y caracteres especiales,
    y convirtiéndolo a minúsculas.

    :param email: El correo electrónico a limpiar.
    :type email: str
    :return: El correo electrónico limpio.
    :rtype: str
    """
    if pd.isna(email) or email is None:
        return ""
    try:
        email = str(email).strip().replace("\xa0", "").replace("\t", "")
        email = email.replace(" ", "")
        return email.lower()
    except Exception as e:
        print(f"Error al limpiar el correo electrónico: {e}")
        return ""

def enviar_archivo_para_validacion(api_key: str, file_path: str) -> requests.Response:
    """
    Envía un archivo para validación a través de la API de Million Verifier.

    :param api_key: La clave de API para autenticación.
    :type api_key: str
    :param file_path: La ruta al archivo que se enviará para validación.
    :type file_path: str
    :return: La respuesta de la solicitud de carga.
    :rtype: requests.Response
    :raises HTTPError: Si la solicitud a la API falla.
    """
    url = f"https://bulkapi.millionverifier.com/bulkapi/v2/upload?key={api_key}"
    with open(file_path, 'rb') as file:
        files = [('file_contents', (file.name, file, 'text/plain'))]
        response = requests.post(url, files=files)
    response.raise_for_status()
    return response

def obtener_file_id(response: requests.Response) -> str:
    """
    Extrae el file_id de la respuesta de la solicitud de carga de archivo a la API de Million Verifier.

    :param response: La respuesta de la solicitud de carga de archivo.
    :type response: requests.Response
    :return: El file_id extraído.
    :rtype: str
    """
    response_data = response.json()
    return response_data.get("file_id")

def consultar_estado(api_key: str, file_id: str) -> dict:
    """
    Consulta el estado de la verificación de correos electrónicos para un archivo cargado en la API de Million Verifier.

    :param api_key: La clave de API para autenticación.
    :type api_key: str
    :param file_id: El file_id del archivo cargado.
    :type file_id: str
    :return: La respuesta de la API con la información del estado.
    :rtype: dict
    :raises HTTPError: Si la solicitud a la API falla.
    """
    url = f"https://bulkapi.millionverifier.com/bulkapi/v2/fileinfo?key={api_key}&file_id={file_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def descargar_resultado_validacion(api_key: str, file_id: str) -> None:
    """
    Descarga el resultado de la verificación de correos electrónicos desde la API de Million Verifier y guarda el contenido en un archivo.

    :param api_key: La clave de API para autenticación.
    :type api_key: str
    :param file_id: El file_id del archivo cuyos resultados se desean descargar.
    :type file_id: str
    :raises HTTPError: Si la solicitud a la API falla.
    """
    url = f"https://bulkapi.millionverifier.com/bulkapi/v2/download?key={api_key}&file_id={file_id}&filter=all"
    response = requests.get(url)
    response.raise_for_status()
    with open(resultado_file_path, 'wb') as file:
        file.write(response.content)
    print(f"Los resultados se han guardado en {resultado_file_path}")

@verificar_correos_router.post("/verificar_correos/", tags=["Correo"], dependencies=[Depends(JWTBearer())])
async def verificar_correos():
    """
    Verifica correos electrónicos desde un archivo Excel y actualiza el archivo con los resultados de la validación.
    """
    try:
        df = pd.read_excel(validacion_inicial_file_path)
        df['CORREO'] = df['CORREO'].str.lower()
    except FileNotFoundError as e:
        return PlainTextResponse(
            content=f"El archivo en la ruta '{validacion_inicial_file_path}' no fue encontrado: {e}",
            status_code=404,
        )

    # Limpieza y validación del campo 'CORREO'
    df["CORREO"] = df["CORREO"].apply(limpiar_email)
    df["¿EL email es inválido?"] = df["CORREO"].apply(
        lambda x: "SI" if pd.isna(x) or x.strip() == "" else ("SI" if es_email_invalido(x) else "NO")
    )

    # Filtrar solo los correos válidos
    df_a_validar = df[df["¿EL email es inválido?"] == "NO"]

    # Si no hay correos válidos para validar, detener el proceso
    if df_a_validar.empty:
        df.to_excel(validacion_inicial_file_path, index=False)
        return PlainTextResponse(
            content="No hay correos válidos a validar en el archivo. Todos los correos se marcaron como inválidos."
        )

    # Guardar los correos a validar en un archivo CSV
    try:
        df_a_validar["CORREO"].to_csv(file_path, index=False, header=False)
    except Exception as e:
        return PlainTextResponse(
            content=f"Error al guardar el archivo CSV: {e}",
            status_code=500,
        )

    # Proceder con la validación a través del servicio externo
    try:
        response = enviar_archivo_para_validacion(api_key, file_path)
        if response.status_code == 200:
            file_id = obtener_file_id(response)
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

    # Esperar hasta que el proceso se complete
    while True:
        time.sleep(10)
        try:
            status_response = consultar_estado(api_key, file_id)
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
                content=f"El procesamiento del archivo falló con el estado: {status}",
                status_code=400,
            )

    # Descargar el archivo de resultados
    try:
        descargar_resultado_validacion(api_key, file_id)
    except (requests.RequestException, FileNotFoundError) as e:
        return PlainTextResponse(
            content=f"Ocurrió un error: {e}",
            status_code=500,
        )

    # Leer el archivo de resultados
    try:
        quality = pd.read_csv(resultado_file_path)
    except FileNotFoundError as e:
        return PlainTextResponse(
            content=f"El archivo en la ruta '{resultado_file_path}' no fue encontrado: {e}",
            status_code=404,
        )

    # Actualizar la columna de validación para los correos que pasaron la validación inicial
    try:
        validated_df = pd.read_excel(validacion_inicial_file_path)
    except FileNotFoundError as e:
        return PlainTextResponse(
            content=f"El archivo en la ruta '{validacion_inicial_file_path}' no fue encontrado: {e}",
            status_code=404,
        )

    if "¿EL email es inválido?" not in validated_df.columns:
        validated_df["¿EL email es inválido?"] = "NO"

    # Mapear los resultados de calidad con los correos
    quality_map = dict(zip(quality["email"], quality["quality"]))

    # Actualizar la columna "¿EL email es inválido?"
    validated_df["¿EL email es inválido?"] = validated_df.apply(
        lambda row: "SI" if row["CORREO"] not in quality_map or quality_map.get(row["CORREO"]) == "bad" else row["¿EL email es inválido?"],
        axis=1
    )

    validated_df["CORREO_SOLICITANTE"] = df["CORREO_SOLICITANTE"].apply(limpiar_email)

    validated_df["¿EL email solicitante es inválido?"] = validated_df["CORREO_SOLICITANTE"].apply(
        lambda x: "NO" if pd.isna(x) or x.strip() == "" else ("SI" if es_email_invalido(x) else "NO")
    )

    # Guardar el archivo actualizado con la validación
    try:
        validated_df.to_excel(validacion_inicial_file_path, index=False)
    except Exception as e:
        return PlainTextResponse(
            content=f"Error al guardar el archivo Excel: {e}",
            status_code=500,
        )

    # Contar correos válidos e inválidos
    count_si = validated_df[validated_df["¿EL email es inválido?"] == "SI"].shape[0]
    count_no = validated_df[validated_df["¿EL email es inválido?"] == "NO"].shape[0]

    # Mensaje de respuesta
    message = {
        "estudiantes_exitosos": int(count_no),
        "estudiantes_no_exitosos": int(count_si)
    }
    return JSONResponse(content=message)

