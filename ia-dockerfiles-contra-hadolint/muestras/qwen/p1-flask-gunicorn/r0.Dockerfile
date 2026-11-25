# Use una imagen base de Python
FROM python:3.11-slim

# Establecer el trabajo actual como directorio de trabajo
WORKDIR /app

# Copiar los archivos requirements.txt y app.py al directorio de trabajo
COPY requirements.txt .
COPY app.py .

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto 8080
EXPOSE 8080

# Comando a ejecutar la aplicación
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
