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

find "$DIR" -type l ! -exec test -e {} \; -exec rm -- {} +
