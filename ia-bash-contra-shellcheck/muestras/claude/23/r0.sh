#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
    echo "Uso: $0 LOCKFILE LOGFILE" >&2
    exit 2
fi

LOCKFILE="$1"
LOGFILE="$2"

exec 9>>"$LOCKFILE" || {
    echo "Error: no se puede abrir el archivo de bloqueo '$LOCKFILE'" >&2
    exit 1
}

if ! flock -n 9; then
    echo "Otra instancia ya se está ejecutando (bloqueo: $LOCKFILE)" >&2
    exit 1
fi

echo 'trabajando' >> "$LOGFILE"
