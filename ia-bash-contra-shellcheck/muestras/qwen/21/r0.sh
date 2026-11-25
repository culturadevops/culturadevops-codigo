#!/bin/bash

LOGFILE=$1
COMMAND=$2
shift 2

if [ -z "$LOGFILE" ] || [ -z "$COMMAND" ]; then
    echo "Uso: script.sh LOGFILE COMANDO [ARGUMENTOS...]"
    exit 1
fi

exec > >(tee -a "$LOGFILE") 2>&1
exec 3>&1

$COMMAND "$@"

exec 1>&3
date +"[%Y-%m-%d %H:%M:%S]" | tee -a "$LOGFILE"
