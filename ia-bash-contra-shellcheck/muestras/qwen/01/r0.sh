#!/bin/bash

# Verificar si se proporcionaron dos argumentos
if [ "$#" -ne 2 ]; then
    echo "Uso: $0 DIR DEST"
    exit 1
fi

DIR=$1
DEST=$2

# Verificar si DIR existe
if [ ! -d "$DIR" ]; then
    echo "El directorio $DIR no existe."
    exit 1
fi

# Verificar si DEST existe, si no, crearlo
if [ ! -d "$DEST" ]; then
    mkdir -p "$DEST"
fi

# Copiar archivos .log de DIR a DEST
find "$DIR" -maxdepth 1 -type f -name "*.log" -exec cp {} "$DEST" \;
