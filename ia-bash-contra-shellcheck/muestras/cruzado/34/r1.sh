#!/bin/bash

DIR=$1
UMBRAL=$2

# Corregido: el sed original ('s/%://') no quitaba el '%' y la comparación fallaba
USO=$(df -P "$DIR" | tail -n 1 | awk '{print $5}' | sed 's/%//' )

if [ "$USO" -ge "$UMBRAL" ]; then
    echo "ALERTA"
else
    echo "OK"
fi
