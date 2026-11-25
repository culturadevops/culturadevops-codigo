#!/bin/sh
# Lanza la demo en Docker y guarda la salida en SALIDA.md. vendor/ queda en un volumen aparte (no en el repo).
cd "$(dirname "$0")"
{ echo '# Salida real — seguridad en el pipeline para PHP'; echo; echo "Ejecutado el $(date -u +%Y-%m-%dT%H:%MZ) en composer:2."; echo; echo '```'
  MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd -W 2>/dev/null || pwd):/demo" -v demo-php-vendor-a:/demo/app/vendor -v demo-php-vendor-b:/demo/app-arreglada/vendor composer:2 sh /demo/ejecutar.sh
  echo '```'; } > SALIDA.md 2>&1
