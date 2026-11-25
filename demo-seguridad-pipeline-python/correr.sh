#!/bin/sh
# Lanza la demo en Docker y guarda la salida en SALIDA.md.
cd "$(dirname "$0")"
{ echo '# Salida real — seguridad en el pipeline para Python'; echo; echo "Ejecutado el $(date -u +%Y-%m-%dT%H:%MZ) en python:3.13-slim."; echo; echo '```'
  MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd -W 2>/dev/null || pwd):/demo" python:3.13-slim sh /demo/ejecutar.sh
  echo '```'; } > SALIDA.md 2>&1
