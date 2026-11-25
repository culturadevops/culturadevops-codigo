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

find "$DIR" -type f -print0 | xargs -0 -n1 -I{} stat -c '%F %n' {} | awk -F/ '{print $NF}' | awk -F. '{print $NF}' | sort | uniq -c | sort -nr | while IFS= read -r count ext; do
    echo "$ext $count"
done
