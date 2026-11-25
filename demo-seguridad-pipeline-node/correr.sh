#!/bin/sh
# Lanza la demo en Docker y guarda la salida en SALIDA.md. node_modules queda en volúmenes aparte.
cd "$(dirname "$0")"
D="$(pwd -W 2>/dev/null || pwd)"
{ echo '# Salida real — seguridad en el pipeline para Node.js'; echo; echo "Ejecutado el $(date -u +%Y-%m-%dT%H:%MZ)."; echo; echo '```'
  MSYS_NO_PATHCONV=1 docker run --rm -v "$D:/demo" python:3.13-slim sh /demo/ejecutar-njsscan.sh
  echo
  MSYS_NO_PATHCONV=1 docker run --rm -v "$D:/demo" -v demo-node-mods-a:/demo/app/node_modules -v demo-node-mods-b:/demo/app-arreglada/node_modules node:22-slim sh /demo/ejecutar-node.sh
  echo '```'; } > SALIDA.md 2>&1
