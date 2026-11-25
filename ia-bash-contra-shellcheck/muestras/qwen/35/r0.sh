#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Uso: $0 FILE"
    exit 1
fi

FILE=$1

while IFS= read -r user; do
    echo "useradd $user"
done < "$FILE"
