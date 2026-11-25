#!/bin/bash

DIR=$1

if [ -z "$DIR" ]; then
  echo "Debes proporcionar un directorio como argumento."
  exit 1
fi

if [ ! -d "$DIR" ]; then
  echo "$DIR no es un directorio válido."
  exit 1
fi

count=0
find "$DIR" -type f \( -name "*.tmp" -o -name "*.bak" \) -exec rm {} \; && count=$(find "$DIR" -type f \( -name "*.tmp" -o -name "*.bak" \) | wc -l)

echo "Se borraron $count archivos .tmp o .bak."
