#!/usr/bin/env bash
# Espera a que termine el banco de Deno (SALIDA-deno-rust.md), toma el candado de medición, mide y lo suelta.
set -u
cd "$(dirname "$0")"
SENAL=<proyecto>/canales/cultura-devops/recursos/pruebas-lenguajes-vs/SALIDA-deno-rust.md
LOCK=<proyecto>/_logs/banco.lock
LIMITE=$(( $(date +%s) + 3*3600 ))
while [ ! -f "$SENAL" ]; do
  [ "$(date +%s)" -gt "$LIMITE" ] && { echo "[X] 3 h sin $SENAL: no mido"; exit 3; }
  sleep 60
done
echo "[ok] existe $SENAL ($(date '+%H:%M'))"
until mkdir "$LOCK" 2>/dev/null; do
  [ "$(date +%s)" -gt "$LIMITE" ] && { echo "[X] 3 h sin candado: no mido"; exit 4; }
  sleep 60
done
trap 'rmdir "$LOCK"; echo "[ok] candado suelto ($(date +%H:%M))"' EXIT
echo "[ok] candado tomado ($(date '+%H:%M'))"
PYTHONUTF8=1 python correr.py medir > _medicion.md
rc=$?
echo "[fin] correr.py medir rc=$rc"
exit $rc
