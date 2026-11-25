#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Uso: $0 DIR"
    exit 1
fi

DIR="$1"
if [ ! -d "$DIR" ]; then
    echo "Error: $DIR no es un directorio válido"
    exit 1
fi

# Genera un hash para cada archivo y guarda el hash y la ruta en un archivo temporal
find "$DIR" -type f -print0 | while IFS= read -r -d '' file; do
    hash=$(sha256sum "$file" | awk '{print $1}')
    echo "$hash $file" >> /tmp/duplicates.tmp
done

# Agrupa los archivos por hash y muestra los grupos duplicados
awk '{print $2}' /tmp/duplicates.tmp | sort | uniq -d | while read -r file; do
    hash=$(awk -F' ' '{print $1}' /tmp/duplicates.tmp | grep -w "$(basename "$file")" | awk '{print $1}')
    echo "Archivo duplicado: $file"
    find "$DIR" -type f -exec sha256sum {} \; | grep "$hash" | awk '{print $2}'
done

# Limpia el archivo temporal
rm /tmp/duplicates.tmp
