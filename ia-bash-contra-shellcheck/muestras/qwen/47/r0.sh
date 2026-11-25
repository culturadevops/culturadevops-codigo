#!/bin/bash

FILE=$1

if [ ! -f "$FILE" ]; then
  echo "El archivo $FILE no existe."
  exit 1
fi

tail -n +1 "$FILE" | grep -m 1 -i 'error' | tail -n 1
