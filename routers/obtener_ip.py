from fastapi import FastAPI, APIRouter
import requests


obtener_ip = APIRouter()

@obtener_ip.get("/get_ip", tags=["Network"])
def get_ip():
    try:
        response = requests.get('https://ipinfo.io/ip')
        response.raise_for_status() 
        ip_address = response.text.strip()
        return {"ip": ip_address}
    except requests.RequestException as e:
        return {"error": str(e)}



