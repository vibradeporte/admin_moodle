from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
import phonenumbers
import pandas as pd
import pycountry


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

@validacion_numeros_whatsapp_router.post("/validar_numeros_whatsapp/", tags=['Whatsapp'])
async def validar_numeros_whatsapp():
    try:
        file_path = 'temp_files/validacion_inicial.xlsx'
        df = pd.read_excel(file_path)
        
        # Ensure the columns exist
        if 'Numero_Wapp_Incorrecto' not in df.columns:
            df['Numero_Wapp_Incorrecto'] = None
        if 'Numero_Con_Prefijo' not in df.columns:
            df['Numero_Con_Prefijo'] = None
        
        for index, row in df.iterrows():
            phone_number = str(row['NUMERO_MOVIL_WS_SIN_PAIS'])
            country_name = row['PAIS_DEL_MOVIL']
            print(f'NUMERO_MOVIL_WS_SIN_PAIS: {phone_number}, PAIS_DEL_MOVIL: {country_name}')
            
            # Verificar si el número es 0, None, NaN, o Null
            if pd.isna(phone_number) or phone_number in ['None', 'nan', '0', 'null', 'NaN']:
                df.at[index, 'Numero_Wapp_Incorrecto'] = 'NO'
                continue
            
            country_code = get_country_code(country_name)
            if not country_code:
                df.at[index, 'Numero_Wapp_Incorrecto'] = 'SI'
                continue
            
            # Verificar los dos primeros dígitos
            primeros_dos_digitos = phone_number[:2]
            country_code_for_validation = phonenumbers.country_code_for_region(country_code)
            
            if primeros_dos_digitos == str(country_code_for_validation):
                parsed_number = phonenumbers.parse("+" + phone_number)
                if phonenumbers.is_valid_number(parsed_number):
                    df.at[index, 'Numero_Wapp_Incorrecto'] = 'NO'
                else:
                    df.at[index, 'Numero_Wapp_Incorrecto'] = 'SI'
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
        
        df.to_excel(file_path, index=False)
        si_rows_count = (df['Numero_Wapp_Incorrecto'] == 'SI').sum()
        no_rows_count = (df['Numero_Wapp_Incorrecto'] == 'NO').sum()

        message = (
            f"Resultados validación de números telefónicos de Whatsapp: \n"
            f"{si_rows_count} Números telefónicos inválidos \n"
            f"{no_rows_count} Números telefónicos válidos \n"
        )

        return PlainTextResponse(content=message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Un error ocurrió: {e}")










