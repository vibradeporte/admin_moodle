import os
from jwt_manager import create_token
from pydantic import BaseModel
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()
usuario = os.getenv("USUARIO_MATRICULAS")
clave = os.getenv("SECRETKEY_MATRICULAS")

class User(BaseModel):
    user: str
    password: str

userlog_router = APIRouter()

@userlog_router.post('/login', tags=['auth'])
def login(usr: User):
    if usr.user == usuario and usr.password == clave:
        token: str = create_token(usr.model_dump())
        return JSONResponse(status_code=200, content=token)
    return JSONResponse(status_code=401, content={"message": "Usuario o contraseña invalida"})