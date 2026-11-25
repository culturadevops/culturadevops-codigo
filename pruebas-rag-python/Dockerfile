FROM python:3.13.17-slim
RUN pip install --no-cache-dir "psycopg[binary]==3.2.10"
WORKDIR /app
COPY rag.py ./
COPY docs ./docs
ENTRYPOINT ["python", "rag.py"]
