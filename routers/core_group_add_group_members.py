from fastapi import APIRouter, HTTPException, Form, Depends
import requests
import pandas as pd
from jwt_manager import JWTBearer

# Definir el enrutador para la API de agregar miembros al grupo
core_group_add_group_members_router = APIRouter()

WS_FUNCTION = "core_group_add_group_members"

@core_group_add_group_members_router.post("/core_group_add_group_members/", tags=['Grupos'], dependencies=[Depends(JWTBearer())])
async def core_group_add_group_members(moodle_url: str = Form(...), moodle_token: str = Form(...)):
    """
    ## **Descripción:**
    Agrega miembros al grupo.

    ## **Parámetros obligatorios:**
        - moodle_url -> URL del servidor Moodle.
        - moodle_token -> Token de autenticación del servidor Moodle.
    
    ## **Códigos retornados:**
        - 200 -> La operación se realizó correctamente.
        - 454 -> La cantidad de caracteres supera el límite de 10 para este KEY.
        - 460 -> La cantidad de caracteres es menor a lo permitido.
        - 474 -> Uno o varios caracteres ingresados no están permitidos en este campo. No se permiten letras, espacios ni números negativos.
        - 478 -> El usuario consultado no existe.
        - 479 -> El grupo consultado no existe
    """
    data = {}
    df_estudiantes = pd.read_csv('temp_files/estudiantes_validados.csv')
    for indice, fila in df_estudiantes.iterrows():
        group_id = fila.get("groupid")
        user_id = fila.get("userid")

        data[f"members[{indice}][groupid]"] = group_id
        data[f"members[{indice}][userid]"] = user_id

    url = f"{moodle_url}/webservice/rest/server.php"
    params = {
        "wstoken": moodle_token,
        "wsfunction": WS_FUNCTION,
        "moodlewsrestformat": "json"
    }

    response = requests.post(url, params=params, data=data)
    response_dict = response.json()
    
    if response_dict is None:
        raise HTTPException(status_code=200, detail="La operación se realizó correctamente.")
    elif 'message' in response_dict and response_dict['message'] == 'Usuario no válido':
        raise HTTPException(status_code=478, detail="El usuario consultado no existe.")
    elif 'message' in response_dict and response_dict['message'] == 'No se puede encontrar registro de datos en la tabla groups de la base de datos.':
        raise HTTPException(status_code=479, detail="El grupo consultado no existe.")
    elif 'message' in response_dict and response_dict['message'] == 'Detectado valor de parámetro no válido':
        raise HTTPException(status_code=474, detail="Uno o varios caracteres ingresados no están permitidos en este campo. No se permiten letras, espacios ni números negativos.")
    
    return {"output": response.json()}
