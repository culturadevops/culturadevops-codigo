#!/bin/bash

FILE=$1

while IFS= read -r service; do
  if pgrep -x "$service" > /dev/null; then
    echo "$service: activo"
  else
    echo "$service: caído"
    exit 1
  fi
done < "$FILE"
