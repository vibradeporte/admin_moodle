from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests
import logging
#from routers.upload_matricula import upload_file_matricula
#from routers.verificar_correos import verificar_correos
#from routers.validar_cursos import validacion_cursos
#from routers.validacion_final import validacion_final
from routers.subida_Archivos import verificacion_inicial_archivo
from routers.validacion_identidad import identificacion_usuario

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Universal Learning ADMIN MOODLE API",
    version="0.0.1"
)


app.include_router(identificacion_usuario)
app.include_router(verificacion_inicial_archivo)
# app.include_router(core_user_create_users_router)
# app.include_router(enrol_manual_enrol_users_router)
#app.include_router(upload_file_matricula)
#app.include_router(verificar_correos)
#app.include_router(validacion_cursos)
#app.include_router(validacion_final)

@app.get('/', tags=['home'])
def message():
    response = requests.get('https://ipinfo.io/ip')
    print(response.text)
    return HTMLResponse('<h1>Universal Learning ADMIN MOODLE API</h1>')



