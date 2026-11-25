FROM python:3.13.17-slim
RUN pip install --no-cache-dir kopf==1.45.2 kubernetes==37.0.1
WORKDIR /app
COPY operador.py .
CMD ["kopf", "run", "--standalone", "--namespace", "default", "/app/operador.py"]
