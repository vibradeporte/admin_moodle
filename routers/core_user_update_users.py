from fastapi import APIRouter, HTTPException, Form
from pydantic import BaseModel
import requests
import pandas as pd
import os
import pycountry

core_user_update_users_router = APIRouter()

WS_FUNCTION = "core_user_update_users"

def obtener_codigo_iso_pais(nombre_pais: str) -> str | None:
    try:
        pais = pycountry.countries.get(name=nombre_pais)
        return pais.alpha_2 if pais else 'SIN PAIS'
    except KeyError:
        return None


@core_user_update_users_router.post("/core_user_update_users/", tags=['Moodle'], status_code=200)
async def core_user_update_users(moodle_url: str = Form(...), moodle_token: str = Form(...)):

    data = {}
    df = pd.read_csv('temp_files/estudiantes_validados.csv')
    df['username'] = df['username'].apply(lambda x: str(x).replace('.0', '') if '.0' in str(x) else str(x))
    df["country"] = df["country"].apply(obtener_codigo_iso_pais)
    df = df.drop_duplicates(subset=['id'])
    if df is None:
        raise HTTPException(status_code=400, detail="No se encontr  el archivo 'temp_files/estudiantes_validados.csv'")

    for i, row in df.iterrows():
        USERID = row.get("userid")

        if USERID is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'userid'")
        
        USERNAME = row.get("username")
        if USERNAME is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'username'")
        
        FIRSTNAME = row.get("firstname")
        if FIRSTNAME is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'firstname'")
        
        LASTNAME = row.get("lastname")
        if LASTNAME is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'lastname'")
        
        EMAIL = row.get("email")
        if EMAIL is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'email'")
        
        CITY = row.get("city")
        if CITY is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'city'")
        
        COUNTRY = row.get("country")
        if COUNTRY is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'country'")
        
        DESCRIPTION = row.get("description")
        if DESCRIPTION is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'description'")
        
        FIRSTNAMEPHONETIC = ""
        LASTNAMEPHONETIC = row.get("lastnamephonetic")
        if LASTNAMEPHONETIC is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'lastnamephonetic'")
        
        MIDDLENAME = ""
        ALTERNATENAME = ""
        INTERESTS = ""
        IDNUMBER = row.get("username")
        if IDNUMBER is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'username'")
        
        INSTITUTION = ""
        DEPARTMENT = ""
        PHONE1 = row.get("phone1")
        if PHONE1 is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'phone1'")
        
        PHONE2 = ""
        ADDRESS = row.get("address")
        if ADDRESS is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'address'")

        data[f"users[{i}][id]"] = int(USERID)
        data[f"users[{i}][username]"] = USERNAME
        data[f"users[{i}][firstname]"] = FIRSTNAME
        data[f"users[{i}][lastname]"] = LASTNAME
        data[f"users[{i}][email]"] = EMAIL
        data[f"users[{i}][city]"] = CITY
        data[f"users[{i}][country]"] = COUNTRY
        data[f"users[{i}][description]"] = DESCRIPTION
        data[f"users[{i}][firstnamephonetic]"] = FIRSTNAMEPHONETIC
        data[f"users[{i}][lastnamephonetic]"] = LASTNAMEPHONETIC
        data[f"users[{i}][middlename]"] = MIDDLENAME
        data[f"users[{i}][alternatename]"] = ALTERNATENAME
        data[f"users[{i}][interests]"] = INTERESTS
        data[f"users[{i}][idnumber]"] = IDNUMBER
        data[f"users[{i}][institution]"] = INSTITUTION
        data[f"users[{i}][department]"] = DEPARTMENT
        data[f"users[{i}][phone1]"] = PHONE1
        data[f"users[{i}][phone2]"] = PHONE2
        data[f"users[{i}][address]"] = ADDRESS

    url = f"{moodle_url}/webservice/rest/server.php"
    params = {
        "wstoken": moodle_token,
        "wsfunction": WS_FUNCTION,
        "moodlewsrestformat": "json"
    }

    response = requests.post(url, params=params, data=data)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {"output": response.json()}

