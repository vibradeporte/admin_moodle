import os
import csv
import requests
import pandas as pd
from return_codes import *
from io import StringIO
import re
from fastapi import APIRouter, UploadFile, File, HTTPException, Form

core_user_create_users_router = APIRouter()
WS_FUNCTION = "core_user_create_users"

@core_user_create_users_router.post("/core_user_create_users/", tags=['Moodle'])
async def core_user_create_users(moodle_url: str = Form(...), moodle_token: str = Form(...)):
    """
    ## **Descripción:**
    Esta función permite crear usuarios.

    ## **Parámetros obligatorios:**
        - username -> Username del usuario. Solo se permiten caracteres alfanuméricos con letras minúsculas, guion bajo (_), guion (-), punto (.) y el símbolo de arroba (@). Su longitud no puede superar los 100 caracteres.
        - firstname -> Primer nombre del usuario.
        - lastname -> Apellido del usuario.
        - email -> Correo electrónico del usuario.
        - idnumber -> Idnumber del usuario.  


    ## **Parámetros opcionales:**
        - createpassword -> Verdadero(1) si la contraseña debe crearse y enviarse por correo al usuario. 0:No
        - auth -> Método de auth.
        - password -> Contraseña. Mínimo ocho digitos. Mínimo una minúscula. Mínimo una mayúscula.
        - maildisplay -> Visibilidad del correo electrónico.
        - city -> Ciudad.
        - country -> País.
        - timezone -> Zona horaria.
        - description -> Descripción.
        - firstnamephonetic -> Pronunciación del nombre del usuario.
        - lastnamephonetic -> Pronunciación del apellido del usuario.
        - middlename -> El segundo nombre del usuario.
        - alternatename -> El nombre alternativo del usuario.
        - interests -> Intereses del usuario (separados por comas).
        - institution -> Institución del usuario.
        - department -> Departamento del usuario.
        - phone1 -> Teléfono del usuario.
        - phone2 -> Número de celular del usuario.
        - address -> Dirección del usuario
        - lang -> Código de la lengua.
        - calendartype -> Tipo de calendario. 
        - theme -> Nombre del tema.
        - mailformat -> Código de formato de correo.
        

    ## **Códigos retornados:**
        - 200 -> La operación se realizó correctamente.
        - 452 -> La cantidad de caracteres supera el límite de 100 para este KEY.
        - 453 -> La cantidad de caracteres supera el límite de 255 para este KEY.
        - 454 -> La cantidad de caracteres supera el límite de 10 para este KEY.
        - 455 -> La cantidad de caracteres supera el límite de 2 para este KEY.
        - 456 -> La cantidad de caracteres supera el límite de 20 para este KEY.
        - 457 -> La cantidad de caracteres supera el límite de 1 para este KEY.
        - 458 -> La cantidad de caracteres supera el límite de 120 para este KEY.
        - 459 -> La cantidad de caracteres supera el límite de 30 para este KEY.
        - 460 -> La cantidad de caracteres es menor a lo permitido.
        - 462 -> El email ingresado no existe.
        - 463 -> La estructura del teléfono es incorrecta. No puede contener letras ni espacios y su tamaño máximo es de 20.
        - 465 -> Uno o varios caracteres ingresados son inválidos para este campo.
        - 466 -> El código alfa-2 ingresado no existe. Verifique la tabla de países e ingrese el código que corresponda.
        - 467 -> El valor de timezone ingresado no existe. Verifique la tabla de zonas horarias e ingrese el valor que corresponda.
        - 470 -> El lenguaje consultado no existe. Verifique la documentación de esta función.
        - 472 -> La estructura del username es incorrecta. Solo se permiten caracteres alfanuméricos con letras minúsculas, guion bajo (_), guion (-), punto (.) y el símbolo de arroba (@). Su longitud no puede superar los 100 caracteres.
        - 473 -> La estructura del email es incorrecta. No se permiten espacios y debe contener un '@'.
        - 474 -> La estructura del id es incorrecta.. No se permiten letras, espacios ni números negativos.
        - 475 -> La cantidad de caracteres supera el límite de 50 para este KEY.
        - 478 -> El usuario consultado no existe.
        
    ## **Valores permitidos en el campo auth:**
        - email.
        - manual.
        - ldap.

    ## **Valores permitidos en el campo suspended:**
        - false -> Habilitar inicio de sesión.
        - true -> Deshabilitar el inicio de sesión.

    ## **Valores permitidos en el campo maildisplay:**
        - 0 -> Oculto.
        - 1 -> Visible para todos.
        - 2 -> Visible para los participantes en el curso.

    ## **Valores permitidos en el campo timezone:**

    | Valor                     | Zona                  |
    |---------------------------|-------------------------|
    | Africa/Abidjan            | Africa/Abidjan         |
    | Africa/Accra              | Africa/Accra           |
    | Africa/Addis_Ababa        | Africa/Addis_Ababa     |
    | Africa/Algiers            | Africa/Algiers         |
    | Africa/Asmara             | Africa/Asmara          |
    | Africa/Bamako             | Africa/Bamako          |
    | Africa/Bangui             | Africa/Bangui          |
    | Africa/Banjul             | Africa/Banjul          |
    | Africa/Bissau             | Africa/Bissau          |
    | Africa/Blantyre           | Africa/Blantyre        |
    | Africa/Brazzaville        | Africa/Brazzaville     |
    | Africa/Bujumbura          | Africa/Bujumbura       |
    | Africa/Cairo              | Africa/Cairo           |
    | Africa/Casablanca         | Africa/Casablanca      |
    | Africa/Ceuta              | Africa/Ceuta           |
    | Africa/Conakry            | Africa/Conakry         |
    | Africa/Dakar              | Africa/Dakar           |
    | Africa/Dar_es_Salaam      | Africa/Dar_es_Salaam   |
    | Africa/Djibouti           | Africa/Djibouti        |
    | Africa/Douala             | Africa/Douala          |
    | Africa/El_Aaiun           | Africa/El_Aaiun        |
    | Africa/Freetown           | Africa/Freetown        |
    | Africa/Gaborone           | Africa/Gaborone        |
    | Africa/Harare             | Africa/Harare          |
    | Africa/Johannesburg       | Africa/Johannesburg    |
    | Africa/Juba               | Africa/Juba            |
    | Africa/Kampala            | Africa/Kampala         |
    | Africa/Khartoum           | Africa/Khartoum        |
    | Africa/Kigali             | Africa/Kigali          |
    | Africa/Kinshasa           | Africa/Kinshasa        |
    | Africa/Lagos              | Africa/Lagos           |
    | Africa/Libreville         | Africa/Libreville      |
    | Africa/Lome               | Africa/Lome            |
    | Africa/Luanda             | Africa/Luanda          |
    | Africa/Lubumbashi         | Africa/Lubumbashi      |
    | Africa/Lusaka             | Africa/Lusaka          |
    | Africa/Malabo             | Africa/Malabo          |
    | Africa/Maputo             | Africa/Maputo          |
    | Africa/Maseru             | Africa/Maseru          |
    | Africa/Mbabane            | Africa/Mbabane         |
    | Africa/Mogadishu          | Africa/Mogadishu      |
    | Africa/Monrovia           | Africa/Monrovia        |
    | Africa/Nairobi            | Africa/Nairobi         |
    | Africa/Ndjamena           | Africa/Ndjamena        |
    | Africa/Niamey             | Africa/Niamey          |
    | Africa/Nouakchott         | Africa/Nouakchott      |
    | Africa/Ouagadougou        | Africa/Ouagadougou     |
    | Africa/Porto-Novo         | Africa/Porto-Novo      |
    | Africa/Sao_Tome           | Africa/Sao_Tome       |
    | Africa/Tripoli            | Africa/Tripoli         |
    | Africa/Tunis              | Africa/Tunis           |
    | Africa/Windhoek           | Africa/Windhoek        |
    | America/Adak              | América/Adak           |
    | America/Anchorage         | América/Anchorage      |
    | America/Anguilla          | América/Anguilla       |
    | America/Antigua           | América/Antigua        |
    | America/Araguaina         | América/Araguaina      |
    | America/Argentina/Buenos_Aires | América/Argentina/Buenos_Aires |
    | America/Argentina/Catamarca | América/Argentina/Catamarca |
    | America/Argentina/Cordoba | América/Argentina/Cordoba |
    | America/Argentina/Jujuy   | América/Argentina/Jujuy|
    | America/Argentina/La_Rioja| América/Argentina/La_Rioja |
    | America/Argentina/Mendoza| América/Argentina/Mendoza |
    | America/Argentina/Rio_Gallegos | América/Argentina/Rio_Gallegos |
    | America/Argentina/Salta   | América/Argentina/Salta |
    | America/Argentina/San_Juan| América/Argentina/San_Juan |
    | America/Argentina/San_Luis| América/Argentina/San_Luis |
    | America/Argentina/Tucuman| América/Argentina/Tucuman |
    | America/Argentina/Ushuaia| América/Argentina/Ushuaia |
    | America/Aruba             | América/Aruba          |
    | America/Asuncion          | América/Asuncion       |
    | America/Atikokan          | América/Atikokan       |
    | America/Bahia             | América/Bahia          |
    | America/Bahia_Banderas    | América/Bahia_Banderas |
    | America/Barbados          | América/Barbados       |
    | America/Belem             | América/Belem          |
    | America/Belize            | América/Belize         |
    | America/Blanc-Sablon      | América/Blanc-Sablon   |
    | America/Boa_Vista         | América/Boa_Vista     |
    | America/Bogota            | América/Bogota         |
    | America/Boise             | América/Boise          |
    | America/Cayman            | América/Cayman         |
    | America/Cambridge_Bay     | América/Cambridge_Bay  |
    | America/Campo_Grande      | América/Campo_Grande   |
    | America/Cancun            | América/Cancun         |
    | America/Caracas           | América/Caracas        |
    | America/Cayenne           | América/Cayenne        |
    | America/Chicago           | América/Chicago        |
    | America/Chihuahua         | América/Chihuahua      |
    | America/Ciudad_Juarez     | América/Ciudad_Juarez  |
    | America/Costa_Rica        | América/Costa_Rica     |
    | America/Creston           | América/Creston        |
    | America/Cuiaba            | América/Cuiaba         |
    | America/Curacao           | América/Curacao        |
    | America/North_Dakota/Beulah | América/North_Dakota/Beulah |
    | America/North_Dakota/Center | América/North_Dakota/Center |
    | America/North_Dakota/New_Salem | América/North_Dakota/New_Salem|
    | America/Danmarkshavn      | América/Danmarkshavn   |
    | America/Dawson            | América/Dawson         |
    | America/Dawson_Creek      | América/Dawson_Creek   |
    | America/Denver            | América/Denver         |
    | America/Detroit           | América/Detroit        |
    | America/Dominica          | América/Dominica       |
    | America/Edmonton          | América/Edmonton       |
    | America/Eirunepe          | América/Eirunepe       |
    | America/El_Salvador       | América/El_Salvador    |
    | America/Fort_Nelson       | América/Fort_Nelson    |
    | America/Fortaleza         | América/Fortaleza      |
    | America/Glace_Bay         | América/Glace_Bay      |
    | America/Goose_Bay         | América/Goose_Bay      |
    | America/Grenada           | América/Grenada        |
    | America/Grand_Turk        | América/Grand_Turk     |
    | America/Guadeloupe        | América/Guadeloupe     |
    | America/Guatemala         | América/Guatemala      |
    | America/Guayaquil         | América/Guayaquil      |
    | America/Guyana            | América/Guyana         |
    | America/Halifax           | América/Halifax        |
    | America/Hermosillo        | América/Hermosillo     |
    | America/Indiana/Indianapolis | América/Indiana/Indianapolis |
    | America/Indiana/Knox      | América/Indiana/Knox   |
    | America/Indiana/Marengo   | América/Indiana/Marengo|
    | America/Indiana/Petersburg| América/Indiana/Petersburg |
    | America/Indiana/Tell_City | América/Indiana/Tell_City |
    | America/Indiana/Vevay     | América/Indiana/Vevay  |
    | America/Indiana/Vincennes | América/Indiana/Vincennes |
    | America/Indiana/Winamac   | América/Indiana/Winamac|
    | America/Inuvik            | América/Inuvik         |
    | America/Iqaluit           | América/Iqaluit        |
    | America/Jamaica           | América/Jamaica        |
    | America/Juneau            | América/Juneau         |
    | America/Kentucky/Louisville | América/Kentucky/Louisville |
    | America/Kentucky/Monticello | América/Kentucky/Monticello |
    | America/Kralendijk        | América/Kralendijk     |
    | America/Havana            | América/Havana         |
    | America/La_Paz            | América/La_Paz         |
    | America/Lima                          | América/Lima                   |
    | America/Los_Angeles                   | América/Los_Ángeles           |
    | America/Lower_Princes                 | América/Lower_Princes         |
    | America/Maceio                        | América/Maceio                |
    | America/Managua                       | América/Managua               |
    | America/Manaus                        | América/Manaos                |
    | America/Marigot                       | América/Marigot               |
    | America/Martinique                    | América/Martinica             |
    | America/Matamoros                     | América/Matamoro              |
    | America/Mazatlan                      | América/Mazatlán              |
    | America/Menominee                     | América/Menominée             |
    | America/Merida                        | América/Mérida                |
    | America/Metlakatla                    | América/Metlakatla            |
    | America/Mexico_City                   | América/México_DF             |
    | America/Miquelon                      | América/Miquelon              |
    | America/Moncton                       | América/Moncton               |
    | America/Monterrey                     | América/Monterrey             |
    | America/Montevideo                    | América/Montevideo            |
    | America/Montserrat                    | América/Montserrat            |
    | America/Nassau                        | América/Nassau                |
    | America/Nome                          | América/Nome                  |
    | America/Noronha                       | América/Noronha               |
    | America/New_York                      | América/Nueva_York            |
    | America/Nuuk                          | América/Nuuk                  |
    | America/Ojinaga                       | América/Ojinaga               |
    | America/Panama                        | América/Panamá                |
    | America/Paramaribo                    | América/Paramaribo            |
    | America/Phoenix                       | América/Phoenix               |
    | America/Port_of_Spain                 | América/Port_of_Spain         |
    | America/Port-au-Prince                | América/Port-au-Prince        |
    | America/Porto_Velho                   | América/Porto_Velho           |
    | America/Puerto_Rico                   | América/Puerto_Rico           |
    | America/Punta_Arenas                  | América/Punta_Arenas          |
    | America/Rankin_Inlet                  | América/Rankin_Inlet          |
    | America/Recife                        | América/Recife                |
    | America/Regina                        | América/Regina                |
    | America/Resolute                      | América/Resolute              |
    | America/Rio_Branco                    | América/Rio_Branco            |
    | America/Santarem                      | América/Santarem              |
    | America/Santiago                      | América/Santiago              |
    | America/Santo_Domingo                 | América/Santo_Domingo         |
    | America/Sao_Paulo                     | América/Sao_Paulo             |
    | America/Scoresbysund                  | América/Scoresbysund          |
    | America/St_Barthelemy                 | América/St_Barthelemy         |
    | America/St_Johns                      | América/St_Johns              |
    | America/St_Kitts                      | América/St_Kitts              |
    | America/St_Lucia                      | América/St_Lucia              |
    | America/St_Thomas                     | América/St_Thomas             |
    | America/St_Vincent                    | América/St_Vincent            |
    | America/Stikla                        | América/Stikla                |
    | America/Swift_Current                 | América/Swift_Current         |
    | America/Tegucigalpa                   | América/Tegucigalpa           |
    | America/Thule                         | América/Thule                 |
    | America/Tijuana                       | América/Tijuana               |
    | America/Toronto                       | América/Toronto               |
    | America/Tortola                       | América/Tortola               |
    | America/Vancouver                     | América/Vancouver             |
    | America/Whitehorse                    | América/Whitehorse            |
    | America/Winnipeg                      | América/Winnipeg              |
    | America/Yakutat                       | América/Yakutat               |
    | Antarctica/Casey                     | Antártida/Casey               |
    | Antarctica/Davis                     | Antártida/Davis               |
    | Antarctica/DumontDUrville            | Antártida/DumontDUrville      |
    | Antarctica/Macquarie                 | Antártida/Macquarie           |
    | Antarctica/Mawson                    | Antártida/Mawson              |
    | Antarctica/McMurdo                   | Antártida/McMurdo             |
    | Antarctica/Palmer                    | Antártida/Palmer              |
    | Antarctica/Rothera                   | Antártida/Rothera             |
    | Antarctica/Syowa                     | Antártida/Syowa               |
    | Antarctica/Troll                     | Antártida/Troll               |
    | Antarctica/Vostok                    | Antártida/Vostok              |
    | Artico/Longyearbyen                  | Ártico/Longyearbyen           |
    | Asia/Aden                             | Asia/Adén                     |
    | Asia/Almaty                           | Asia/Almaty                   |
    | Asia/Amman                            | Asia/Amman                    |
    | Asia/Anadyr                           | Asia/Anadyr                   |
    | Asia/Aqtau                            | Asia/Aqtau                    |
    | Asia/Aqtobe                           | Asia/Aqtobe                   |
    | Asia/Ashgabat                         | Asia/Ashgabat                 |
    | Asia/Atyrau                           | Asia/Atyrau                   |
    | Asia/Baghdad                          | Asia/Baghdad                  |
    | Asia/Bahrain                           | Asia/Bahrein                        |
    | Asia/Baku                              | Asia/Bakú                           |
    | Asia/Bangkok                           | Asia/Bangkok                        |
    | Asia/Barnaul                           | Asia/Barnaul                        |
    | Asia/Beirut                            | Asia/Beirut                         |
    | Asia/Bishkek                           | Asia/Bishkek                        |
    | Asia/Brunei                            | Asia/Brunei                         |
    | Asia/Chita                             | Asia/Chita                          |
    | Asia/Choibalsan                        | Asia/Choibalsan                     |
    | Asia/Colombo                           | Asia/Colombo                        |
    | Asia/Damasco                           | Asia/Damasco                        |
    | Asia/Dhaka                             | Asia/Dhaka                          |
    | Asia/Dili                              | Asia/Dili                           |
    | Asia/Dubai                             | Asia/Dubái                          |
    | Asia/Dushanbe                          | Asia/Dusambé                        |
    | Asia/Famagusta                         | Asia/Famagusta                     |
    | Asia/Gaza                              | Asia/Gaza                           |
    | Asia/Hebron                            | Asia/Hebrón                         |
    | Asia/Ho_Chi_Minh                       | Asia/Ho_Chi_Minh                    |
    | Asia/Hong_Kong                         | Asia/Hong_Kong                      |
    | Asia/Hovd                              | Asia/Hovd                           |
    | Asia/Irkutsk                           | Asia/Irkutsk                        |
    | Asia/Jakarta                           | Asia/Jakarta                        |
    | Asia/Jayapura                          | Asia/Jayapura                       |
    | Asia/Jerusalén                         | Asia/Jerusalén                      |
    | Asia/Kabul                             | Asia/Kabul                          |
    | Asia/Kamchatka                         | Asia/Kamchatka                      |
    | Asia/Karachi                           | Asia/Karachi                        |
    | Asia/Kathmandu                         | Asia/Kathmandu                      |
    | Asia/Khandyga                          | Asia/Khandyga                       |
    | Asia/Kolkata                           | Asia/Kolkata                        |
    | Asia/Krasnoyarsk                       | Asia/Krasnoyarsk                    |
    | Asia/Kuala_Lumpur                      | Asia/Kuala_Lumpur                   |
    | Asia/Kuching                           | Asia/Kuching                        |
    | Asia/Kuwait                            | Asia/Kuwait                         |
    | Asia/Macau                             | Asia/Macao                          |
    | Asia/Magadan                           | Asia/Magadán                        |
    | Asia/Makassar                          | Asia/Makassar                       |
    | Asia/Manila                            | Asia/Manila                         |
    | Asia/Muscat                            | Asia/Mascate                        |
    | Asia/Nicosia                           | Asia/Nicosia                        |
    | Asia/Novokuznetsk                      | Asia/Novokuznetsk                   |
    | Asia/Novosibirsk                       | Asia/Novosibirsk                    |
    | Asia/Omsk                              | Asia/Omsk                           |
    | Asia/Oral                              | Asia/Oral                           |
    | Asia/Phnom_Penh                        | Asia/Phnom_Penh                     |
    | Asia/Pontianak                         | Asia/Pontianak                      |
    | Asia/Pyongyang                         | Asia/Pyongyang                      |
    | Asia/Qatar                             | Asia/Catar                          |
    | Asia/Qostanay                          | Asia/Qostanay                       |
    | Asia/Qyzylorda                         | Asia/Qyzylorda                      |
    | Asia/Riyadh                            | Asia/Riad                           |
    | Asia/Sakhalin                          | Asia/Sajalín                        |
    | Asia/Samarkanda                        | Asia/Samarcanda                     |
    | Asia/Seoul                             | Asia/Seúl                           |
    | Asia/Shanghai                          | Asia/Shanghái                       |
    | Asia/Singapur                          | Asia/Singapur                       |
    | Asia/Srednekolymsk                     | Asia/Srednekolymsk                  |
    | Asia/Taipei                            | Asia/Taipei                         |
    | Asia/Tashkent                          | Asia/Tashkent                       |
    | Asia/Tbilisi                           | Asia/Tbilisi                        |
    | Asia/Tehran                            | Asia/Teherán                        |
    | Asia/Thimphu                           | Asia/Thimphu                        |
    | Asia/Tokyo                             | Asia/Tokio                          |
    | Asia/Tomsk                             | Asia/Tomsk                          |
    | Asia/Ulaanbaatar                       | Asia/Ulan Bator                     |
    | Asia/Urumqi                            | Asia/Urumqi                         |
    | Asia/Ust-Nera                          | Asia/Ust-Nera                       |
    | Asia/Vientiane                         | Asia/Vientiane                      |
    | Asia/Vladivostok                       | Asia/Vladivostok                    |
    | Asia/Yakutsk                           | Asia/Yakutsk                        |
    | Asia/Yangon                            | Asia/Yangón                         |
    | Asia/Yekaterinburg                     | Asia/Yekaterimburgo                 |
    | Asia/Yerevan                           | Asia/Ereván                         |
    | Atlantic/Faroe                        | Atlántico/Faroe                     |
    | Atlantic/Azores                       | Atlántico/Azores                    |
    | Atlantic/Bermuda                      | Atlántico/Bermudas                  |
    | Atlantic/Cape_Verde                   | Atlántico/Cabo Verde                |
    | Atlantic/Canarias                     | Atlántico/Canarias                  |
    | Atlantic/Madeira                      | Atlántico/Madeira                   |
    | Atlantic/Reykjavik                    | Atlántico/Reikiavik                 |
    | Atlantic/South_Georgia                | Atlántico/Islas Georgias del Sur    |
    | Atlantic/St_Helena                    | Atlántico/Santa Elena               |
    | Atlantic/Stanley                      | Atlántico/Stanley                   |
    | Australia/Adelaida                    | Australia/Adelaida                  |
    | Australia/Brisbane                    | Australia/Brisbane                  |
    | Australia/Broken_Hill                 | Australia/Broken Hill               |
    | Australia/Darwin                      | Australia/Darwin                    |
    | Australia/Eucla                       | Australia/Eucla                     |
    | Australia/Hobart                      | Australia/Hobart                    |
    | Australia/Lindeman                    | Australia/Lindeman                  |
    | Australia/Lord_Howe                   | Australia/Lord Howe                 |
    | Australia/Melbourne                   | Australia/Melbourne                 |
    | Australia/Perth                       | Australia/Perth                     |
    | Australia/Sydney                      | Australia/Sydney                    |
    | Europe/Amsterdam                      | Europa/Ámsterdam                    |
    | Europe/Andorra                        | Europa/Andorra                      |
    | Europe/Atenas                         | Europa/Atenas                       |
    | Europe/Belgrado                       | Europa/Belgrado                     |
    | Europe/Berlín                         | Europa/Berlín                       |
    | Europe/Bruselas                       | Europa/Bruselas                     |
    | Europe/Bucarest                       | Europa/Bucarest                     |
    | Europe/Budapest                       | Europa/Budapest                     |
    | Europe/Busingen                       | Europa/Busingen                     |
    | Europe/Chisinau                       | Europa/Chisinau                     |
    | Europe/Copenhague                     | Europa/Copenhague                   |
    | Europe/Dublín                         | Europa/Dublín                       |
    | Europe/Estambul                       | Europa/Estambul                     |
    | Europe/Estocolmo                      | Europa/Estocolmo                    |
    | Europe/Gibraltar                      | Europa/Gibraltar                    |
    | Europe/Guernsey                       | Europa/Guernsey                     |
    | Europe/Helsinki                       | Europa/Helsinki                     |
    | Europe/Isla_de_Man                    | Europa/Isla de Man                  |
    | Europe/Jersey                         | Europa/Jersey                       |
    | Europe/Kaliningrado                   | Europa/Kaliningrado                 |
    | Europe/Kiev                           | Europa/Kiev                         |
    | Europe/Kirov                          | Europa/Kírov                        |
    | Europe/Lisboa                         | Europa/Lisboa                       |
    | Europe/Ljubljana                      | Europa/Liubliana                    |
    | Europe/Londres                        | Europa/Londres                      |
    | Europe/Luxemburgo                     | Europa/Luxemburgo                   |
    | Europe/Madrid                         | Europa/Madrid                       |
    | Europe/Malta                          | Europa/Malta                        |
    | Europe/Mariehamn                      | Europa/Mariehamn                    |
    | Europe/Mónaco                         | Europa/Mónaco                       |
    | Europe/Moscu                          | Europa/Moscú                        |
    | Europe/Oslo                           | Europa/Oslo                         |
    | Europe/Paris                          | Europa/París                        |
    | Europe/Podgorica                      | Europa/Podgorica                    |
    | Europe/Praga                          | Europa/Praga                        |
    | Europe/Riga                           | Europa/Riga                         |
    | Europe/Roma                           | Europa/Roma                         |
    | Europe/Samara                         | Europa/Samara                       |
    | Europe/San_Marino                     | Europa/San Marino                   |
    | Europe/Sarajevo                       | Europa/Sarajevo                     |
    | Europe/Saratov                        | Europa/Saratov                      |
    | Europe/Simferopol                     | Europa/Simferópol                   |
    | Europe/Skopje                         | Europa/Esloboden                    |
    | Europe/Sofia                          | Europa/Sofía                        |
    | Europe/Tallinn                        | Europa/Tallin                       |
    | Europe/Tirana                         | Europa/Tirana                       |
    | Europe/Vaduz                          | Europa/Vaduz                        |
    | Europe/Varsovia                       | Europa/Varsovia                     |
    | Europe/Vaticano                       | Europa/Ciudad del Vaticano          |
    | Europe/Viena                          | Europa/Viena                        |
    | Europe/Vilna                          | Europa/Vilna                        |
    | Europe/Zagreb                         | Europa/Zagreb                       |
    | Europe/Zurich                         | Europa/Zurich                       |
    | Europe/Astracan                       | Europa/Astracán                     |
    | Europe/Ulianovsk                      | Europa/Ulianovsk                    |
    | Europe/Volgogrado                     | Europa/Volgogrado                   |
    | India/Antananarivo                    | India/Antananarivo                  |
    | India/Chagos                          | India/Chagos                        |
    | India/Christmas                       | India/Christmas                     |
    | India/Comoros                         | India/Comoras                       |
    | India/Kerguelen                       | India/Kerguelen                     |
    | India/Mahe                            | India/Mahe                          |
    | India/Maldivas                        | India/Maldivas                      |
    | India/Mauricio                        | India/Mauricio                      |
    | India/Mayotte                         | India/Mayotte                       |
    | India/Reunion                         | India/Reunión                       |
    | India/Cocos                           | India/Cocos                         |
    | Pacifico/Chuuk                        | Pacífico/Chuuk                      |
    | Pacifico/Pohnpei                      | Pacífico/Pohnpei                    |
    | Pacifico/Apia                         | Pacífico/Apia                       |
    | Pacifico/Auckland                     | Pacífico/Auckland                   |
    | Pacifico/Bougainville                 | Pacífico/Bougainville               |
    | Pacifico/Chatham                      | Pacífico/Chatham                    |
    | Pacifico/Easter                       | Pacífico/Easter                     |
    | Pacifico/Efate                        | Pacífico/Efate                      |
    | Pacifico/Fakaofo                      | Pacífico/Fakaofo                    |
    | Pacifico/Fidji                        | Pacífico/Fiyi                       |
    | Pacifico/Funafuti                     | Pacífico/Funafuti                   |
    | Pacifico/Galápagos                    | Pacífico/Galápagos                  |
    | Pacifico/Gambier                      | Pacífico/Gambier                    |
    | Pacifico/Guadalcanal                  | Pacífico/Guadalcanal                |
    | Pacifico/Guam                         | Pacífico/Guam                       |
    | Pacifico/Honolulu                     | Pacífico/Honolulu                   |
    | Pacifico/Kanton                       | Pacífico/Kantón                     |
    | Pacifico/Kiritimati                   | Pacífico/Kiritimati                 |
    | Pacifico/Kosrae                       | Pacífico/Kosrae                     |
    | Pacifico/Kwajalein                    | Pacífico/Kwajalein                  |
    | Pacifico/Majuro                       | Pacífico/Majuro                     |
    | Pacifico/Marquesas                    | Pacífico/Marquesas                  |
    | Pacifico/Midway                       | Pacífico/Midway                     |
    | Pacifico/Nauru                        | Pacífico/Nauru                      |
    | Pacifico/Niue                         | Pacífico/Niue                       |
    | Pacifico/Norfolk                      | Pacífico/Norfolk                    |
    | Pacifico/Noumea                       | Pacífico/Noumea                     |
    | Pacifico/Pago_Pago                    | Pacífico/Pago_Pago                  |
    | Pacifico/Palau                        | Pacífico/Palau                      |
    | Pacifico/Pitcairn                     | Pacífico/Pitcairn                   |
    | Pacifico/Port_Moresby                 | Pacífico/Port_Moresby               |
    | Pacifico/Rarotonga                    | Pacífico/Rarotonga                  |
    | Pacifico/Saipan                       | Pacífico/Saipán                     |
    | Pacifico/Tahiti                       | Pacífico/Tahití                     |
    | Pacifico/Tarawa                       | Pacífico/Tarawa                     |
    | Pacifico/Tongatapu                    | Pacífico/Tongatapu                  |
    | Pacifico/Wake                         | Pacífico/Wake                       |
    | Pacifico/Wallis                       | Pacífico/Wallis                     |
    | UTC                                    | UTC                                 |
    | 99                                     | Zona horaria del servidor (América/Nueva_York) |


    ## **Valores permitidos en el campo mailformat:**
        - 0 -> Texto plano.
        - 1 -> HTML.
        

    ## **Valores permitidos en el campo country:**
    Se debe ingresar el código alfa-2 de la norma ISO 3166-1 según corresponda.

    | Código alfa-2 | País o Área                            |
    |---------------|----------------------------------------|
    | AD            | Andorra                                |
    | AE            | Emiratos Árabes Unidos                 |
    | AF            | Afganistán                             |
    | AG            | Antigua y Barbuda                      |
    | AI            | Anguila                                |
    | AL            | Albania                                |
    | AM            | Armenia                                |
    | AO            | Angola                                 |
    | AQ            | Antártida                              |
    | AR            | Argentina                              |
    | AS            | Samoa Americana                        |
    | AT            | Austria                                |
    | AU            | Australia                              |
    | AW            | Aruba                                  |
    | AX            | Islas Åland                            |
    | AZ            | Azerbaiyán                             |
    | BA            | Bosnia y Herzegovina                   |
    | BB            | Barbados                               |
    | BD            | Bangladés                              |
    | BE            | Bélgica                                |
    | BF            | Burkina Faso                           |
    | BG            | Bulgaria                               |
    | BH            | Baréin                                 |
    | BI            | Burundi                                |
    | BJ            | Benín                                  |
    | BL            | San Bartolomé                          |
    | BM            | Bermudas                               |
    | BN            | Brunéi                                 |
    | BO            | Bolivia (Estado Plurinacional de)      |
    | BQ            | Bonaire, San Eustaquio y Saba          |
    | BR            | Brasil                                 |
    | BS            | Bahamas                                |
    | BT            | Bután                                  |
    | BV            | Isla Bouvet                            |
    | BW            | Botsuana                               |
    | BY            | Bielorrusia                            |
    | BZ            | Belice                                 |
    | CA            | Canadá                                 |
    | CC            | Islas Cocos                            |
    | CD            | Congo, República Democrática del       |
    | CF            | República Centroafricana                |
    | CG            | Congo                                  |
    | CH            | Suiza                                  |
    | CI            | Côte d'Ivoire                          |
    | CK            | Islas Cook                             |
    | CL            | Chile                                  |
    | CM            | Camerún                                |
    | CN            | China                                  |
    | CO            | Colombia                               |
    | CR            | Costa Rica                             |
    | CU            | Cuba                                   |
    | CV            | Cabo Verde                             |
    | CW            | Curazao                                |
    | CX            | Isla de Navidad                        |
    | CY            | Chipre                                 |
    | CZ            | República Checa                        |
    | DE            | Alemania                               |
    | DJ            | Yibuti                                 |
    | DK            | Dinamarca                              |
    | DM            | Dominica                               |
    | DO            | República Dominicana                   |
    | DZ            | Argelia                                |
    | EC            | Ecuador                                |
    | EE            | Estonia                                |
    | EG            | Egipto                                 |
    | EH            | Sahara Occidental                      |
    | ER            | Eritrea                                |
    | ES            | España                                 |
    | ET            | Etiopía                                |
    | FI            | Finlandia                              |
    | FJ            | Fiyi                                   |
    | FK            | Islas Malvinas                         |
    | FM            | Micronesia (Estados Federados de)      |
    | FO            | Islas Feroe                            |
    | FR            | Francia                                |
    | GA            | Gabón                                  |
    | GB            | Reino Unido                            |
    | GD            | Granada                                |
    | GE            | Georgia                                |
    | GF            | Guayana Francesa                       |
    | GG            | Guernsey                               |
    | GH            | Ghana                                  |
    | GI            | Gibraltar                              |
    | GL            | Groenlandia                            |
    | GM            | Gambia                                 |
    | GN            | Guinea                                 |
    | GP            | Guadalupe                              |
    | GQ            | Guinea Ecuatorial                      |
    | GR            | Grecia                                 |
    | GS            | Georgia del Sur e Islas Sandwich del Sur|
    | GT            | Guatemala                              |
    | GU            | Guam                                   |
    | GW            | Guinea-Bissau                          |
    | GY            | Guyana                                 |
    | HK            | Hong Kong                              |
    | HM            | Islas Heard y McDonald                 |
    | HN            | Honduras                               |
    | HR            | Croacia                                |
    | HT            | Haití                                  |
    | HU            | Hungría                                |
    | ID            | Indonesia                              |
    | IE            | Irlanda                                |
    | IL            | Israel                                 |
    | IM            | Isla de Man                            |
    | IN            | India                                  |
    | IO            | Territorio Británico del Océano Índico|
    | IQ            | Irak                                   |
    | IR            | Irán (República Islámica del)         |
    | IS            | Islandia                               |
    | IT            | Italia                                 |
    | JE            | Jersey                                 |
    | JM            | Jamaica                                |
    | JO            | Jordania                               |
    | JP            | Japón                                  |
    | KE            | Kenia                                  |
    | KG            | Kirguistán                             |
    | KH            | Camboya                                |
    | KI            | Kiribati                               |
    | KM            | Comoras                                |
    | KN            | San Cristóbal y Nieves                |
    | KP            | Corea (República Popular Democrática de)|
    | KR            | Corea (República de)                   |
    | KW            | Kuwait                                 |
    | KY            | Islas Caimán                           |
    | KZ            | Kazajistán                             |
    | LA            | República Democrática Popular Lao      |
    | LB            | Líbano                                 |
    | LC            | Santa Lucía                            |
    | LI            | Liechtenstein                          |
    | LK            | Sri Lanka                              |
    | LR            | Liberia                                |
    | LS            | Lesoto                                 |
    | LT            | Lituania                               |
    | LU            | Luxemburgo                             |
    | LV            | Letonia                                |
    | LY            | Libia                                  |
    | MA            | Marruecos                              |
    | MC            | Mónaco                                 |
    | MD            | Moldavia (República de)                |
    | ME            | Montenegro                             |
    | MF            | Saint Martin (parte francesa)          |
    | MG            | Madagascar                             |
    | MH            | Islas Marshall                         |
    | MK            | Macedonia del Norte                    |
    | ML            | Malí                                   |
    | MM            | Myanmar                                |
    | MN            | Mongolia                               |
    | MO            | Macao                                  |
    | MP            | Islas Marianas del Norte               |
    | MQ            | Martinica                              |
    | MR            | Mauritania                             |
    | MS            | Montserrat                             |
    | MT            | Malta                                  |
    | MU            | Mauricio                               |
    | MV            | Maldivas                               |
    | MW            | Malaui                                 |
    | MX            | México                                 |
    | MY            | Malasia                                |
    | MZ            | Mozambique                             |
    | NA            | Namibia                                |
    | NC            | Nueva Caledonia                        |
    | NE            | Níger                                  |
    | NF            | Isla Norfolk                           |
    | NG            | Nigeria                                |
    | NI            | Nicaragua                              |
    | NL            | Países Bajos                           |
    | NO            | Noruega                                |
    | NP            | Nepal                                  |
    | NR            | Nauru                                  |
    | NU            | Niue                                   |
    | NZ            | Nueva Zelanda                          |
    | OM            | Omán                                   |
    | PA            | Panamá                                 |
    | PE            | Perú                                   |
    | PF            | Polinesia Francesa                     |
    | PG            | Papúa Nueva Guinea                     |
    | PH            | Filipinas                              |
    | PK            | Pakistán                               |
    | PL            | Polonia                                |
    | PM            | San Pedro y Miquelón                   |
    | PN            | Pitcairn                               |
    | PR            | Puerto Rico                            |
    | PS            | Palestina, Estado de                   |
    | PT            | Portugal                               |
    | PW            | Palaos                                 |
    | PY            | Paraguay                               |
    | QA            | Catar                                  |
    | RE            | Reunión                                |
    | RO            | Rumania                                |
    | RS            | Serbia                                 |
    | RU            | Rusia (Federación de)                  |
    | RW            | Ruanda                                 |
    | SA            | Arabia Saudita                         |
    | SB            | Islas Salomón                          |
    | SC            | Seychelles                             |
    | SD            | Sudán                                  |
    | SE            | Suecia                                 |
    | SG            | Singapur                               |
    | SH            | Santa Elena, Ascensión y Tristán de Acuña|
    | SI            | Eslovenia                              |
    | SJ            | Svalbard y Jan Mayen                   |
    | SK            | Eslovaquia                             |
    | SL            | Sierra Leona                           |
    | SM            | San Marino                             |
    | SN            | Senegal                                |
    | SO            | Somalia                                |
    | SR            | Surinam                                |
    | SS            | Sudán del Sur                          |
    | ST            | Santo Tomé y Príncipe                  |
    | SV            | El Salvador                            |
    | SX            | Sint Maarten (parte neerlandesa)       |
    | SY            | República Árabe Siria                  |
    | SZ            | Esvatini                               |
    | TC            | Islas Turcas y Caicos                  |
    | TD            | Chad                                   |
    | TF            | Tierras Australes Francesas            |
    | TG            | Togo                                   |
    | TH            | Tailandia                              |
    | TJ            | Tayikistán                             |
    | TK            | Tokelau                                |
    | TL            | Timor-Leste                            |
    | TM            | Turkmenistán                           |
    | TN            | Túnez                                  |
    | TO            | Tonga                                  |
    | TR            | Turquía                                |
    | TT            | Trinidad y Tobago                      |
    | TV            | Tuvalu                                 |
    | TW            | Taiwán                                 |
    | TZ            | Tanzania, República Unida de           |
    | UA            | Ucrania                                |
    | UG            | Uganda                                 |
    | UM            | Islas menores alejadas de los Estados Unidos|
    | US            | Estados Unidos de América              |
    | UY            | Uruguay                                |
    | UZ            | Uzbekistán                             |
    | VA            | Ciudad del Vaticano                    |
    | VC            | San Vicente y las Granadinas           |
    | VE            | Venezuela (República Bolivariana de)   |
    | VG            | Islas Vírgenes Británicas              |
    | VI            | Islas Vírgenes de los Estados Unidos   |
    | VN            | Viet Nam                               |
    | VU            | Vanuatu                                |
    | WF            | Wallis y Futuna                        |
    | WS            | Samoa                                  |
    | XK            | Kosovo                                 |
    | YE            | Yemen                                  |
    | YT            | Mayotte                                |
    | ZA            | Sudáfrica                              |
    | ZM            | Zambia                                 |
    | ZW            | Zimbabue                               |

    ## **Valores permitidos en el campo lang:**
    Se debe ingresar un código de lengua válido según la norma ISO 639-1.
    | Código | Lenguas                                 |
    |--------|-----------------------------------------|
    | aa     | afar                                    |
    | ab     | abjasio (o abjasiano)                   |
    | ae     | avéstico                                |
    | af     | afrikáans                               |
    | ak     | akano                                   |
    | am     | amhárico                                |
    | an     | aragonés                                |
    | ar     | árabe                                   |
    | as     | asamés                                  |
    | av     | avar (o ávaro)                          |
    | ay     | aimara                                  |
    | az     | azerí                                   |
    | ba     | baskir                                  |
    | be     | bielorruso                              |
    | bg     | búlgaro                                 |
    | bh     | bhoyapurí                               |
    | bi     | bislama                                 |
    | bm     | bambara                                 |
    | bn     | bengalí                                 |
    | bo     | tibetano                                |
    | br     | bretón                                  |
    | bs     | bosnio                                  |
    | ca     | catalán                                 |
    | ce     | checheno                                |
    | ch     | chamorro                                |
    | co     | corso                                   |
    | cr     | cree                                    |
    | cs     | checo                                   |
    | cu     | eslavo eclesiástico antiguo             |
    | cv     | chuvasio                                |
    | cy     | galés                                   |
    | da     | danés                                   |
    | de     | alemán                                  |
    | dv     | maldivo (o dhivehi)                     |
    | dz     | dzongkha                                |
    | ee     | ewé                                     |
    | el     | griego (moderno)                        |
    | en     | inglés                                  |
    | eo     | esperanto                               |
    | es     | español (o castellano)                  |
    | et     | estonio                                 |
    | eu     | euskera                                 |
    | fa     | persa                                   |
    | ff     | fula                                    |
    | fi     | finés (o finlandés)                     |
    | fj     | fiyiano (o fiyi)                        |
    | fo     | feroés                                  |
    | fr     | francés                                 |
    | fy     | frisón (o frisio)                       |
    | ga     | irlandés (o gaélico)                    |
    | gd     | gaélico escocés                         |
    | gl     | gallego                                 |
    | gn     | guaraní                                 |
    | gu     | guyaratí (o guyaratí)                   |
    | gv     | manés (gaélico manés o de Isla de Man)  |
    | ha     | hausa                                   |
    | he     | hebreo                                  |
    | hi     | hindi (o hindú)                         |
    | ho     | hiri motu                               |
    | hr     | croata                                  |
    | ht     | haitiano                                |
    | hu     | húngaro                                 |
    | hy     | armenio                                 |
    | hz     | herero                                  |
    | ia     | interlingua                             |
    | id     | indonesio                               |
    | ie     | occidental                              |
    | ig     | igbo                                    |
    | ii     | yi de Sichuán                           |
    | ik     | iñupiaq                                 |
    | io     | ido                                     |
    | is     | islandés                                |
    | it     | italiano                                |
    | iu     | inuktitut (o inuit)                     |
    | ja     | japonés                                 |
    | jv     | javanés                                 |
    | ka     | georgiano                               |
    | kg     | kongo                                   |
    | ki     | kikuyu                                  |
    | kj     | kuanyama                                |
    | kk     | kazajo                                  |
    | kl     | groenlandés (o kalaallisut)             |
    | km     | camboyano (o jemer)                     |
    | kn     | canarés                                 |
    | ko     | coreano                                 |
    | kr     | kanuri                                  |
    | ks     | cachemiro (o cachemir)                  |
    | ku     | kurdo                                   |
    | kv     | komi                                    |
    | kw     | córnico                                 |
    | ky     | kirguís                                 |
    | la     | latín                                   |
    | lb     | luxemburgués                            |
    | lg     | luganda                                 |
    | li     | limburgués                              |
    | ln     | lingala                                 |
    | lo     | lao                                     |
    | lt     | lituano                                 |
    | lu     | luba-katanga (o chiluba)                |
    | lv     | letón                                   |
    | mg     | malgache (o malagasy)                   |
    | mh     | marshalés                               |
    | mi     | maorí                                   |
    | mk     | macedonio                               |
    | ml     | malayalam                               |
    | mn     | mongol                                  |
    | mr     | maratí                                  |
    | ms     | malayo                                  |
    | mt     | maltés                                  |
    | my     | birmano                                 |
    | na     | nauruano                                |
    | nb     | noruego bokmål                          |
    | nd     | ndebele del norte                       |
    | ne     | nepalí                                  |
    | ng     | ndonga                                  |
    | nl     | neerlandés (u holandés)                 |
    | nn     | nynorsk                                 |
    | no     | noruego                                 |
    | nr     | ndebele del sur                         |
    | nv     | navajo                                  |
    | ny     | chichewa                                |
    | oc     | occitano                                |
    | oj     | ojibwa                                  |
    | om     | oromo                                   |
    | or     | oriya                                   |
    | os     | osético                                 |
    | pa     | panyabí                                 |
    | pi     | pali                                    |
    | pl     | polaco                                  |
    | ps     | pastú                                   |
    | pt     | portugués                               |
    | qu     | quechua                                 |
    | rm     | romanche                                |
    | rn     | kirundi                                 |
    | ro     | rumano                                  |
    | ru     | ruso                                    |
    | rw     | ruandés (o kiñaruanda)                  |
    | sa     | sánscrito                               |
    | sc     | sardo                                   |
    | sd     | sindhi                                  |
    | se     | sami septentrional                      |
    | sg     | sango                                   |
    | si     | cingalés                                |
    | sk     | eslovaco                                |
    | sl     | esloveno                                |
    | sm     | samoano                                 |
    | sn     | shona                                   |
    | so     | somalí                                  |
    | sq     | albanés                                 |
    | sr     | serbio                                  |
    | ss     | suazi, swati, o siSwati                 |
    | st     | sesotho                                 |
    | su     | sundanés o sondanés                     |
    | sv     | sueco                                   |
    | sw     | suajili                                 |
    | ta     | tamil                                   |
    | te     | télugu                                  |
    | tg     | tayiko                                  |
    | th     | tailandés                               |
    | ti     | tigriña                                 |
    | tk     | turcomano                               |
    | tl     | tagalo                                  |
    | tn     | setsuana                                |
    | to     | tongano                                 |
    | tr     | turco                                   |
    | ts     | tsonga                                  |
    | tt     | tártaro                                 |
    | tw     | twi                                     |
    | ty     | tahitiano                               |
    | ug     | uigur                                   |
    | uk     | ucraniano                               |
    | ur     | urdu                                    |
    | uz     | uzbeko                                  |
    | ve     | venda                                   |
    | vi     | vietnamita                              |
    | vo     | volapük                                 |
    | wa     | valón                                   |
    | wo     | wolof                                   |
    | xh     | xhosa                                   |
    | yi     | yídish                                  |
    | yo     | yoruba                                  |
    | za     | chuan, chuang o zhuang                  |
    | zh     | chino                                   |
    | zu     | zulú                                    |




    """
    
    # Leer el archivo CSV y extraer los datos
    data = {}
    df_1 = pd.read_csv('temp_files/estudiantes_validados.csv')
    df_1['username'] = df_1['username'].apply(lambda x: str(x).replace('.0', '') if '.0' in str(x) else str(x))
    df = df_1[df_1['Estado'] == 'NO está en la BD esa cédula']
    df = df.drop_duplicates(subset=['username'])
    i = 0  # Inicializar el contador
    for i, row in df.iterrows():
        CREATEPASSWORD = row.get("createpassword")
        USERNAME = row.get("username")
        AUTH = "manual"
        PASSWORD = row.get("password")
        FIRSTNAME = row.get("firstname")
        LASTNAME = row.get("lastname")
        EMAIL = row.get("email")
        #MAILDISPLAY = row.get("maildisplay")
        CITY = row.get("city")
        COUNTRY = row.get("country")
        TIMEZONE = row.get("timezone")
        DESCRIPTION = row.get("description")
        FIRSTNAMEPHONETIC = ""
        LASTNAMEPHONETIC = row.get("lastnamephonetic")
        MIDDLENAME = ""
        ALTERNATENAME = ""
        INTERESTS = ""
        IDNUMBER = row.get("username")
        INSTITUTION = ""
        DEPARTMENT = ""
        PHONE1 = row.get("phone1")
        PHONE2 = ""
        ADDRESS = row.get("address")
        #LANG = ""
        CALENDARTYPE = ""
        THEME = ""
        #MAILFORMAT = ""
    
        data[f"users[{i}][createpassword]"] = CREATEPASSWORD
        data[f"users[{i}][username]"] = USERNAME
        data[f"users[{i}][auth]"] = AUTH
        data[f"users[{i}][password]"] = "P@SsW0RD123"
        data[f"users[{i}][firstname]"] = FIRSTNAME
        data[f"users[{i}][lastname]"] = LASTNAME
        data[f"users[{i}][email]"] = EMAIL
        #data[f"users[{i}][maildisplay]"] = MAILDISPLAY
        data[f"users[{i}][city]"] = CITY
        data[f"users[{i}][country]"] = COUNTRY
        data[f"users[{i}][timezone]"] = TIMEZONE
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
        #data[f"users[{i}][lang]"] = LANG
        #data[f"users[{i}][calendartype]"] = CALENDARTYPE
        #data[f"users[{i}][theme]"] = THEME
        #data[f"users[{i}][mailformat]"] = MAILFORMAT
        #data[f"users[{i}][customfields][0][type]"] = row.get("custom_type")
        #data[f"users[{i}][customfields][0][value]"] = row.get("custom_value")
        #data[f"users[{i}][preferences][0][type]"] = row.get("pref_type")
        #data[f"users[{i}][preferences][0][value]"] = row.get("pref_value")
        i += 1  # Incrementar el contador en cada iteración

    # Hacer la solicitud a Moodle
    url = f"{moodle_url}/webservice/rest/server.php"
    params = {
        "wstoken": moodle_token,
        "wsfunction": WS_FUNCTION,
        "moodlewsrestformat": "json"
    }
    #print(data)
    response = requests.post(url, params=params, data=data)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {"output": response.json()}
