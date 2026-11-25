FROM python:3.12.8-slim-bookworm
WORKDIR /app
COPY server.py .
RUN useradd --create-home app
USER app
EXPOSE 8080
CMD ["python", "server.py"]
