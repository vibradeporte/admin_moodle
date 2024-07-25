from fastapi import APIRouter, HTTPException, Form
from pydantic import BaseModel
import requests
import pandas as pd
import os

core_user_update_users_router = APIRouter()

WS_FUNCTION = "core_user_update_users"

@core_user_update_users_router.post("/core_user_update_users/", tags=['Moodle'], status_code=200)
async def core_user_update_users(moodle_url: str = Form(...), moodle_token: str = Form(...)):

    data = {}
    df = pd.read_csv('temp_files/estudiantes_validados.csv')
    
    for i, row in df.iterrows():
        USERID = row.get("userid")
        USERNAME = row.get("username", "")
        FIRSTNAME = row.get("firstname", "")
        LASTNAME = row.get("lastname", "")
        EMAIL = row.get("email", "")
        CITY = row.get("city", "")
        COUNTRY = row.get("country", "")
        DESCRIPTION = row.get("description", "")
        FIRSTNAMEPHONETIC = ""
        LASTNAMEPHONETIC = row.get("lastnamephonetic","")
        MIDDLENAME = ""
        ALTERNATENAME = ""
        INTERESTS = ""
        IDNUMBER = row.get("username", "")
        INSTITUTION = ""
        DEPARTMENT = ""
        PHONE1 = row.get("phone1", "")
        PHONE2 = ""
        ADDRESS = row.get("address", "")

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
        data[f"users[{i}][phone1]"] = int(PHONE1)
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
