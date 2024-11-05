from fastapi import FastAPI, UploadFile, APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import pandas as pd
from io import BytesIO
import regex as re
import unidecode
import os
from jwt_manager import JWTBearer

validacion_nombres_apellidos_router = APIRouter()

def verificar_cruzados(row: pd.Series) -> str:
    """
    Verificar si hay coincidencias entre los nombres y apellidos, y si son iguales en más de 3 casos.

    :param row: Fila de un DataFrame que contiene los resultados de la búsqueda de nombres y apellidos cruzados.
    :type row: pd.Series
    :return: 'SI' si hay más de 3 coincidencias, 'NO' de lo contrario.
    :rtype: str
    """
    columnas_a_verificar = [
        'primer_nombre_es_apellido', 'segundo_nombre_es_apellido',
        'primer_apellido_es_nombre', 'segundo_apellido_es_nombre'
    ]

    num_coincidencias = sum(row[columna] for columna in columnas_a_verificar)
    if num_coincidencias == 0:
        return 'NO'
    elif num_coincidencias >= 3:
        return 'SI'
    else:
        return 'SI'

def validar_nombre_apellido(nombre: str) -> str:
    """
    Verificar si un nombre o apellido es válido.

    :param nombre: Nombre o apellido a verificar.
    :type nombre: str
    :return: 'SI' si el nombre o apellido es inválido, 'NO' de lo contrario.
    :rtype: str
    """
    # Verificar si la cadena es vacía o solo contiene espacios
    if not nombre or not nombre.strip():
        return "SI"
    
    # Verificar si la longitud es menor a 3
    if len(nombre) < 3:
        return "SI"
    
    # Verificar si la cadena es 'NAN'
    if nombre.upper() == 'NAN':
        return "SI"
    
    # Verificar si contiene caracteres no permitidos (solo letras y espacios, incluyendo acentos)
    if not re.match(r"^[\p{L}\s]+$", nombre):
        return "SI"
    
    return "NO"

def encontrar_similitudes(token: str, lista: list) -> bool:
    """
    Verifica si un token se encuentra en una lista de valores.

    :param token: Token a buscar.
    :type token: str
    :param lista: Lista en la cual se buscará el token.
    :type lista: list
    :return: True si el token se encuentra en la lista, False de lo contrario.
    :rtype: bool
    """
    return token in lista

def nuevo_estan_cruzados(datos: pd.DataFrame) -> pd.DataFrame:
    """
    Evalúa si los nombres y apellidos están cruzados entre sí.

    :param datos: DataFrame que contiene los nombres y apellidos a evaluar.
    :type datos: pd.DataFrame
    :return: DataFrame con la evaluación de si los nombres y apellidos están cruzados.
    :rtype: pd.DataFrame
    """
    fuente_de_busqueda = "routers/Nombres y apellidos.xlsx"
    df_nombres_apellidos = pd.read_excel(fuente_de_busqueda)

    # Normalizar nombres y apellidos
    datos['NOMBRES'] = datos["NOMBRES"].str.strip().apply(unidecode.unidecode).str.upper()
    datos['vector_nombres'] = datos['NOMBRES'].str.split()
    datos['primer_nombre'] = datos['vector_nombres'].map(lambda x: x[0] if len(x) > 0 else None)
    datos['primer_nombre_es_apellido'] = datos['primer_nombre'].apply(lambda x: encontrar_similitudes(x, df_nombres_apellidos['Apellido'].tolist()))

    datos['segundo_nombre'] = datos['vector_nombres'].apply(lambda x: x[1] if len(x) >= 2 else None)
    datos['segundo_nombre_es_apellido'] = datos['segundo_nombre'].apply(lambda x: encontrar_similitudes(x, df_nombres_apellidos['Apellido'].tolist()))

    datos['APELLIDOS'] = datos["APELLIDOS"].str.strip().apply(unidecode.unidecode).str.upper()
    datos['vector_apellidos'] = datos['APELLIDOS'].str.split()
    datos['primer_apellido'] = datos['vector_apellidos'].map(lambda x: x[0] if len(x) > 0 else None)
    datos['primer_apellido_es_nombre'] = datos['primer_apellido'].apply(lambda x: encontrar_similitudes(x, df_nombres_apellidos['Nombre'].tolist()))

    datos['segundo_apellido'] = datos['vector_apellidos'].apply(lambda x: x[1] if len(x) >= 2 else None)
    datos['segundo_apellido_es_nombre'] = datos['segundo_apellido'].apply(lambda x: encontrar_similitudes(x, df_nombres_apellidos['Nombre'].tolist()))

    # Evaluar los resultados de verificación cruzada
    datos['estan_cruzados'] = datos.apply(verificar_cruzados, axis=1)

    # Eliminar columnas innecesarias
    columnas_a_eliminar = ['vector_nombres', 'primer_nombre', 'primer_nombre_es_apellido', 'segundo_nombre',
                           'segundo_nombre_es_apellido', 'vector_apellidos', 'primer_apellido', 
                           'primer_apellido_es_nombre', 'segundo_apellido', 'segundo_apellido_es_nombre']
    datos.drop(columns=columnas_a_eliminar, inplace=True)
    return datos

