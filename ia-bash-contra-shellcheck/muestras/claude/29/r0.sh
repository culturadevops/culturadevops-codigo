#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Uso: $0 DIR" >&2
    exit 1
fi

dir=$1

if [[ ! -d "$dir" ]]; then
    echo "Error: '$dir' no es un directorio" >&2
    exit 1
fi

find "$dir" -type f -mmin -1440 -print
