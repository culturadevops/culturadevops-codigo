# Use la imagen base oficial de Python
FROM python:3.10-slim

# Establece el trabajo actual como directorio de trabajo
WORKDIR /app

# Copia los archivos requirements.txt y main.py al directorio de trabajo
COPY requirements.txt .
COPY main.py .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto 8080
EXPOSE 8080

# Ejecuta la aplicación FastAPI con uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
