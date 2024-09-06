from fastapi import APIRouter, HTTPException, Form
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
    return iso_paises.get(nombre_pais.upper(), 'SIN PAIS')


@core_user_update_users_router.post("/core_user_update_users/", tags=['Moodle'], status_code=200)
async def core_user_update_users(moodle_url: str = Form(...), moodle_token: str = Form(...)):

    data = {}
    df = pd.read_csv('temp_files/estudiantes_validados.csv')
    df['username'] = df['username'].apply(lambda x: str(x).replace('.0', '') if '.0' in str(x) else str(x))
    df["country"] = df["country"].apply(obtener_codigo_iso_pais)
    df = df.drop_duplicates(subset=['userid'])
    if df is None:
        raise HTTPException(status_code=400, detail="No se encontr  el archivo 'temp_files/estudiantes_validados.csv'")

    for i, row in df.iterrows():
        USERID = row.get("userid")

        if USERID is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'userid'")
        
        USERNAME = row.get("username")
        if USERNAME is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'username'")
        
        PASSWORD = row.get("password")
        if PASSWORD is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'password'")
        
        FIRSTNAME = row.get("firstname")
        if FIRSTNAME is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'firstname'")
        
        LASTNAME = row.get("lastname")
        if LASTNAME is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'lastname'")
        
        EMAIL = row.get("email")
        if EMAIL is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'email'")
        
        CITY = row.get("city")
        if CITY is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'city'")
        
        COUNTRY = row.get("country")
        if COUNTRY is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'country'")
        
        DESCRIPTION = row.get("description")
        if DESCRIPTION is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'description'")
        
        FIRSTNAMEPHONETIC = ""
        LASTNAMEPHONETIC = row.get("lastnamephonetic")
        if LASTNAMEPHONETIC is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'lastnamephonetic'")
        
        MIDDLENAME = ""
        ALTERNATENAME = ""
        INTERESTS = ""
        IDNUMBER = row.get("username")
        if IDNUMBER is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'username'")
        
        INSTITUTION = ""
        DEPARTMENT = ""
        PHONE1 = row.get("phone1")
        if PHONE1 is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'phone1'")
        
        PHONE2 = ""
        ADDRESS = row.get("address")
        if ADDRESS is None:
            raise HTTPException(status_code=400, detail="El archivo 'temp_files/estudiantes_validados.csv' no tiene la columna 'address'")

        data[f"users[{i}][id]"] = int(USERID)
        data[f"users[{i}][username]"] = USERNAME
        data[f"users[{i}][password]"] = PASSWORD
        data[f"users[{i}][firstname]"] = FIRSTNAME
        data[f"users[{i}][lastname]"] = LASTNAME
        data[f"users[{i}][email]"] = EMAIL
        data[f"users[{i}][city]"] = CITY
        data[f"users[{i}][country]"] = COUNTRY
        data[f"users[{i}][description]"] = DESCRIPTION
        data[f"users[{i}][firstnamephonetic]"] = FIRSTNAMEPHONETIC
        data[f"users[{i}][lastnamephonetic]"] = LASTNAMEPHONETIC
        data[f"users[{i}][middlename]"] = MIDDLENAME
        data[f"users[{i}][alternatename]"] = ALTERNATENAME
        data[f"users[{i}][interests]"] = INTERESTS
        data[f"users[{i}][idnumber]"] = IDNUMBER
        data[f"users[{i}][institution]"] = INSTITUTION
        data[f"users[{i}][department]"] = DEPARTMENT
        data[f"users[{i}][phone1]"] = PHONE1
        data[f"users[{i}][phone2]"] = PHONE2
        data[f"users[{i}][address]"] = ADDRESS

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

