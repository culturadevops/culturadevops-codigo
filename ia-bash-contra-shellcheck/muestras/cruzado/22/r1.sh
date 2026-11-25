#!/bin/bash

# Comprueba si se ha proporcionado al menos un comando
if [ -z "$1" ]; then
  echo "Usage: $0 COMANDO [ARGUMENTOS...]"
  exit 1
fi

comando="$1"
shift

for ((i=1; i<=3; i++)); do
  echo "Intento $i: $comando $*"
  $comando "$@" && break
  sleep 1
done

exit $?
