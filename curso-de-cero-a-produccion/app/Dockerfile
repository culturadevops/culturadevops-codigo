# El de producción: imagen pequeña, un usuario sin privilegios y el directorio de datos suyo.
FROM python:3.13-slim
RUN pip install --no-cache-dir "psycopg[binary]==3.2.*" \
 && useradd --system --uid 10001 --home /app tienda \
 && mkdir -p /datos && chown tienda /datos
COPY tienda.py /app/tienda.py
WORKDIR /app
USER tienda
CMD ["python", "-u", "tienda.py"]
