from fastapi import Depends, HTTPException, APIRouter, Body
from jwt_manager import JWTBearer
import base64
import os

# Definir el enrutador para la API de archivo base64
archivo_base64_router = APIRouter()

@archivo_base64_router.post("/ArchivoBase64/", tags=['Archivos'], dependencies=[Depends(JWTBearer())])
async def generar_base64_desde_archivo(ruta_archivo: str = Body(..., embed=True, description="Ruta al archivo")) -> dict:
    """
    Genera una representación base64 de un archivo localizado en la ruta especificada.

    Argumentos:
    ruta_archivo (str): La ruta del archivo que se quiere convertir en base64.

    Retorna:
    dict: Un diccionario con el contenido base64 del archivo, su nombre y tipo.
    """
    if not os.path.exists(ruta_archivo):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    with open(ruta_archivo, 'rb') as archivo:
        contenido_binario = archivo.read()
        contenido_base64 = base64.b64encode(contenido_binario).decode('utf-8')
    
    nombre_archivo = os.path.basename(ruta_archivo)
    tipo_archivo = ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    if nombre_archivo.endswith(".xlsx") else "application/octet-stream")
    
    respuesta_archivo = {
        "content": contenido_base64,
        "name": nombre_archivo,
        "type": tipo_archivo
    }
    
    return respuesta_archivo

