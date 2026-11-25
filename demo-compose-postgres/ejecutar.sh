#!/bin/bash
# Corre la demo de Docker Compose + PostgreSQL y deja la salida literal en SALIDA.md. Desde Git Bash:
#   bash canales/cultura-devops/recursos/demo-compose-postgres/ejecutar.sh
cd "$(dirname "$0")" || exit 1
export MSYS_NO_PATHCONV=1
{
  echo "# SALIDA — Docker Compose con PostgreSQL (cultura-devops)"
  echo
  echo "> Corrida del $(date '+%Y-%m-%d %H:%M'). Docker $(docker version --format '{{.Server.Version}}'), $(docker compose version), imagen postgres:18."
  echo
  echo '```'
  bash ./correr.sh
  echo '```'
} > SALIDA.md
cat SALIDA.md
