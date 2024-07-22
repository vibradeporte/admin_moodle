from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests

# Archivos
from routers.Archivo_base64 import Archivo_base64_router

# Validacion Inicial
from routers.validacion_identidad import identificacion_usuario
from routers.validacion_nombres_apellidos import validacion_nombres_apellidos_router
from routers.subida_Archivos import verificacion_inicial_archivo
from routers.validacion_cedula import validacion_cedula_router

# Correos
from routers.Envio_Correo import correo_router
from routers.verificar_correos import verificar_correos
from routers.Envio_Correo_Archivo_Adjunto import correo_archivo_adjunto_router

# Cursos
from routers.validar_cursos_certificado import validacion_cursos_certificado_router_prueba
from routers.duracion_curso_y_descripcion import duracion_curso_y_descripcion_router
from routers.nombres_cursos import nombres_cursos_router

# Validacion Secundaria
from routers.validacion_num_wapp import validacion_numeros_whatsapp_router
from routers.normalizacion import normalizacion_router
from routers.validacion_final import validacion_final
from routers.validar_estatus_estudiante import validacion_estudiantes_estatus_router
# JSON
from routers.Parametros_bienvenida import Bienvenida_wapp_estudiantes_router
from routers.estructura_correo_bienvenida import Bienvenida_correo_estudiantes_router

# Grupos
from routers.core_group_create_groups import core_group_create_groups_router
from routers.core_group_add_group_members import core_group_add_group_members_router

# Estudiantes
from routers.core_user_create_users import core_user_create_users_router
from routers.enrol_manual_enrol_users import enrol_manual_enrol_users_router
from routers.prueba_user_id import prueba_conseguir_id
from routers.usuarios_bd import usuarios_bd_router


# SQL
from routers.poblar_tabla_matricula import poblar_tabla_matricula_router
from routers.poblar_tabla_detalle_matricula import poblar_tabla_detalle_matricula_router

# WhatsApp
from routers.envio_mensajes_whatsapp import envio_mensajes_whatsapp_router

app = FastAPI(
    title="Universal Learning ADMIN MOODLE API",
    version="0.0.1"
)

# Including routers
# Archivos
app.include_router(Archivo_base64_router)

# SQL
app.include_router(poblar_tabla_matricula_router)
app.include_router(poblar_tabla_detalle_matricula_router)

# Grupos
app.include_router(core_group_create_groups_router)
app.include_router(core_group_add_group_members_router)

# JSON
app.include_router(Bienvenida_wapp_estudiantes_router)

# Correos
app.include_router(correo_router)
app.include_router(Bienvenida_correo_estudiantes_router)
app.include_router(correo_archivo_adjunto_router)

# Estudiantes
app.include_router(enrol_manual_enrol_users_router)
app.include_router(core_user_create_users_router)
app.include_router(identificacion_usuario)
app.include_router(prueba_conseguir_id)
app.include_router(validacion_cedula_router)
app.include_router(verificacion_inicial_archivo)
app.include_router(validacion_nombres_apellidos_router)
app.include_router(verificar_correos)
app.include_router(validacion_numeros_whatsapp_router)
app.include_router(normalizacion_router)
app.include_router(validacion_final)
app.include_router(validacion_cursos_certificado_router_prueba)
app.include_router(validacion_estudiantes_estatus_router)
# Moodle
app.include_router(usuarios_bd_router)
app.include_router(duracion_curso_y_descripcion_router)
app.include_router(nombres_cursos_router)

# WhatsApp
app.include_router(envio_mensajes_whatsapp_router)

@app.get('/', tags=['home'])
def message():
    response = requests.get('https://ipinfo.io/ip')
    ip_address = response.text.strip()
    return HTMLResponse(f'<h1>Universal Learning ADMIN MOODLE API</h1><p>Client IP: {ip_address}</p>')

