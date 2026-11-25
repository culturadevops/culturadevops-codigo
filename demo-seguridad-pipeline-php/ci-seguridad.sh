#!/bin/sh
# ci-seguridad.sh — el job de seguridad del pipeline para PHP. Falla si hay hallazgos.
# Uso: ci-seguridad.sh <carpeta-del-código>
set -u
cd "$1"
fallo=0
echo "== psalm --taint-analysis (de dónde viene el dato y adónde llega)"
vendor/bin/psalm --taint-analysis --no-progress --output-format=compact --monochrome || fallo=1
echo "== composer audit (dependencias de composer.lock, sin las de desarrollo)"
composer audit --no-dev --format=plain || fallo=1
if [ $fallo -ne 0 ]; then echo "PIPELINE: FALLA (hay hallazgos de seguridad)"; exit 1; fi
echo "PIPELINE: PASA"
