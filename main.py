from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from routers.upload_matricula import *


app = FastAPI()
app.title = "Universal Learning ADMIN MOODLE API "
app.version = "0.0.1"

app.include_router(upload_file_matricula)
app.include_router(verificar_correos)

@app.get('/', tags=['home'])
def message():
    return HTMLResponse('<h1>Universal Learning ADMIN MOODLE API</h1>')
