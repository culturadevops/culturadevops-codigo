#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Uso: $0 DIR" >&2
    exit 1
fi

dir="$1"

if [[ ! -d "$dir" ]]; then
    echo "Error: '$dir' no es un directorio" >&2
    exit 1
fi

find "$dir" -mindepth 1 -maxdepth 1 -type d -print0 \
    | xargs -0 -r du -sh -- 2>/dev/null \
    | sort -rh
