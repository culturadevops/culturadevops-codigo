#!/bin/bash
# Ejecuta la demo de recuperación a un punto en el tiempo y deja la salida literal en SALIDA.md. Desde Git Bash:
#   bash canales/cultura-devops/recursos/demo-postgres-pitr/ejecutar.sh
cd "$(dirname "$0")" || exit 1
export MSYS_NO_PATHCONV=1
AQUI=$(cygpath -w "$PWD")
{
  echo "# SALIDA — Postgres: vuelve al segundo antes del desastre (cultura-devops)"
  echo
  echo "> Corrida del $(date '+%Y-%m-%d %H:%M') en postgres:18 (un solo contenedor: servidor, archivo de WAL y copia base)."
  echo
  echo '```'
  docker run --rm -u postgres -v "$AQUI:/trabajo" postgres:18 bash -c "postgres --version; bash /trabajo/correr.sh" 2>&1
  echo '```'
} > SALIDA.md
cat SALIDA.md
