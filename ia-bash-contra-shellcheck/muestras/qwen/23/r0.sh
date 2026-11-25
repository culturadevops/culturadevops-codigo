#!/bin/bash

LOCKFILE=$1
LOGFILE=$2

if ! exec 9>! "$LOCKFILE"; then
  echo "No se pudo adquirir el bloqueo" >&2
  exit 1
fi

if ! flock -x 9; then
  echo "No se pudo adquirir el bloqueo" >&2
  exit 1
fi

echo "trabajando" > "$LOGFILE"

exec 9>&-
