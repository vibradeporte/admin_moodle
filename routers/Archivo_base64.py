from fastapi import FastAPI, HTTPException, APIRouter, Query
import base64
import os

Archivo_base64_router = APIRouter()

@Archivo_base64_router.get("/ArchivoBase64/", tags = ['Archivos'])
async def get_file_base64(file_path: str = Query(..., description="Path to the file")):
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    with open(file_path, 'rb') as file:
        file_content = file.read()
        base64_encoded = base64.b64encode(file_content).decode('utf-8')
    
    file_name = os.path.basename(file_path)
    file_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if file_name.endswith(".xlsx") else "application/octet-stream"
    
    response = {
        "content": base64_encoded,
        "name": file_name,
        "type": file_type
    }
    
    return response