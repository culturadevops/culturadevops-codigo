FROM python:3.12.8-slim-bookworm
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir . && useradd --create-home app
USER app
EXPOSE 8080
CMD ["servicio"]
