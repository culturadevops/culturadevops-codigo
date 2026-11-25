#!/usr/bin/env bash
set -u

if [ "$#" -ne 1 ]; then
    echo "Uso: $0 FILE" >&2
    exit 2
fi

file="$1"

if [ ! -f "$file" ] || [ ! -r "$file" ]; then
    echo "Error: no se puede leer '$file'" >&2
    exit 2
fi

falta=0

while IFS= read -r ruta || [ -n "$ruta" ]; do
    ruta="${ruta%$'\r'}"
    [ -z "$ruta" ] && continue
    if [ ! -e "$ruta" ] && [ ! -L "$ruta" ]; then
        printf 'FALTA: %s\n' "$ruta"
        falta=1
    fi
done < "$file"

exit "$falta"
