#!/usr/bin/env bash
# Corre el escenario cronometrado «tiempos» del vídeo 800 SOLO cuando:
#  1) ya existe SALIDA-deno-rust.md (el banco de Deno terminó), y
#  2) se puede tomar el candado _logs/banco.lock (nadie más está midiendo).
# Suelta el candado al salir, pase lo que pase.
set -u
AQUI="$(cd "$(dirname "$0")" && pwd)"
SENAL=<proyecto>/canales/cultura-devops/recursos/pruebas-lenguajes-vs/SALIDA-deno-rust.md
CANDADO=<proyecto>/_logs/banco.lock
until [ -f "$SENAL" ]; do sleep 60; done
until mkdir "$CANDADO" 2>/dev/null; do sleep 60; done
trap 'rmdir "$CANDADO"' EXIT
echo "candado tomado $(date '+%F %T')"
cd "$AQUI" && PYTHONUTF8=1 python correr.py "${1:-tiempos}"
echo "medición terminada $(date '+%F %T')"
