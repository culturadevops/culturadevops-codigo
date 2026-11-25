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

cd "$DIR" || exit

find . -maxdepth 1 -type f -exec sha256sum {} \; > SHA256SUMS
