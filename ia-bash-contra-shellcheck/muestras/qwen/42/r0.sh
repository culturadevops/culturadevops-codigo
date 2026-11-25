#!/bin/bash

FILE=$1
SEGUNDOS=$2

for ((i=0; i<${SEGUNDOS}; i++)); do
  if [ -e "$FILE" ]; then
    exit 0
  fi
  sleep 1
done

exit 1
