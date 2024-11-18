# Usa una imagen oficial de Python
FROM python:3.11-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia las dependencias y las instala
COPY requirements.txt /app/
RUN pip cache purge
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install gunicorn uvicorn

# Copia el código fuente de la API
COPY . /app/

# Copia el archivo .env al directorio de trabajo en el contenedor
COPY .env /app/.env

# Expone el puerto
EXPOSE 8002

# Comando para ejecutar Gunicorn con Uvicorn, con un timeout de 120 segundos
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8002", "--timeout", "120", "main:app"]
