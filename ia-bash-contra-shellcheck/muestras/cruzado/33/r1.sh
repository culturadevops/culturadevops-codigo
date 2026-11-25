#!/bin/bash

DIR=$1
DEST=$2

if [ ! -d "$DIR" ]; then
    echo "El directorio especificado no existe."
    exit 1
fi

if [ ! -d "$DEST" ]; then
    echo "El destino especificado no es un directorio."
    exit 1
fi

find "$DIR" -type f -name "*.log" -print0 | while IFS= read -r -d $'\0' file; do
    if [ -f "$file" ]; then
        cat "$file" >> "$DEST/todo.log"
    fi
done

echo "Archivos de log combinados en $DEST/todo.log"
