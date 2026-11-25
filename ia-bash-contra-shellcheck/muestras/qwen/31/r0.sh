#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Uso: $0 DIR"
    exit 1
fi

DIR=$1

if [ ! -d "$DIR" ]; then
    echo "El directorio especificado no existe."
    exit 1
fi

find "$DIR" -mindepth 1 -maxdepth 1 -type d -exec du -h {} + | sort -rh | awk '{print $1, $2}'
