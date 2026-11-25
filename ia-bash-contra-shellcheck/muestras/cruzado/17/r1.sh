#!/bin/bash

# Verificar si se proporcionaron dos argumentos
if [ "$#" -ne 2 ]; then
    echo "Uso: $0 DIR DEST"
    exit 1
fi

DIR="$1"
DEST="$2"

# Crear la estructura de directorios en DEST si no existe
mkdir -p "$DEST"

# Encontrar todos los archivos en DIR y sus subdirectorios
find "$DIR" -type f -print0 | while IFS= read -r -d '' file; do
    # Obtener el nombre del archivo en DEST
    dest_file="${file#"$DIR"/}"
    dest_file="$DEST/$dest_file"
    dir_name=$(dirname "$dest_file")

    # Crear la estructura de directorios en DEST si es necesario
    mkdir -p "$dir_name"

    # Verificar si el archivo en DEST es más antiguo o no existe
    if [ ! -f "$dest_file" ] || [ "$file" -nt "$dest_file" ]; then
        # Copiar el archivo
        cp --preserve=timestamps "$file" "$dest_file"
    fi
done
