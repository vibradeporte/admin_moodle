from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import phonenumbers
import pandas as pd
import pycountry
import re
from jwt_manager import JWTBearer

validacion_numeros_whatsapp_router = APIRouter()

def get_country_code(country_name: str) -> str:
    """
    Obtiene el código de país en formato alfa-2 a partir del nombre del país.

    :param country_name: Nombre del país.
    :type country_name: str
    :return: Código de país en formato alfa-2.
    :rtype: str
    """
    try:
        country = pycountry.countries.get(name=country_name)
        return country.alpha_2 if country else None
    except Exception:
        return None

def prepend_country_code(phone_number: str, country_code: str) -> str:
    """
    Añade el código de país al número de teléfono.

    :param phone_number: Número de teléfono sin el código de país.
    :type phone_number: str
    :param country_code: Código de país en formato alfa-2.
    :type country_code: str
    :return: Número de teléfono completo con el prefijo del país.
    :rtype: str
    """
    try:
        country_prefix = phonenumbers.country_code_for_region(country_code)
        full_number = f"+{country_prefix}{phone_number}"
        return full_number
    except Exception:
        return phone_number

def limpiar_numero(numero: str) -> str:
    """
    Limpia el número de teléfono eliminando caracteres no numéricos.

    :param numero: Número de teléfono a limpiar.
    :type numero: str
    :return: Número de teléfono limpio o un mensaje si no es válido.
    :rtype: str
    """
    if pd.isnull(numero):
        return 'SIN NUMERO DE WHATSAPP'
    numero_limpio = re.sub(r'\D', '', str(numero))
    return numero_limpio if numero_limpio != '' else 'SIN NUMERO'

@validacion_numeros_whatsapp_router.post("/api2/validar_numeros_whatsapp/", tags=['Whatsapp'], dependencies=[Depends(JWTBearer())])
async def validar_numeros_whatsapp():
    """
    Valida los números de teléfono de WhatsApp de los estudiantes en un archivo de Excel.

    :return: JSONResponse con los resultados de la validación de números telefónicos.
    :rtype: JSONResponse
    """
    try:
        # Ruta del archivo Excel a validar
        file_path = 'temp_files/validacion_inicial.xlsx'
        df_estudiantes = pd.read_excel(file_path, dtype={'NUMERO_MOVIL_WS_SIN_PAIS': str})

        # Limpiar los números en la columna 'NUMERO_MOVIL_WS_SIN_PAIS'
        df_estudiantes['NUMERO_MOVIL_WS_SIN_PAIS'] = df_estudiantes['NUMERO_MOVIL_WS_SIN_PAIS'].apply(limpiar_numero)

        # Asegurarse de que las columnas de validación existan
        if 'Numero_Wapp_Incorrecto' not in df_estudiantes.columns:
            df_estudiantes['Numero_Wapp_Incorrecto'] = None
        if 'Numero_Con_Prefijo' not in df_estudiantes.columns:
            df_estudiantes['Numero_Con_Prefijo'] = ''

        for index, fila in df_estudiantes.iterrows():
            phone_number = str(fila['NUMERO_MOVIL_WS_SIN_PAIS'])
            country_name = fila['PAIS_DEL_MOVIL']
            print(f'NUMERO_MOVIL_WS_SIN_PAIS: {phone_number}, PAIS_DEL_MOVIL: {country_name}')
            
            # Verificar si el número es 0, None, NaN, o vacío
            if phone_number in ['None', 'nan', '0', 'null', 'NaN', '', 'SIN NUMERO DE WHATSAPP']:
                df_estudiantes.at[index, 'Numero_Wapp_Incorrecto'] = 'NO'
                df_estudiantes.at[index, 'Numero_Con_Prefijo'] = 'SIN NUMERO DE WHATSAPP'
                continue
            
            country_code = get_country_code(country_name)
            if not country_code:
                df_estudiantes.at[index, 'Numero_Wapp_Incorrecto'] = 'SI'
                df_estudiantes.at[index, 'Numero_Con_Prefijo'] = 'SIN NUMERO DE WHATSAPP'
                continue
            
            # Verificar los dos primeros dígitos
            primeros_dos_digitos = phone_number[:2]
            country_code_for_validation = phonenumbers.country_code_for_region(country_code)
            
            if primeros_dos_digitos == str(country_code_for_validation):
                try:
                    parsed_number = phonenumbers.parse("+" + phone_number)
                    if phonenumbers.is_valid_number(parsed_number):
                        df_estudiantes.at[index, 'Numero_Wapp_Incorrecto'] = 'NO'
                        df_estudiantes.at[index, 'Numero_Con_Prefijo'] = '+' + phone_number
                    else:
                        df_estudiantes.at[index, 'Numero_Wapp_Incorrecto'] = 'SI'
                        df_estudiantes.at[index, 'Numero_Con_Prefijo'] = '+' + phone_number
                except Exception:
                    df_estudiantes.at[index, 'Numero_Wapp_Incorrecto'] = 'SI'
                    df_estudiantes.at[index, 'Numero_Con_Prefijo'] = 'SIN NUMERO DE WHATSAPP'
            else:
                full_phone_number = prepend_country_code(phone_number, country_code)
                df_estudiantes.at[index, 'Numero_Con_Prefijo'] = full_phone_number
                try:
                    parsed_number = phonenumbers.parse(full_phone_number)
                    if phonenumbers.is_valid_number(parsed_number):
                        df_estudiantes.at[index, 'Numero_Wapp_Incorrecto'] = 'NO'
                    else:
                        df_estudiantes.at[index, 'Numero_Wapp_Incorrecto'] = 'SI'
                except Exception:
                    df_estudiantes.at[index, 'Numero_Wapp_Incorrecto'] = 'SI'
                    df_estudiantes.at[index, 'Numero_Con_Prefijo'] = 'SIN NUMERO DE WHATSAPP'

        # Reemplazar valores NaN o vacíos en la columna Numero_Con_Prefijo con 'SIN NUMERO DE WHATSAPP'
        df_estudiantes['Numero_Con_Prefijo'] = df_estudiantes['Numero_Con_Prefijo'].replace('', 'SIN NUMERO DE WHATSAPP')

        # Guardar el archivo actualizado
        df_estudiantes.to_excel(file_path, index=False)

        # Contar resultados
        si_rows_count = (df_estudiantes['Numero_Wapp_Incorrecto'] == 'SI').sum()
        no_rows_count = (df_estudiantes['Numero_Wapp_Incorrecto'] == 'NO').sum()

        response_data = {
            "mensaje": "Resultados validación de números telefónicos de Whatsapp",
            "invalidos": int(si_rows_count),
            "validos": int(no_rows_count)
        }

        return JSONResponse(content=response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Un error ocurrió: {e}")
