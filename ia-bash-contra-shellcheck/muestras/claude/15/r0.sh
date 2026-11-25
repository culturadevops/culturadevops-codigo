#!/usr/bin/env bash
# Añade la fecha de modificación (AAAA-MM-DD_) al principio de cada .txt de DIR.
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Uso: $(basename "$0") DIR" >&2
    exit 1
fi

dir=$1

if [[ ! -d "$dir" ]]; then
    echo "Error: '$dir' no es un directorio" >&2
    exit 1
fi

shopt -s nullglob dotglob

renombrados=0
omitidos=0
errores=0

for ruta in "$dir"/*.txt; do
    # Solo archivos regulares (no directorios ni enlaces simbólicos)
    [[ -f "$ruta" && ! -L "$ruta" ]] || continue

    nombre=$(basename -- "$ruta")

    # Evitar añadir el prefijo dos veces
    if [[ "$nombre" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}_ ]]; then
        echo "Omitido (ya tiene fecha): $nombre"
        omitidos=$((omitidos + 1))
        continue
    fi

    if ! fecha=$(date -r "$ruta" +%Y-%m-%d); then
        echo "Error: no se pudo obtener la fecha de '$nombre'" >&2
        errores=$((errores + 1))
        continue
    fi

    destino="$dir/${fecha}_${nombre}"

    if [[ -e "$destino" ]]; then
        echo "Omitido (el destino ya existe): ${fecha}_${nombre}" >&2
        omitidos=$((omitidos + 1))
        continue
    fi

    if mv -n -- "$ruta" "$destino"; then
        echo "$nombre -> ${fecha}_${nombre}"
        renombrados=$((renombrados + 1))
    else
        echo "Error: no se pudo renombrar '$nombre'" >&2
        errores=$((errores + 1))
    fi
done

echo "Renombrados: $renombrados | Omitidos: $omitidos | Errores: $errores"

[[ $errores -eq 0 ]]
