#!/usr/bin/env bash
# Uso: script.sh DIR
# Cuenta los archivos de cada extensión en DIR (recursivo) e imprime "EXT N",
# de mayor a menor. Los archivos sin extensión se agrupan como "(sin_extension)".

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Uso: $(basename "$0") DIR" >&2
    exit 1
fi

dir=$1

if [[ ! -d "$dir" ]]; then
    echo "Error: '$dir' no es un directorio" >&2
    exit 1
fi

if [[ ! -r "$dir" || ! -x "$dir" ]]; then
    echo "Error: sin permisos para leer '$dir'" >&2
    exit 1
fi

declare -A count=()

while IFS= read -r -d '' path; do
    name=${path##*/}
    # Quitar los puntos iniciales (archivos ocultos como .bashrc no tienen extensión)
    stripped=${name#"${name%%[!.]*}"}
    if [[ "$stripped" == *.* && -n "${stripped##*.}" ]]; then
        ext=${stripped##*.}
    else
        ext="(sin_extension)"
    fi
    count["$ext"]=$(( ${count["$ext"]:-0} + 1 ))
done < <(find "$dir" -type f -print0 2>/dev/null)

if [[ ${#count[@]} -eq 0 ]]; then
    exit 0
fi

for ext in "${!count[@]}"; do
    printf '%s\t%d\n' "$ext" "${count[$ext]}"
done | LC_ALL=C sort -t $'\t' -k2,2nr -k1,1 | awk -F '\t' '{ print $1, $2 }'
