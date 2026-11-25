#!/usr/bin/env bash
#
# Uso: script.sh LOGFILE COMANDO [ARGUMENTOS...]
# Ejecuta COMANDO con sus argumentos y añade su salida (stdout y stderr)
# a LOGFILE, con cada línea precedida de [AAAA-MM-DD HH:MM:SS].
# El script termina con el mismo código de salida que COMANDO.

set -u
set -o pipefail

usage() {
    printf 'Uso: %s LOGFILE COMANDO [ARGUMENTOS...]\n' "${0##*/}" >&2
    exit 2
}

[[ $# -ge 2 ]] || usage

logfile=$1
shift

if [[ -z "$logfile" ]]; then
    printf 'Error: LOGFILE no puede estar vacío\n' >&2
    exit 2
fi

logdir=$(dirname -- "$logfile")
if [[ ! -d "$logdir" ]]; then
    printf 'Error: el directorio "%s" no existe\n' "$logdir" >&2
    exit 2
fi

if ! { : >> "$logfile"; } 2>/dev/null; then
    printf 'Error: no se puede escribir en "%s"\n' "$logfile" >&2
    exit 2
fi

if ! command -v -- "$1" >/dev/null 2>&1; then
    printf '[%(%Y-%m-%d %H:%M:%S)T] Error: comando no encontrado: %s\n' -1 "$1" >> "$logfile"
    printf 'Error: comando no encontrado: %s\n' "$1" >&2
    exit 127
fi

timestamp_lines() {
    local line
    while IFS= read -r line || [[ -n "$line" ]]; do
        printf '[%(%Y-%m-%d %H:%M:%S)T] %s\n' -1 "$line"
    done
}

"$@" 2>&1 | timestamp_lines >> "$logfile"
status=("${PIPESTATUS[@]}")

if [[ ${status[1]} -ne 0 ]]; then
    printf 'Error: fallo al escribir en "%s"\n' "$logfile" >&2
fi

exit "${status[0]}"
