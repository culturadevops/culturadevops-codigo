#!/bin/bash

DIR=$1
LIMITE=$2

if [ -d "$DIR" ]; then
    TAMAÑO=$(du -sk "$DIR" | cut -f1)
    if [ "$TAMAÑO" -gt "$LIMITE" ]; then
        echo "$TAMAÑO"
        exit 2
    else
        echo "$TAMAÑO"
    fi
else
    echo "El directorio especificado no existe."
    exit 1
fi
