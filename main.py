from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests
import logging

from routers.verificar_correos import *
from routers.subida_Archivos import *
#from routers.validacion_identidad import identificacion_usuario
from routers.validacion_cedula import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Universal Learning ADMIN MOODLE API",
    version="0.0.1"
)

app.include_router(validacion_cedula_router)
#app.include_router(identificacion_usuario)
app.include_router(verificacion_inicial_archivo)
#app.include_router(upload_file_matricula)
app.include_router(verificar_correos)
#app.include_router(validacion_cursos)
#app.include_router(validacion_final)

@app.get('/', tags=['home'])
def message():
    response = requests.get('https://ipinfo.io/ip')
    print(response.text)
    return HTMLResponse('<h1>Universal Learning ADMIN MOODLE API</h1>')



