#!/usr/bin/env bash
set -euo pipefail

MAX=5

usage() {
    echo "Uso: $(basename "$0") FILE" >&2
    exit 1
}

[[ $# -eq 1 ]] || usage
FILE="$1"
[[ -n "$FILE" ]] || usage

dir=$(dirname -- "$FILE")
if [[ ! -d "$dir" ]]; then
    echo "Error: el directorio '$dir' no existe" >&2
    exit 1
fi
if [[ -e "$FILE" && ! -f "$FILE" ]]; then
    echo "Error: '$FILE' existe pero no es un archivo regular" >&2
    exit 1
fi

if [[ -f "$FILE" ]]; then
    # Borrar el más viejo
    rm -f -- "${FILE}.${MAX}"

    # Desplazar FILE.(n) -> FILE.(n+1), de mayor a menor
    for (( i = MAX - 1; i >= 1; i-- )); do
        if [[ -e "${FILE}.${i}" ]]; then
            mv -f -- "${FILE}.${i}" "${FILE}.$(( i + 1 ))"
        fi
    done

    # FILE -> FILE.1
    mv -f -- "$FILE" "${FILE}.1"

    # Crear FILE nuevo vacío conservando permisos y propietario del anterior
    : > "$FILE"
    chmod --reference="${FILE}.1" -- "$FILE" 2>/dev/null || true
    chown --reference="${FILE}.1" -- "$FILE" 2>/dev/null || true
else
    : > "$FILE"
fi

echo "Rotado: $FILE"
