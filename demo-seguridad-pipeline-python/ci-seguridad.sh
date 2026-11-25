#!/bin/sh
# ci-seguridad.sh — el job de seguridad del pipeline: falla si hay hallazgos de severidad MEDIA o ALTA.
# Uso: ci-seguridad.sh <carpeta-del-código>   (NIVEL=-lll para fallar solo con las altas)
set -u
cd "$1"
NIVEL="${NIVEL:--ll}"
fallo=0
echo "== bandit (código, umbral $NIVEL)"
bandit -q -r . $NIVEL -f txt || fallo=1
echo "== semgrep (reglas de Python, Flask y secretos)"
semgrep --config p/python --config p/flask --config p/secrets --metrics=off --quiet --error . >/dev/null 2>&1 || { echo "semgrep: hay hallazgos"; fallo=1; }
echo "== pip-audit (dependencias de requirements.txt)"
pip-audit -r requirements.txt --progress-spinner off 2>&1 | tail -n 4 || true
pip-audit -r requirements.txt --progress-spinner off >/dev/null 2>&1 || fallo=1
if [ $fallo -ne 0 ]; then echo "PIPELINE: FALLA (hay hallazgos de seguridad)"; exit 1; fi
echo "PIPELINE: PASA"
