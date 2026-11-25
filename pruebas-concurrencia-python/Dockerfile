# Banco del vídeo 772 «Concurrencia en Python medida» (cultura-devops).
# No hay imagen oficial de Docker con el CPython free-threaded (2026-11-04: python:3.14* no tiene variantes «t»).
# Por eso los DOS intérpretes salen del mismo sitio: python-build-standalone instalado con uv, versiones fijadas.
# Así la única diferencia entre los dos es el GIL, no el compilador ni la distribución.
FROM astral/uv:0.13.7-trixie-slim

ENV UV_PYTHON_INSTALL_DIR=/opt/python
RUN uv python install 3.14.10 3.14.10+freethreaded \
 && ln -s "$(uv python find 3.14.10)" /usr/local/bin/python3.14 \
 && ln -s "$(uv python find 3.14.10+freethreaded)" /usr/local/bin/python3.14t \
 && python3.14 -VV && python3.14t -VV

WORKDIR /banco
COPY *.py /banco/
