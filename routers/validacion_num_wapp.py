from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import JSONResponse
import phonenumbers
import pandas as pd
import pycountry

validacion_numeros_whatsapp_router = APIRouter()

def get_country_code(country_name):
    try:
        country = pycountry.countries.get(name=country_name)
        return country.alpha_2
    except:
        return None

def prepend_country_code(phone_number, country_code):
    try:
        country_prefix = phonenumbers.country_code_for_region(country_code)
        full_number = f"+{country_prefix}{phone_number}"
        return full_number
    except:
        return phone_number

@validacion_numeros_whatsapp_router.post("/validar_numeros_whatsapp/", tags=['Validacion_Secundaria'])
async def validar_numeros_whatsapp():
    try:
        file_path = 'temp_files/validacion_inicial.xlsx'
        invalid_file_path = 'temp_files/invalidos_matricula_por_wapp.xlsx'
        df = pd.read_excel(file_path)
        
        # Ensure the columns exist
        if 'Numero_Wapp_Incorrecto' not in df.columns:
            df['Numero_Wapp_Incorrecto'] = None
        if 'Numero_Con_Prefijo' not in df.columns:
            df['Numero_Con_Prefijo'] = None
        
        for index, row in df.iterrows():
            phone_number = row['NUMERO_MOVIL_WS_SIN_PAIS']
            country_name = row['PAIS_DEL_MOVIL']
            print(f'NUMERO_MOVIL_WS_SIN_PAIS: {phone_number}, PAIS_DEL_MOVIL: {country_name}')
            
            country_code = get_country_code(country_name)
            if not country_code:
                df.at[index, 'Numero_Wapp_Incorrecto'] = 'SI'
                continue
            
            full_phone_number = prepend_country_code(phone_number, country_code)
            df.at[index, 'Numero_Con_Prefijo'] = full_phone_number
            
            try:
                parsed_number = phonenumbers.parse(full_phone_number)
                if not phonenumbers.is_valid_number(parsed_number):
                    df.at[index, 'Numero_Wapp_Incorrecto'] = 'SI'
                    continue
                phone_country_code = phonenumbers.region_code_for_number(parsed_number)
                if phone_country_code != country_code:
                    df.at[index, 'Numero_Wapp_Incorrecto'] = 'SI'
                else:
                    df.at[index, 'Numero_Wapp_Incorrecto'] = 'NO'
            except Exception as e:
                df.at[index, 'Numero_Wapp_Incorrecto'] = 'SI'
        
        invalid_df = df[df['Numero_Wapp_Incorrecto'] == 'SI']
        valid_df = df[df['Numero_Wapp_Incorrecto'] == 'NO']
        
        invalid_df.to_excel(invalid_file_path, index=False)
        valid_df.to_excel(file_path, index=False)

        si_rows_count = len(invalid_df)
        no_rows_count = len(valid_df)

        message = (
            f"VALIDACIÓN DE NÚMEROS TELEFONICOS DE WHATSAPP: "
            f"{si_rows_count} NÚMEROS TELEFÓNICOS INVALIDOS, "
            f"{no_rows_count} NÚMEROS TELEFÓNICOS VALIDOS"
        )

        return JSONResponse(content={'message': message})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Un error ocurrió: {e}")



