# Use una imagen base de Python
FROM python:3.9-slim

# Establece el trabajo actual como directorio de trabajo
WORKDIR /app

# Copia los archivos requirements.txt y app.py al directorio de trabajo
COPY requirements.txt .
COPY app.py .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponga el puerto 8080
EXPOSE 8080

# Ejecuta la aplicación
CMD ["python", "app.py"]
