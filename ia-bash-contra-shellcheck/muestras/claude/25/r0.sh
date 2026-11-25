#!/usr/bin/env bash
# Uso: script.sh FILE CLAVE
# Imprime el valor de CLAVE en un archivo de configuración con líneas CLAVE=valor.
set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "Uso: $(basename "$0") FILE CLAVE" >&2
    exit 2
fi

file=$1
key=$2

if [[ ! -f $file || ! -r $file ]]; then
    echo "Error: no se puede leer el archivo '$file'" >&2
    exit 2
fi

if [[ -z $key ]]; then
    echo "Error: la clave no puede estar vacía" >&2
    exit 2
fi

found=0
value=""

while IFS= read -r line || [[ -n $line ]]; do
    line=${line%$'\r'}
    # Quitar espacios iniciales
    trimmed=${line#"${line%%[![:space:]]*}"}
    # Ignorar líneas vacías y comentarios
    [[ -z $trimmed || $trimmed == \#* ]] && continue
    [[ $trimmed == *=* ]] || continue

    k=${trimmed%%=*}
    v=${trimmed#*=}
    # Quitar espacios finales de la clave y espacios iniciales/finales del valor
    k=${k%"${k##*[![:space:]]}"}
    v=${v#"${v%%[![:space:]]*}"}
    v=${v%"${v##*[![:space:]]}"}

    if [[ $k == "$key" ]]; then
        # Quitar comillas envolventes si las hay
        if [[ ${#v} -ge 2 && ( ( $v == \"*\" ) || ( $v == \'*\' ) ) ]]; then
            v=${v:1:${#v}-2}
        fi
        value=$v
        found=1
        # La última aparición prevalece
    fi
done < "$file"

if [[ $found -eq 1 ]]; then
    printf '%s\n' "$value"
    exit 0
else
    echo "Error: clave '$key' no encontrada en '$file'" >&2
    exit 1
fi
