# FastAPI + uvicorn sobre la slim oficial (el patrón del vídeo 153).
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY servidor.py .
EXPOSE 8080
CMD ["uvicorn", "servidor:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "warning"]
