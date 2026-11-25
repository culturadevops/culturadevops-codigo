#!/usr/bin/env bash
# Uso: script.sh DIR DEST
# Concatena en DEST/todo.log todos los .log de DIR (recursivo), ordenados por nombre de archivo.

set -euo pipefail

usage() {
    echo "Uso: $(basename "$0") DIR DEST" >&2
    exit 1
}

[[ $# -eq 2 ]] || usage

DIR=$1
DEST=$2

if [[ ! -d "$DIR" ]]; then
    echo "Error: '$DIR' no es un directorio" >&2
    exit 1
fi

mkdir -p -- "$DEST"

DIR_ABS=$(realpath -- "$DIR")
DEST_ABS=$(realpath -- "$DEST")
OUT="$DEST_ABS/todo.log"

# Archivo temporal en DEST para no incluir la salida en la búsqueda
TMP=$(mktemp -- "$DEST_ABS/.todo.log.XXXXXX")
trap 'rm -f -- "$TMP"' EXIT

count=0

# Formato: "basename/ruta\0"; el basename no contiene '/', así que se
# ordena por nombre de archivo y, a igualdad, por ruta completa.
while IFS= read -r -d '' entry; do
    file=${entry#*/}
    file_abs=$(realpath -- "$file")

    # Saltar la salida y el temporal si DEST está dentro de DIR
    [[ "$file_abs" == "$OUT" || "$file_abs" == "$TMP" ]] && continue

    if [[ -r "$file" ]]; then
        cat -- "$file" >> "$TMP"
        count=$((count + 1))
    else
        echo "Aviso: no se puede leer '$file', se omite" >&2
    fi
done < <(find "$DIR_ABS" -type f -name '*.log' -printf '%f/%p\0' | LC_ALL=C sort -z)

mv -f -- "$TMP" "$OUT"
trap - EXIT

echo "Concatenados $count archivo(s) .log en '$OUT'"
