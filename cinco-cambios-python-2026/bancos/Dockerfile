# 715 · Imagen de banco: Python oficial 3.14.10 + uv 0.13.6, y por uv las dos builds de CPython 3.14.10
# (con GIL y free-threaded, «3.14.10t»), del mismo proyecto python-build-standalone: una sola variable cambia.
FROM python:3.14.10-slim-trixie
RUN pip install --no-cache-dir pip==26.2.2 uv==0.13.6 \
 && uv python install 3.14.10 3.14.10t \
 && ln -s "$(uv python find 3.14.10)" /usr/local/bin/py-gil \
 && ln -s "$(uv python find 3.14.10t)" /usr/local/bin/py-t
WORKDIR /banco
COPY hilos.py /banco/
