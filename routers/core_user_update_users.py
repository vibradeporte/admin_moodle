from fastapi import APIRouter, HTTPException, Form,Depends
from jwt_manager import JWTBearer
from pydantic import BaseModel
import requests
import pandas as pd
import os
import pycountry

core_user_update_users_router = APIRouter()

WS_FUNCTION = "core_user_update_users"

iso_paises = {
    "ANDORRA": "AD",
    "EMIRATOS ÁRABES UNIDOS": "AE",
    "AFGANISTÁN": "AF",
    "ANTIGUA Y BARBUDA": "AG",
    "ANGUILA": "AI",
    "ALBANIA": "AL",
    "ARMENIA": "AM",
    "ANGOLA": "AO",
    "ANTÁRTIDA": "AQ",
    "ARGENTINA": "AR",
    "SAMOA AMERICANA": "AS",
    "AUSTRIA": "AT",
    "AUSTRALIA": "AU",
    "ARUBA": "AW",
    "ISLAS ÅLAND": "AX",
    "AZERBAIYÁN": "AZ",
    "BOSNIA Y HERZEGOVINA": "BA",
    "BARBADOS": "BB",
    "BANGLADÉS": "BD",
    "BÉLGICA": "BE",
    "BURKINA FASO": "BF",
    "BULGARIA": "BG",
    "BARÉIN": "BH",
    "BURUNDI": "BI",
    "BENÍN": "BJ",
    "SAN BARTOLOMÉ": "BL",
    "BERMUDAS": "BM",
    "BRUNÉI": "BN",
    "BOLIVIA": "BO",
    "BONAIRE, SAN EUSTAQUIO Y SABA": "BQ",
    "BRASIL": "BR",
    "BAHAMAS": "BS",
    "BUTÁN": "BT",
    "ISLA BOUVET": "BV",
    "BOTSUANA": "BW",
    "BIELORRUSIA": "BY",
    "BELICE": "BZ",
    "CANADÁ": "CA",
    "ISLAS COCOS": "CC",
    "CONGO": "CD",
    "REPÚBLICA CENTROAFRICANA": "CF",
    "CONGO": "CG",
    "SUIZA": "CH",
    "CÔTE D'IVOIRE": "CI",
    "ISLAS COOK": "CK",
    "CHILE": "CL",
    "CAMERÚN": "CM",
    "CHINA": "CN",
    "COLOMBIA": "CO",
    "COSTA RICA": "CR",
    "CUBA": "CU",
    "CABO VERDE": "CV",
    "CURAZAO": "CW",
    "ISLA DE NAVIDAD": "CX",
    "CHIPRE": "CY",
    "REPÚBLICA CHECA": "CZ",
    "ALEMANIA": "DE",
    "YIBUTI": "DJ",
    "DINAMARCA": "DK",
    "DOMINICA": "DM",
    "REPÚBLICA DOMINICANA": "DO",
    "ARGELIA": "DZ",
    "ECUADOR": "EC",
    "ESTONIA": "EE",
    "EGIPTO": "EG",
    "SAHARA OCCIDENTAL": "EH",
    "ERITREA": "ER",
    "ESPAÑA": "ES",
    "ETIOPÍA": "ET",
    "FINLANDIA": "FI",
    "FIYI": "FJ",
    "ISLAS MALVINAS": "FK",
    "MICRONESIA": "FM",
    "ISLAS FEROE": "FO",
    "FRANCIA": "FR",
    "GABÓN": "GA",
    "REINO UNIDO": "GB",
    "GRANADA": "GD",
    "GEORGIA": "GE",
    "GUAYANA FRANCESA": "GF",
    "GUERNSEY": "GG",
    "GHANA": "GH",
    "GIBRALTAR": "GI",
    "GROENLANDIA": "GL",
    "GAMBIA": "GM",
    "GUINEA": "GN",
    "GUADALUPE": "GP",
    "GUINEA ECUATORIAL": "GQ",
    "GRECIA": "GR",
    "GEORGIA DEL SUR E ISLAS SANDWICH DEL SUR": "GS",
    "GUATEMALA": "GT",
    "GUAM": "GU",
    "GUINEA-BISSAU": "GW",
    "GUYANA": "GY",
    "HONG KONG": "HK",
    "ISLAS HEARD Y MCDONALD": "HM",
    "HONDURAS": "HN",
    "CROACIA": "HR",
    "HAITÍ": "HT",
    "HUNGRÍA": "HU",
    "INDONESIA": "ID",
    "IRLANDA": "IE",
    "ISRAEL": "IL",
    "ISLA DE MAN": "IM",
    "INDIA": "IN",
    "TERRITORIO BRITÁNICO DEL OCÉANO ÍNDICO": "IO",
    "IRAK": "IQ",
    "IRÁN": "IR",
    "ISLANDIA": "IS",
    "ITALIA": "IT",
    "JERSEY": "JE",
    "JAMAICA": "JM",
    "JORDANIA": "JO",
    "JAPÓN": "JP",
    "KENIA": "KE",
    "KIRGUISTÁN": "KG",
    "CAMBOYA": "KH",
    "KIRIBATI": "KI",
    "COMORAS": "KM",
    "SAN CRISTÓBAL Y NIEVES": "KN",
    "COREA DEL NORTE": "KP",
    "COREA DEL SUR": "KR",
    "KUWAIT": "KW",
    "ISLAS CAIMÁN": "KY",
    "KAZAJISTÁN": "KZ",
    "REPÚBLICA DEMOCRÁTICA POPULAR LAO": "LA",
    "LÍBANO": "LB",
    "SANTA LUCÍA": "LC",
    "LIECHTENSTEIN": "LI",
    "SRI LANKA": "LK",
    "LIBERIA": "LR",
    "LESOTO": "LS",
    "LITUANIA": "LT",
    "LUXEMBURGO": "LU",
    "LETONIA": "LV",
    "LIBIA": "LY",
    "MARRUECOS": "MA",
    "MÓNACO": "MC",
    "MOLDAVIA": "MD",
    "MONTENEGRO": "ME",
    "SAINT MARTIN": "MF",
    "MADAGASCAR": "MG",
    "ISLAS MARSHALL": "MH",
    "MACEDONIA DEL NORTE": "MK",
    "MALÍ": "ML",
    "MYANMAR": "MM",
    "MONGOLIA": "MN",
    "MACAO": "MO",
    "ISLAS MARIANAS DEL NORTE": "MP",
    "MARTINICA": "MQ",
    "MAURITANIA": "MR",
    "MONTSERRAT": "MS",
    "MALTA": "MT",
    "MAURICIO": "MU",
    "MALDIVAS": "MV",
    "MALAUI": "MW",
    "MÉXICO": "MX",
    "MALASIA": "MY",
    "MOZAMBIQUE": "MZ",
    "NAMIBIA": "NA",
    "NUEVA CALEDONIA": "NC",
    "NÍGER": "NE",
    "ISLA NORFOLK": "NF",
    "NIGERIA": "NG",
    "NICARAGUA": "NI",
    "PAÍSES BAJOS": "NL",
    "NORUEGA": "NO",
    "NEPAL": "NP",
    "NAURU": "NR",
    "NIUE": "NU",
    "NUEVA ZELANDA": "NZ",
    "OMÁN": "OM",
    "PANAMÁ": "PA",
    "PERÚ": "PE",
    "POLINESIA FRANCESA": "PF",
    "PAPÚA NUEVA GUINEA": "PG",
    "FILIPINAS": "PH",
    "PAKISTÁN": "PK",
    "POLONIA": "PL",
    "SAN PEDRO Y MIQUELÓN": "PM",
    "PITCAIRN": "PN",
    "PUERTO RICO": "PR",
    "PALESTINA": "PS",
    "PORTUGAL": "PT",
    "PALAOS": "PW",
    "PARAGUAY": "PY",
    "CATAR": "QA",
    "REUNIÓN": "RE",
    "RUMANIA": "RO",
    "SERBIA": "RS",
    "RUSIA": "RU",
    "RUANDA": "RW",
    "ARABIA SAUDITA": "SA",
    "ISLAS SALOMÓN": "SB",
    "SEYCHELLES": "SC",
    "SUDÁN": "SD",
    "SUECIA": "SE",
    "SINGAPUR": "SG",
    "SANTA ELENA, ASCENSIÓN Y TRISTÁN DE ACUÑA": "SH",
    "ESLOVENIA": "SI",
    "SVALBARD Y JAN MAYEN": "SJ",
    "ESLOVAQUIA": "SK",
    "SIERRA LEONA": "SL",
    "SAN MARINO": "SM",
    "SENEGAL": "SN",
    "SOMALIA": "SO",
    "SURINAM": "SR",
    "SUDÁN DEL SUR": "SS",
    "SANTO TOMÉ Y PRÍNCIPE": "ST",
    "EL SALVADOR": "SV",
    "SINT MAARTEN": "SX",
    "REPÚBLICA ÁRABE SIRIA": "SY",
    "ESVATINI": "SZ",
    "ISLAS TURCAS Y CAICOS": "TC",
    "CHAD": "TD",
    "TIERRAS AUSTRALES FRANCESAS": "TF",
    "TOGO": "TG",
    "TAILANDIA": "TH",
    "TAYIKISTÁN": "TJ",
    "TOKELAU": "TK",
    "TIMOR-LESTE": "TL",
    "TURKMENISTÁN": "TM",
    "TÚNEZ": "TN",
    "TONGA": "TO",
    "TURQUÍA": "TR",
    "TRINIDAD Y TOBAGO": "TT",
    "TUVALU": "TV",
    "TAIWÁN": "TW",
    "TANZANIA, REPÚBLICA UNIDA DE": "TZ",
    "UCRANIA": "UA",
    "UGANDA": "UG",
    "ISLAS MENORES ALEJADAS DE LOS ESTADOS UNIDOS": "UM",
    "ESTADOS UNIDOS": "US",
    "URUGUAY": "UY",
    "UZBEKISTÁN": "UZ",
    "CIUDAD DEL VATICANO": "VA",
    "SAN VICENTE Y LAS GRANADINAS": "VC",
    "VENEZUELA": "VE",
    "ISLAS VÍRGENES BRITÁNICAS": "VG",
    "ISLAS VÍRGENES DE LOS ESTADOS UNIDOS": "VI",
    "VIET NAM": "VN",
    "VANUATU": "VU",
    "WALLIS Y FUTUNA": "WF",
    "SAMOA": "WS",
    "KOSOVO": "XK",
    "YEMEN": "YE",
    "MAYOTTE": "YT",
    "SUDÁFRICA": "ZA",
    "ZAMBIA": "ZM",
    "ZIMBABUE": "ZW"
}
def obtener_codigo_iso_pais(nombre_pais: str) -> str:
    """
    Devuelve el código ISO del país correspondiente al nombre proporcionado.

    Parameters:
    nombre_pais (str): Nombre del país en español.

    Returns:
    str: Código ISO del país si se encuentra, de lo contrario 'SIN PAIS'.
    """
    return iso_paises.get(nombre_pais.upper(), 'SIN PAIS')

