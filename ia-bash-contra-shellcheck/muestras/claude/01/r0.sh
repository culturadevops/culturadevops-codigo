#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
    echo "Uso: $0 DIR DEST" >&2
    exit 1
fi

DIR=$1
DEST=$2

if [ ! -d "$DIR" ]; then
    echo "Error: '$DIR' no es un directorio" >&2
    exit 1
fi

if ! mkdir -p -- "$DEST"; then
    echo "Error: no se pudo crear '$DEST'" >&2
    exit 1
fi

find "$DIR" -mindepth 1 -maxdepth 1 -type f -name '*.log' -exec cp -p -- {} "$DEST"/ \;
