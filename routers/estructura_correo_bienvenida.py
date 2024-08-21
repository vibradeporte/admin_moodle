from fastapi import FastAPI, UploadFile, APIRouter, HTTPException
from typing import List, Dict
import pandas as pd

app = FastAPI()
Bienvenida_correo_estudiantes_router = APIRouter()

def transformar_datos_bienvenida(datos: pd.DataFrame) -> List[Dict]:
    estructura_deseada = []    
    for _, fila in datos.iterrows():
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .content {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                }}
            </style>
        </head>
        <body>
            <img src="https://elaulavirtual.com/imagenes_mensajes/ins/ENCABEZADO_CORREOS_INS2.png" alt="Banner" class="banner">
            <div class="content">
                <p>Apreciado(a) {fila['firstname']} {fila['lastname']},</p>
                <p>Reciba un cordial saludo de bienvenida al curso {fila['NOMBRE_LARGO_CURSO']}.</p>
                <p>El ingreso al aula virtual se hace por la siguiente dirección: <a href="https://elaulavirtual.com/test">https://elaulavirtual.com/test</a></p>
                <p>Su usuario es su número de cédula: {fila['username']} (sin espacios, ni puntos, ni comas, ni apóstrofo) y su contraseña es: P@SsW0RD123</p>
                <p>Todos los recursos de estudio y evaluaciones estarán disponibles a partir de {fila['timestart']} y hasta el {fila['timeend']}, dado que el usuario y contraseña estarán habilitados por un plazo de {fila['enrolperiod']} días.</p>
                <p>Al finalizar el curso encontrará una encuesta de satisfacción, para nosotros es muy importante su diligenciamiento ya que nos permitirá conocer su opinión y hacer las mejoras correspondientes.</p>
                <p>Si necesita apoyo técnico puede hacer <a href="https://wa.me/573209939001">clic aquí para ir al CHAT de soporte de WhatsApp</a> o puede escribirnos al correo <a href="mailto:AulasVirtuales@Fasecolda.com">AulasVirtuales@Fasecolda.com</a></p>
                <p>Cordialmente,</p>
                <p>Soporte de Aula Virtuales INS.</p>
            </div>
        </body>
        </html>
        """
        
        item = {
            "from_e": "aulasvirtuales@fasecolda.com",
            "to": fila['email'],
            "subject": f"Bienvenida al Curso {fila['NOMBRE_LARGO_CURSO']}",
            "cc": fila['CORREO_SOLICITANTE'],
            "html_content": html_content,
            "content": f"Apreciado(a) {fila['firstname']} {fila['lastname']},\nReciba un cordial saludo de bienvenida al curso {fila['NOMBRE_LARGO_CURSO']}.\nEl ingreso al aula virtual se hace por la siguiente dirección: https://elaulavirtual.com/ins\nSu usuario es su número de cédula: {fila['username']} y su contraseña es: P@SsW0RD123 \nTodos los recursos de estudio y evaluaciones estarán disponibles hasta el {fila['timeend']}, dado que el usuario y contraseña estarán habilitados por un plazo de {fila['enrolperiod']} días.\nAl finalizar el curso encontrará una encuesta de satisfacción, para nosotros es muy importante su diligenciamiento ya que nos permitirá conocer su opinión y hacer las mejoras correspondientes.\nSi necesita apoyo técnico puede hacer clic aquí para ir al CHAT de soporte de WhatsApp o puede escribirnos al correo AulasVirtuales@Fasecolda.com\nCordialmente,\nSoporte de Aula Virtuales INS."
        }
        
        estructura_deseada.append(item)
    return estructura_deseada

@Bienvenida_correo_estudiantes_router.post("/Estructura_Correo_Bienvenida/")
async def bienvenida_correo():
    try:
        datos = pd.read_csv('temp_files/estudiantes_validados.csv')
        # Ensure 'timestart' and 'timeend' are datetime objects
        datos['timestart'] = pd.to_datetime(datos['timestart'], unit='s')
        datos['timeend'] = pd.to_datetime(datos['timeend'], unit='s')
        # Convert to date and calculate enrolperiod
        datos['timestart_date'] = datos['timestart'].dt.date
        datos['timeend_date'] = datos['timeend'].dt.date
        datos['enrolperiod'] = (datos['timeend'] - datos['timestart']).dt.days
        estructura_deseada = transformar_datos_bienvenida(datos)
        return estructura_deseada
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
