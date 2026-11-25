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

find "$DIR" -type f -name "*.txt" | while read -r file; do
    if grep -q $'\r' "$file"; then
        sed -i 's/\r$//' "$file"
    fi
done
