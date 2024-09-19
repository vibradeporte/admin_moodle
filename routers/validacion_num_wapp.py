from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import JSONResponse
import phonenumbers
import pandas as pd
import pycountry
import re

validacion_numeros_whatsapp_router = APIRouter()

# Función para obtener el código de país en formato alfa-2
def get_country_code(country_name):
    try:
        country = pycountry.countries.get(name=country_name)
        return country.alpha_2
    except:
        return None

# Función para añadir el código de país al número de teléfono
def prepend_country_code(phone_number, country_code):
    try:
        country_prefix = phonenumbers.country_code_for_region(country_code)
        full_number = f"+{country_prefix}{phone_number}"
        return full_number
    except:
        return phone_number

def limpiar_numero(numero):
    if pd.isnull(numero):  # Si el valor es nulo
        return 'SIN NUMERO DE WHATSAPP'
    numero_limpio = re.sub(r'\D', '', str(numero))  # Eliminar todo lo que no sea un dígito
    return numero_limpio if numero_limpio != '' else 'SIN NUMERO'

@validacion_numeros_whatsapp_router.post("/validar_numeros_whatsapp/", tags=['Whatsapp'])
async def validar_numeros_whatsapp():
    try:
        file_path = 'temp_files/validacion_inicial.xlsx'
        df = pd.read_excel(file_path, dtype={'NUMERO_MOVIL_WS_SIN_PAIS': str})

        # Limpiar los números en la columna 'NUMERO_MOVIL_WS_SIN_PAIS'
        df['NUMERO_MOVIL_WS_SIN_PAIS'] = df['NUMERO_MOVIL_WS_SIN_PAIS'].apply(limpiar_numero)

        # Asegurarse de que las columnas de validación existan
        if 'Numero_Wapp_Incorrecto' not in df.columns:
            df['Numero_Wapp_Incorrecto'] = None
        if 'Numero_Con_Prefijo' not in df.columns:
            df['Numero_Con_Prefijo'] = ''

        for index, row in df.iterrows():
            phone_number = str(row['NUMERO_MOVIL_WS_SIN_PAIS'])
            country_name = row['PAIS_DEL_MOVIL']
            print(f'NUMERO_MOVIL_WS_SIN_PAIS: {phone_number}, PAIS_DEL_MOVIL: {country_name}')
            
            # Verificar si el número es 0, None, NaN, o Null
            if phone_number in ['None', 'nan', '0', 'null', 'NaN', '', 'SIN NUMERO DE WHATSAPP']:
                df.at[index, 'Numero_Wapp_Incorrecto'] = 'NO'
                df.at[index, 'Numero_Con_Prefijo'] = 'SIN NUMERO DE WHATSAPP'
                continue
            
            country_code = get_country_code(country_name)
            if not country_code:
                df.at[index, 'Numero_Wapp_Incorrecto'] = 'SI'
                df.at[index, 'Numero_Con_Prefijo'] = 'SIN NUMERO DE WHATSAPP'
                continue
            
            # Verificar los dos primeros dígitos
            primeros_dos_digitos = phone_number[:2]
            country_code_for_validation = phonenumbers.country_code_for_region(country_code)
            
            if primeros_dos_digitos == str(country_code_for_validation):
                parsed_number = phonenumbers.parse("+" + phone_number)
                if phonenumbers.is_valid_number(parsed_number):
                    df.at[index, 'Numero_Wapp_Incorrecto'] = 'NO'
                    df.at[index, 'Numero_Con_Prefijo'] = '+' + phone_number
                else:
                    df.at[index, 'Numero_Wapp_Incorrecto'] = 'SI'
                    df.at[index, 'Numero_Con_Prefijo'] = '+' + phone_number
            else:
                full_phone_number = prepend_country_code(phone_number, country_code)
                df.at[index, 'Numero_Con_Prefijo'] = full_phone_number
                try:
                    parsed_number = phonenumbers.parse(full_phone_number)
                    if phonenumbers.is_valid_number(parsed_number):
                        df.at[index, 'Numero_Wapp_Incorrecto'] = 'NO'
                    else:
                        df.at[index, 'Numero_Wapp_Incorrecto'] = 'SI'
                except Exception as e:
                    df.at[index, 'Numero_Wapp_Incorrecto'] = 'SI'
                    df.at[index, 'Numero_Con_Prefijo'] = 'SIN NUMERO DE WHATSAPP'

        # Reemplazar valores NaN o vacíos en la columna Numero_Con_Prefijo con 'SIN NUMERO DE WHATSAPP'
        df['Numero_Con_Prefijo'] = df['Numero_Con_Prefijo'].replace('', 'SIN NUMERO DE WHATSAPP')

        # Guardar el archivo actualizado
        df.to_excel(file_path, index=False)

        # Contar resultados
        si_rows_count = (df['Numero_Wapp_Incorrecto'] == 'SI').sum()
        no_rows_count = (df['Numero_Wapp_Incorrecto'] == 'NO').sum()

        response_data = {
            "mensaje": "Resultados validación de números telefónicos de Whatsapp",
            "invalidos": int(si_rows_count),
            "validos": int(no_rows_count)
        }

        return JSONResponse(content=response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Un error ocurrió: {e}")





