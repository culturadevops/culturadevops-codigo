#!/bin/bash

if [ -z "$1" ]; then
    echo "Debes proporcionar un directorio como argumento."
    exit 1
fi

DIR=$1

if [ ! -d "$DIR" ]; then
    echo "El argumento proporcionado no es un directorio válido."
    exit 1
fi

find "$DIR" -maxdepth 1 -type f -name "*.txt" -exec awk 'BEGIN{FS=ORS} {print FILENAME ": " NF}' {} \;
