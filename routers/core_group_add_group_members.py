from fastapi import APIRouter, HTTPException, UploadFile, File
import requests
import os
from return_codes import *
import re
import pandas as pd

core_group_add_group_members_router = APIRouter()

MOODLE_URL = os.getenv("MOODLE_URL")
MOODLE_TOKEN = os.getenv("MOODLE_TOKEN")

WS_FUNCTION = "core_group_add_group_members"


@core_group_add_group_members_router.post("/core_group_add_group_members/", tags=['Moodle'])
async def core_group_add_group_members(file: UploadFile = File(...)):
    """
    ## **Descripción:**
    Agrega miembros al grupo.

    ## **Parámetros obligatorios:**
        - groupid -> Id del grupo. Debe ser un entero positivo. 
        - userid -> Id del usuario. Debe ser un entero positivo. 
    
     ## **Códigos retornados:**
        - 200 -> La operación se realizó correctamente.
        - 454 -> La cantidad de caracteres supera el límite de 10 para este KEY.
        - 460 -> La cantidad de caracteres es menor a lo permitido.
        - 474 -> Uno o varios caracteres ingresados no están permitidos en este campo. No se permiten letras, espacios ni números negativos.
        - 478 -> El usuario consultado no existe.
        - 479 -> El grupo consultado no existe

    """
    data = {}
    df = pd.read_csv('temp_files/estudiantes_validados.csv')
    i = 0
    for i, row in df.iterrows():
        GROUPID = row.get("groupid")
        USERID = row.get("userid")


        if GROUPID == None:
            codigo = FALTAN_CARACTERES
            mensaje = HTTP_MESSAGES.get(codigo)
            raise HTTPException(codigo, mensaje)

        GROUPID = str(GROUPID)
        if len(GROUPID) > 10:
            codigo = SOBRAN_CARACTERES_10
            mensaje = HTTP_MESSAGES.get(codigo)
            raise HTTPException(codigo, mensaje)
        
        regex = r'^[0-9]{1,10}$'
        if not re.match(regex, GROUPID):
            
            codigo = CARACTER_INVALIDO_ID
            mensaje = HTTP_MESSAGES.get(codigo)
            raise HTTPException(codigo, mensaje)



        if USERID == None:
            codigo = FALTAN_CARACTERES
            mensaje = HTTP_MESSAGES.get(codigo)
            raise HTTPException(codigo, mensaje)
        USERID = str(USERID)
        regex = r'^[0-9]{1,10}$'
        if not re.match(regex, USERID):
            
            codigo = CARACTER_INVALIDO_ID
            mensaje = HTTP_MESSAGES.get(codigo)
            raise HTTPException(codigo, mensaje)
        
        if len(USERID) > 10:
                codigo = SOBRAN_CARACTERES_10
                mensaje = HTTP_MESSAGES.get(codigo)
                raise HTTPException(codigo, mensaje)

        data[f"members[{i}][groupid]"]= GROUPID
        data[f"members[{i}][userid]"]= USERID
        i += 1

    url = f"{MOODLE_URL}/webservice/rest/server.php"
    params = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": WS_FUNCTION,
        "moodlewsrestformat": "json"
    }
    

    response = requests.post(url, params=params, data=data)
    response_dict = response.json()
    
    if response_dict == None:
        codigo = OK
        mensaje = HTTP_MESSAGES.get(codigo)
        raise HTTPException(codigo, mensaje)   
    elif 'message' in response_dict and response_dict['message'] == 'Usuario no válido':
        codigo = USER_NO_EXISTE
        mensaje = HTTP_MESSAGES.get(codigo)
        raise HTTPException(codigo, mensaje)
    elif 'message' in response_dict and response_dict['message'] == 'No se puede encontrar registro de datos en la tabla groups de la base de datos.':
        codigo = GROUP_NO_EXISTE
        mensaje = HTTP_MESSAGES.get(codigo)
        raise HTTPException(codigo, mensaje)
    elif 'message' in response_dict and response_dict['message'] == 'Detectado valor de parámetro no válido':
        codigo = GROUP_NO_EXISTE
        mensaje = HTTP_MESSAGES.get(codigo)
        raise HTTPException(codigo, mensaje)
    return {"output": response.json()}  
   