#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Uso: $0 DIR"
    exit 1
fi

DIR=$1

if [ ! -d "$DIR" ]; then
    echo "Error: $DIR no es un directorio válido"
    exit 1
fi

find "$DIR" -type f -print0 | xargs -0 du -b | sort -nr | awk -F '\t' '{print $2, $1}' | head -n 3
