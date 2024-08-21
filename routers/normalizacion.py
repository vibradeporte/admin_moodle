from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import JSONResponse,PlainTextResponse
import pandas as pd
import os
from fuzzywuzzy import process
from collections import Counter
import numpy as np
import math
import uvicorn
import re 

normalizacion_router = APIRouter()

class StringScoreCalculator:
    def __init__(self):
        self.bag = np.zeros((256, 256))

    def calculate_similarity_score(self, array1, array2):
        if not isinstance(array1, str) or not isinstance(array2, str):
            return 0.0

        byte_array1 = array1.encode('utf-8')
        byte_array2 = array2.encode('utf-8')

        return self._calculate_similarity_score(byte_array1, byte_array2)

    def _calculate_similarity_score(self, byte_array1, byte_array2):
        length1 = len(byte_array1)
        length2 = len(byte_array2)
        minLength = min(length1, length2)
        maxLength = max(length1, length2)

        if minLength == 0 or maxLength <= 1:
            return 0.0

        symmetricDifferenceCardinality = 0

        for i in range(1, length1):
            self.bag[byte_array1[i-1] & 0xFF][byte_array1[i] & 0xFF] += 1
            symmetricDifferenceCardinality += 1

        for j in range(1, length2):
            bigram_count = self.bag[byte_array2[j-1] & 0xFF][byte_array2[j] & 0xFF] - 1
            self.bag[byte_array2[j-1] & 0xFF][byte_array2[j] & 0xFF] = bigram_count

            if bigram_count >= 0:
                symmetricDifferenceCardinality -= 1
            else:
                symmetricDifferenceCardinality += 1

        for i in range(1, length1):
            self.bag[byte_array1[i-1] & 0xFF][byte_array1[i] & 0xFF] = 0
        for j in range(1, length2):
            self.bag[byte_array2[j-1] & 0xFF][byte_array2[j] & 0xFF] = 0

        rabbit_score = max(1.0 - math.pow(1.2 * symmetricDifferenceCardinality / maxLength, 5.0 / math.log10(maxLength + 1)), 0)
        return rabbit_score * 100

def find_representative_city(city_list, threshold):
    clusters = {}
    for city in city_list:
        if not isinstance(city, str):
            city = str(city)
        added_to_cluster = False
        for rep_city in clusters:
            calculator = StringScoreCalculator()
            if calculator.calculate_similarity_score(city, rep_city) > threshold:
                clusters[rep_city].append(city)
                added_to_cluster = True
                break
        if not added_to_cluster:
            clusters[city] = [city]
    
    representative_names = {}
    for rep_city, similar_cities in clusters.items():
        most_common_city = Counter(similar_cities).most_common(1)[0][0]
        representative_names[rep_city] = most_common_city
    
    return representative_names

def map_cities_to_representative(city_list, representative_names, threshold):
    city_mapping = []
    calculator = StringScoreCalculator()
    for city in city_list:
        if not isinstance(city, str):
            city = str(city)
        match = process.extractOne(city, representative_names.keys(), scorer=calculator.calculate_similarity_score)
        if match[1] > threshold:
            city_mapping.append((city, representative_names[match[0]]))
        else:
            city_mapping.append((city, city))
    return city_mapping


def validar_pais(pais):
    if not isinstance(pais, str):
        return 'SI'
    if len(pais) == 0 or len(pais) < 3:
        return 'SI'
    if not re.match("^[a-zA-Z ]+$", pais):
        return 'SI'
    return 'NO'

@normalizacion_router.post("/Normalizacion/", tags=['Validacion_Secundaria'])
async def normalizar():
    try:
        file_path = 'temp_files/validacion_inicial.xlsx'

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"El archivo en la ruta '{file_path}' no fue encontrado.")

        df = pd.read_excel(file_path)
        df['El campo del pais esta vacío'] = df['PAIS_DE_RESIDENCIA'].apply(validar_pais)
        similarity_threshold = 80
        representative_names_empresa = find_representative_city(df['EMPRESA'], threshold=similarity_threshold)
        representative_names_ciudad = find_representative_city(df['CIUDAD'], threshold=similarity_threshold)
        empresa_mapping = map_cities_to_representative(df['EMPRESA'], representative_names_empresa, threshold=similarity_threshold)
        ciudad_mapping = map_cities_to_representative(df['CIUDAD'], representative_names_ciudad, threshold=similarity_threshold)

        df['EMPRESA'] = [mapped[1] for mapped in empresa_mapping]
        df['CIUDAD'] = [mapped[1] for mapped in ciudad_mapping]
        print(df)
        df.to_excel(file_path, index=False)

        message = (
            f"Normalización de ciudad y empresa completada exitosamente."
        )
        return PlainTextResponse(content=message)  
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


