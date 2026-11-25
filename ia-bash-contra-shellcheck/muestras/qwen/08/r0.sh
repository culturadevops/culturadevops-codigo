#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Uso: $0 DIR"
    exit 1
fi

DIR=$1

if [ ! -d "$DIR" ]; then
    echo "Error: $DIR no es un directorio válido."
    exit 1
fi

find "$DIR" -type f -exec bash -c '
    for file; do
        ext="${file##*.}"
        base="${file%.*}"
        mv "$file" "${base,,}.${ext}"
    done' bash {} +

echo "Se han cambiado las extensiones a minúsculas en todos los archivos del directorio."
