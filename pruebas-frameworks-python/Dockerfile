# Una imagen por framework: docker build --build-arg FW=django -t cd-fwpy-django:1 .
# La misma base que el banco «¿Python o X?» (python:3.13.17-slim). Cada imagen instala SOLO su framework y su servidor,
# con todas las versiones fijadas en req/<fw>.txt (pip freeze de la primera construcción; las directas están en req/<fw>.in).
FROM python:3.13.17-slim
ARG FW
WORKDIR /app
COPY req/${FW}.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ /app/
ENV FW=${FW} WORKERS=2 PYTHONUNBUFFERED=1
EXPOSE 8080
ENTRYPOINT ["sh", "/app/arrancar.sh"]
