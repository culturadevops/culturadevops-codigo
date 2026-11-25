# Imagen del job: Python + boto3 encima de postgres:18.6-alpine, para tener pg_dump/pg_restore/psql 18.6 (los del servidor).
FROM postgres:18.6-alpine
RUN apk add --no-cache python3 py3-pip && pip install --no-cache-dir --break-system-packages boto3
COPY respaldo.py /usr/local/bin/respaldo.py
RUN printf '#!/bin/sh\nexec python3 /usr/local/bin/respaldo.py "$@"\n' > /usr/local/bin/respaldo && chmod +x /usr/local/bin/respaldo
ENTRYPOINT []
