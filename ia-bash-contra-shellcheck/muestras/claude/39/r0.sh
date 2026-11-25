#!/usr/bin/env bash
set -euo pipefail

usage() {
    echo "Uso: $(basename "$0") DIR" >&2
    exit 1
}

[[ $# -eq 1 ]] || usage

DIR="${1%/}"
[[ -n "$DIR" ]] || DIR="/"

if [[ ! -d "$DIR" ]]; then
    echo "Error: '$DIR' no es un directorio" >&2
    exit 1
fi

movidos=0
errores=0

while IFS= read -r -d '' archivo; do
    mes=$(date -r "$archivo" +%Y-%m) || { echo "Error: no se pudo leer la fecha de '$archivo'" >&2; errores=$((errores + 1)); continue; }
    destino="$DIR/$mes"

    if ! mkdir -p -- "$destino"; then
        echo "Error: no se pudo crear '$destino'" >&2
        errores=$((errores + 1))
        continue
    fi

    nombre=$(basename -- "$archivo")
    if [[ -e "$destino/$nombre" ]]; then
        echo "Aviso: '$destino/$nombre' ya existe, se omite '$archivo'" >&2
        errores=$((errores + 1))
        continue
    fi

    if mv -n -- "$archivo" "$destino/"; then
        echo "Movido: $archivo -> $destino/"
        movidos=$((movidos + 1))
    else
        echo "Error: no se pudo mover '$archivo'" >&2
        errores=$((errores + 1))
    fi
done < <(find "$DIR" -mindepth 1 -maxdepth 1 -type f -name '*.log' -print0)

echo "Total movidos: $movidos, errores/omitidos: $errores"
[[ $errores -eq 0 ]]
