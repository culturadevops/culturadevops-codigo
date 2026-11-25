#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Uso: $0 FILE" >&2
    exit 1
fi

file=$1

if [[ ! -f $file || ! -r $file ]]; then
    echo "Error: no se puede leer el archivo '$file'" >&2
    exit 1
fi

awk -F',' '
    NR == 1 { next }
    {
        sub(/\r$/, "")
        if ($0 ~ /^[[:space:]]*$/) next
        email = $NF
        gsub(/^[[:space:]"]+|[[:space:]"]+$/, "", email)
        if (email != "") print email
    }
' "$file"
