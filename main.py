from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from routers.Registrar_Usuarios import *
from routers.matricular_Usuarios import *
from routers.upload_matricula import *
from routers.verificar_correos import *
from routers.validar_cursos import *
from routers.validacion_final import *
app = FastAPI()
app.title = "Universal Learning ADMIN MOODLE API "
app.version = "0.0.1"


#app.include_router(core_user_create_users_router)
#app.include_router(enrol_manual_enrol_users_router)
app.include_router(upload_file_matricula)
app.include_router(verificar_correos)
app.include_router(validacion_cursos)
app.include_router(validacion_final)
@app.get('/', tags=['home'])
def message():
    return HTMLResponse('<h1>Universal Learning ADMIN MOODLE API</h1>')
