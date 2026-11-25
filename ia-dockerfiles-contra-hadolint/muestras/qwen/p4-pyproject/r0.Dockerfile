# Use una imagen base de Python
FROM python:3.11-slim

# Establecer el trabajo actual como directorio de trabajo
WORKDIR /app

# Copiar los archivos del proyecto
COPY pyproject.toml .
COPY src/servicio/__init__.py .
COPY src/servicio/main.py .

# Instalar las dependencias
RUN pip install --no-cache-dir -e .

# Exposición del puerto 8080
EXPOSE 8080

# Comando a ejecutar
CMD ["python", "-m", "servicio"]
