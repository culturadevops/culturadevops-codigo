#!/bin/bash

FILE=$1

while IFS= read -r line; do
    if [ ! -e "$line" ]; then
        echo "FALTA: $line"
    fi
done < "$FILE"

if grep -q "FALTA:" "$FILE"; then
    exit 1
fi
