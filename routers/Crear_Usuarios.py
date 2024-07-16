from fastapi import APIRouter, HTTPException, UploadFile, File, FastAPI
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
import requests
import os
import pandas as pd
import re

core_user_create_users_router = APIRouter()

estudiantes_matricular = 'temp_files/estudiantes_validados.csv'

load_dotenv()
MOODLE_URL = os.getenv("MOODLE_URL")
MOODLE_TOKEN = os.getenv("MOODLE_TOKEN")

WS_FUNCTION = "core_user_create_users"

def validate_username(username):
    if len(username) > 100:
        raise ValueError("The username exceeds 100 characters.")
    regex = r'^[a-z0-9_.-]{1,100}$'
    if not re.match(regex, username):
        raise ValueError("Invalid username format.")
    return True

def validate_name(name):
    if len(name) > 100:
        raise ValueError("The name exceeds 100 characters.")
    regex = r'^[a-zA-Z\s]+$'
    if not re.match(regex, name):
        raise ValueError("Invalid name format.")
    return True

@core_user_create_users_router.post("/core_user_create_users_from_file/", tags=['Moodle'])
async def core_user_create_users_from_file():
    """
    Create multiple users from a CSV file.
    """
    try:
        df = pd.read_csv(estudiantes_matricular)
        df = df.astype(str)
        #df = df1[df1['Estado'] == 'NO está en la BD esa cédula']

        users_data = []
        responses = []

        for _, row in df.iterrows():
            try:
                validate_username(row['username'])
                validate_name(row['firstname'])
                validate_name(row['lastname'])
                # validate_email(row['email'])  # Uncomment and implement if needed

                user_data = {
                    "username": row['username'],
                    "firstname": row['firstname'],
                    "lastname": row['lastname'],
                    "email": row['email'],
                    "idnumber": row['username'],
                    "city": row['city'],
                    "country": row['country'],
                    "phone1": row['phone1'],
                }

                users_data.append({
                    "createpassword": 1,
                    "username": user_data["username"],
                    "auth": "manual",
                    "password": "P@ssw0rd123", 
                    "firstname": user_data["firstname"],
                    "lastname": user_data["lastname"],
                    "email": user_data["email"],
                    "idnumber": user_data["idnumber"],
                    #"city": user_data["city"],
                    #"phone1": user_data["phone1"],
                    #"country": user_data["country"]
                })

            except ValueError as ve:
                responses.append({"error": str(ve), "row": row.to_dict()})

        if users_data:
            params = {
                "wstoken": MOODLE_TOKEN,
                "wsfunction": WS_FUNCTION,
                "moodlewsrestformat": "json"
            }

            data = {}
            for i, user in enumerate(users_data):
                for key, value in user.items():
                    data[f"users[{i}][{key}]"] = value

            response = requests.post(f"{MOODLE_URL}/webservice/rest/server.php", params=params, data=data)
            responses.append(response.json())

        return {"output": responses}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
