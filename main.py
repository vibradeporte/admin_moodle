from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests


from routers.verificar_correos import *
from routers.subida_Archivos import *
#from routers.validacion_identidad import identificacion_usuario
from routers.validacion_cedula import *


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#moodle
from routers.est_matriculados_curso_con_certificados import est_matriculados_curso_con_certificados_router
from routers.usuarios_bd import usuarios_bd_router
from routers.duracion_curso_y_descripcion import duracion_curso_y_descripcion_router
from routers.nombres_cursos import nombres_cursos_router


app = FastAPI()
app.title = "Universal Learning ADMIN MOODLE API "
app.version = "0.0.1"


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

app.include_router(validacion_cursos)
app.include_router(validacion_final)


#moodle
app.include_router(est_matriculados_curso_con_certificados_router)
app.include_router(usuarios_bd_router)
app.include_router(duracion_curso_y_descripcion_router)
app.include_router(nombres_cursos_router)

@app.get('/', tags=['home'])
def message():
    response = requests.get('https://ipinfo.io/ip')
    ip_address = response.text.strip()
    print(ip_address)
    return HTMLResponse(f'<h1>Universal Learning ADMIN MOODLE API</h1><p>Client IP: {ip_address}</p>')



