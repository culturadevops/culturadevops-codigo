#!/bin/bash

if [ -z "$1" ]; then
    echo "Debes proporcionar el directorio como argumento."
    exit 1
fi

DIR=$1

if [ ! -d "$DIR" ]; then
    echo "El directorio especificado no existe."
    exit 1
fi

total_lines=$(find "$DIR" -type f -name "*.log" -exec grep -c ERROR {} \; | awk '{sum += $1} END {print sum}')

echo "$total_lines"
