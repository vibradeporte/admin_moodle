from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests

from routers.validacion_nombres_apellidos import *
from routers.verificar_correos import *
from routers.subida_Archivos import *
from routers.matricular_Usuarios import *
from routers.prueba_user_id import prueba_conseguir_id
from routers.validacion_cedula import *
from routers.validacion_num_wapp import *
from routers.normalizacion import *
from routers.validacion_final import *
from routers.validar_cursos_certificado import *
from routers.validacion_identidad import *

#from  routers.core_group_create_groups import *

from routers.core_user_create_users import *

from routers.enrol_manual_enrol_users import *


#moodle
from routers.est_matriculados_curso_con_certificados import est_matriculados_curso_con_certificados_router
from routers.usuarios_bd import usuarios_bd_router
from routers.duracion_curso_y_descripcion import duracion_curso_y_descripcion_router
from routers.nombres_cursos import nombres_cursos_router


#Whatsapp
from routers.envio_mensajes_whatsapp import *

app = FastAPI()
app.title = "Universal Learning ADMIN MOODLE API "
app.version = "0.0.1"


app = FastAPI(
    title="Universal Learning ADMIN MOODLE API",
    version="0.0.1"
)

#app.include_router(core_group_create_groups_router)

app.include_router(enrol_manual_enrol_users_router)

app.include_router(core_user_create_users_router)

app.include_router(identificacion_usuario)

app.include_router(prueba_conseguir_id)
app.include_router(validacion_cedula_router)
app.include_router(enrol_manual_enrol_users_router)
app.include_router(verificacion_inicial_archivo)
app.include_router(validacion_nombres_apellidos_router)
app.include_router(verificar_correos)
app.include_router(validacion_numeros_whatsapp_router)
app.include_router(normalizacion_router)
app.include_router(validacion_final)
app.include_router(validacion_cursos_certificado_router_prueba)

#moodle
app.include_router(est_matriculados_curso_con_certificados_router)
app.include_router(usuarios_bd_router)
app.include_router(duracion_curso_y_descripcion_router)
app.include_router(nombres_cursos_router)

#whatsapp
app.include_router(envio_mensajes_whatsapp_router)
@app.get('/', tags=['home'])
def message():
    response = requests.get('https://ipinfo.io/ip')
    ip_address = response.text.strip()
    print(ip_address)
    return HTMLResponse(f'<h1>Universal Learning ADMIN MOODLE API</h1><p>Client IP: {ip_address}</p>')






