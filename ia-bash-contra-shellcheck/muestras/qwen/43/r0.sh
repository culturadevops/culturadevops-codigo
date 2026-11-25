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

# Copiar solo archivos .txt de DIR y sus subdirectorios a DEST
find "$DIR" -type f -name "*.txt" -print0 | xargs -0 -I {} cp --parents {} "$DEST"
