#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Uso: $0 DIR"
    exit 1
fi

DIR=$1

if [ ! -d "$DIR" ]; then
    echo "El directorio especificado no existe."
    exit 1
fi

find "$DIR" -maxdepth 1 -type f -name "*.txt" | while read -r file; do
    mod_date=$(stat -c %y "$file" | awk '{print $1}' | sed 's/\/\///;s/ /-/g')
    new_name="${mod_date}_$(basename "$file")"
    mv "$file" "$new_name"
done