@validacion_nombres_apellidos_router.post("/validar_nombres_apellidos/", tags=['Validacion_Inicial'], dependencies=[Depends(JWTBearer())])
async def validar_nombres_apellidos():
    """
    Valida los nombres y apellidos de los estudiantes, verificando su validez y si están cruzados.

    :return: JSONResponse con los resultados de la validación de nombres y apellidos.
    :rtype: JSONResponse
    """
    try:
        # Ruta del archivo Excel a validar
        file_path = 'temp_files/validacion_inicial.xlsx'

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"El archivo en la ruta '{file_path}' no fue encontrado.")

        # Leer el archivo Excel
        df_estudiantes = pd.read_excel(file_path)
        df_estudiantes['NOMBRES'] = df_estudiantes['NOMBRES'].astype(str)
        df_estudiantes['APELLIDOS'] = df_estudiantes['APELLIDOS'].astype(str)

        # Validar nombres y apellidos
        df_estudiantes['Nombre_Invalido'] = df_estudiantes['NOMBRES'].apply(validar_nombre_apellido)
        df_estudiantes['Apellido_Invalido'] = df_estudiantes['APELLIDOS'].apply(validar_nombre_apellido)

        # Evaluar si los nombres y apellidos están cruzados
        df_estudiantes = nuevo_estan_cruzados(df_estudiantes)

        # Reemplazar 'NAN' por valores más claros
        df_estudiantes['NOMBRES'] = df_estudiantes['NOMBRES'].replace('NAN', 'SIN NOMBRES')
        df_estudiantes['APELLIDOS'] = df_estudiantes['APELLIDOS'].replace('NAN', 'SIN APELLIDOS')

        # Guardar el archivo actualizado
        df_estudiantes.to_excel(file_path, index=False)

        # Contar resultados
        si_rows_count = ((df_estudiantes['Nombre_Invalido'] == 'SI') | (df_estudiantes['Apellido_Invalido'] == 'SI') | (df_estudiantes['estan_cruzados'] == 'SI')).sum()
        no_rows_count = ((df_estudiantes['Nombre_Invalido'] == 'NO') & (df_estudiantes['Apellido_Invalido'] == 'NO') & (df_estudiantes['estan_cruzados'] == 'NO')).sum()

        response_data = {
            "validacion_nombres_apellidos": {
                "correctos": int(no_rows_count),
                "incorrectos": int(si_rows_count)
            }
        }
    
        # Devolver la respuesta en formato JSON
        return JSONResponse(content=response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Un error ocurrió: {str(e)}")

