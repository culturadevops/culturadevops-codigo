#!/bin/bash

# Verifica si se proporcionaron dos argumentos
if [ "$#" -ne 2 ]; then
    echo "Uso: $0 FILE CLAVE"
    exit 1
fi

FILE=$1
CLAVE=$2

# Lee el archivo y busca la clave (sin tubería, para que exit afecte al script)
while IFS='=' read -r key value; do
    if [ "$key" == "$CLAVE" ]; then
        echo "$value"
        exit 0
    fi
done < <(grep -v '^#' "$FILE")

echo "Clave no encontrada"
exit 1
