#!/usr/bin/env bash
# Copia ORIGEN a DESTINO/respaldo-AAAAMMDD.
set -euo pipefail

ORIGEN=${1:?uso: respaldo.sh ORIGEN DESTINO}
DESTINO=${2:?uso: respaldo.sh ORIGEN DESTINO}
FECHA=$(date +%Y%m%d)

mkdir -p $DESTINO
cd $DESTINO
cp -r $ORIGEN respaldo-$FECHA
echo "respaldo listo: $DESTINO/respaldo-$FECHA"
