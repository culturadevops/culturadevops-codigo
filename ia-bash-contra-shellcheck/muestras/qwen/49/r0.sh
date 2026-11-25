#!/bin/bash

# Verificar si se proporcionaron dos argumentos
if [ "$#" -ne 2 ]; then
    echo "Uso: $0 FILE DEST"
    exit 1
fi

FILE=$1
DEST=$2

# Verificar si el archivo de destino existe
if [ -f "$DEST/$FILE" ]; then
    # Si existe, agregar la fecha y hora al nombre del archivo
    NEW_NAME="${FILE}_$(date +%Y%m%d_%H%M%S)"
    cp "$FILE" "$DEST/$NEW_NAME"
else
    # Si no existe, simplemente copiar el archivo
    cp "$FILE" "$DEST/$FILE"
fi
