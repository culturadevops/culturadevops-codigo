#!/bin/bash

DIR=$1

if [ ! -d "$DIR" ]; then
    echo "El directorio especificado no existe."
    exit 1
fi

find "$DIR" -type f -name "*.tar.gz" | while read -r file; do
    filename=$(basename "$file" .tar.gz)
    mkdir -p "$DIR/$filename"
    tar -xzf "$file" -C "$DIR/$filename"
done
