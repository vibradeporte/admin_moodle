from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
import os

app = FastAPI()
subida_de_archivo_router = APIRouter()

UPLOAD_DIRECTORY = "temp_files/"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

@subida_de_archivo_router.post("/Subir_Archivo/", tags=['Validacion_Inicial'])
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="El archivo no es un archivo Excel. Por favor, sube un archivo con extensión .xlsx o .xls.")
    
    try:
        contents = await file.read()
        new_file_name = f"validacion_archivo{os.path.splitext(file.filename)[1]}"
        file_path = os.path.join(UPLOAD_DIRECTORY, new_file_name)
        
        with open(file_path, 'wb') as f:
            f.write(contents)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hubo un error subiendo el archivo: {str(e)}")
    
    finally:
        file.file.close()

    return {"message": "Se ha subido el archivo exitosamente"}