@core_user_update_users_router.post("/api2/core_user_update_users/", tags=['Moodle'], status_code=200, dependencies=[Depends(JWTBearer())])
async def core_user_update_users(moodle_url: str = Form(...), moodle_token: str = Form(...)):
    """
    ## **Descripción:**
    Actualiza la información de usuarios en Moodle.

    ## **Parámetros obligatorios:**
        - moodle_url -> URL del servidor Moodle.
        - moodle_token -> Token de autenticación del servidor Moodle.
    """
    data = {}
    try:
        df = pd.read_csv('temp_files/estudiantes_validados.csv')
    except Exception as e:
        raise HTTPException(status_code=400, detail="Error al leer el archivo CSV")

    df['username'] = df['username'].apply(lambda x: str(x).replace('.0', '') if '.0' in str(x) else str(x))
    df['phone1'] = df['phone1'].apply(lambda x: str(x).replace('.0', '') if '.0' in str(x) else str(x)).apply(lambda x: str(x).replace('nan', '') if 'nan' in str(x) else str(x)).astype(str)
    df["country"] = df["country"].apply(obtener_codigo_iso_pais)
    df = df.drop_duplicates(subset=['userid'])

    if df is None:
        raise HTTPException(status_code=400, detail="No se encontró el archivo 'temp_files/estudiantes_validados.csv'")

    for i, row in df.iterrows():
        user_id = row.get("userid")
        if user_id is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'userid'")

        try:
            data[f"users[{i}][id]"] = int(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"El campo 'userid' con valor '{user_id}' en la fila {i} no es convertible a entero")

        data[f"users[{i}][username]"] = row.get("username", "")
        data[f"users[{i}][suspended]"] = 0
        data[f"users[{i}][password]"] = row.get("password", "")
        data[f"users[{i}][firstname]"] = row.get("firstname", "")
        data[f"users[{i}][lastname]"] = row.get("lastname", "")
        data[f"users[{i}][email]"] = row.get("email", "")
        data[f"users[{i}][city]"] = row.get("city", "")
        data[f"users[{i}][country]"] = row.get("country", "")
        data[f"users[{i}][description]"] = row.get("description", "")
        data[f"users[{i}][firstnamephonetic]"] = ""
        data[f"users[{i}][lastnamephonetic]"] = row.get("lastnamephonetic", "")
        data[f"users[{i}][middlename]"] = ""
        data[f"users[{i}][alternatename]"] = ""
        data[f"users[{i}][interests]"] = ""
        data[f"users[{i}][idnumber]"] = row.get("username", "")
        data[f"users[{i}][institution]"] = row.get("EMPRESA", "")
        data[f"users[{i}][department]"] = ""
        data[f"users[{i}][phone1]"] = row.get("phone1", "")
        data[f"users[{i}][phone2]"] = ""
        data[f"users[{i}][address]"] = row.get("address", "")

    url = f"{moodle_url}/webservice/rest/server.php"
    params = {
        "wstoken": moodle_token,
        "wsfunction": WS_FUNCTION,
        "moodlewsrestformat": "json"
    }

    response = requests.post(url, params=params, data=data)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {"output": response.json()}
