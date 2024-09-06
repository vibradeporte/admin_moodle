import os
import re
import pandas as pd
from datetime import datetime
from fastapi import APIRouter, HTTPException
from sqlalchemy import create_engine, text
from utils import construir_url_mysql
from dotenv import load_dotenv

creacion_contrasena_router = APIRouter()

# Cargar variables de entorno
load_dotenv()
usuario_base_datos = os.getenv("USER_DB_UL_ADMIN")
contrasena_base_datos = os.getenv("PASS_DB_UL_ADMIN")
host_base_datos = os.getenv("HOST_DB_ADMIN")
nombre_base_datos = os.getenv("NAME_DB_UL_ADMIN")

# Construir la URL de conexión a la base de datos
url_base_datos = construir_url_mysql(
    usuario_base_datos, contrasena_base_datos, host_base_datos, '3306', nombre_base_datos
)

def generar_contrasena(politica_contrasena: str, username: None) -> str:
    """
    Genera una contraseña basándose en la política de contraseña y el nombre de usuario.

    Args:
        politica_contrasena (str): La política de contraseña.
        username (str): El nombre de usuario para personalizar la contraseña (opcional).

    Returns:
        str: La contraseña generada.

    Raises:
        ValueError: Si la política de contraseña no contiene una expresión válida.
    """
    # Ejemplo: Generar una contraseña simple combinando la política y el username
    patron_cadena_texto = r":\s*([^\"]+)"
    match = re.search(patron_cadena_texto, politica_contrasena)
    if not match:
        raise ValueError("La política de contraseña no contiene una expresión válida.")
    
    return match.group(1)

@creacion_contrasena_router.post("/creacion_contrasena/", tags=['contrasena'], status_code=200)
async def creacion_contrasena(id_usuario_matricula: int):
    try:
        # Crear motor de conexión a la base de datos
        motor_base_datos = create_engine(url_base_datos)
        
        # Ruta del archivo de entrada
        archivo_de_entrada = 'temp_files/estudiantes_validados.csv'
        if not os.path.exists(archivo_de_entrada):
            raise HTTPException(status_code=404, detail="El archivo estudiantes_validados.csv no existe.")
        
        # Cargar los datos del archivo CSV
        df_estudiantes = pd.read_csv(archivo_de_entrada)
        
        # Consultar la política de contraseña desde la base de datos
        with motor_base_datos.connect() as connection:
            consulta_sql = text("""
                SELECT
                    c.POLITICA_CONTRASENA as POLITICA_CONTRASENA
                FROM
                    USUARIO AS u
                JOIN CLIENTE AS c ON u.FID_CLIENTE = c.ID_CLIENTE
                WHERE
                    u.ID_USUARIO = :ID_USUARIO;
            """).params(ID_USUARIO=id_usuario_matricula)
            
            row = connection.execute(consulta_sql).fetchone()
            if row:
                politica_contrasena = row[0]
            else:
                raise HTTPException(status_code=400, detail="No se encontró la política de contraseña para el usuario.")
        
        # Generar la contraseña para cada estudiante
        df_estudiantes['password'] = df_estudiantes['username'].apply(
            lambda username: eval(generar_contrasena(politica_contrasena, username))
        )
        
        # Guardar los cambios en el archivo CSV
        df_estudiantes.to_csv(archivo_de_entrada, index=False)
        
        return {
            "message": "Contraseñas generadas correctamente."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante la creación de contraseñas: {str(e)}")
