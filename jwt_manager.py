import os
from dotenv import load_dotenv
from jwt import encode, decode
from fastapi.security import HTTPBearer
from fastapi import Request, HTTPException

load_dotenv()
mysecretkey = os.getenv("SECRETKEY_MATRICULAS")
usuario = os.getenv("USUARIO_MATRICULAS")

class JWTBearer(HTTPBearer):
    async def __call__(self, request: Request):
        auth = await super().__call__(request)
        data = validate_token(auth.credentials)
        if data['user'] != usuario:
            raise HTTPException(status_code=403, detail="Credenciales invalidas")

def create_token(data: dict):
    token: str = encode(payload=data, key=mysecretkey, algorithm="HS256")
    return token

def validate_token(token: str):
    data: dict = decode(token, key=mysecretkey, algorithms=['HS256'])
    return data