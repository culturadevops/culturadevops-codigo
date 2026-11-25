#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Uso: $0 DIR" >&2
    exit 1
fi

dir=$1

if [[ ! -d $dir ]]; then
    echo "Error: '$dir' no es un directorio" >&2
    exit 1
fi

shopt -s nullglob

for f in "$dir"/*.txt; do
    [[ -f $f ]] || continue
    n=$(awk 'END { print NR }' "$f")
    printf '%s: %s\n' "${f##*/}" "$n"
done
