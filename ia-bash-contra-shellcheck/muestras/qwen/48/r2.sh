#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Uso: $0 DIR"
    exit 1
fi

DIR=$1

find "$DIR" -type f -name "*.csv" | while read -r file; do
    if [ -f "$file" ]; then
        lines=$(sed -n 1p "$file" | grep -o "," | wc -l)
        total_lines=$(wc -l < "$file")
        echo "${file##*/}: $(($total_lines - $lines - 1)) filas"
    fi
done
