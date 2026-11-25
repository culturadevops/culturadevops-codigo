#!/usr/bin/env bash
# Organiza los archivos regulares de DIR en subcarpetas según su extensión (en minúsculas).
# Uso: script.sh DIR

set -euo pipefail

usage() {
    echo "Uso: $(basename "$0") DIR" >&2
    exit 1
}

[[ $# -eq 1 ]] || usage

dir=$1

if [[ ! -d $dir ]]; then
    echo "Error: '$dir' no es un directorio." >&2
    exit 1
fi

if [[ ! -w $dir || ! -x $dir ]]; then
    echo "Error: sin permisos suficientes sobre '$dir'." >&2
    exit 1
fi

movidos=0
omitidos=0
errores=0

while IFS= read -r -d '' ruta; do
    nombre=${ruta##*/}

    # Sin punto, o archivo oculto sin otra extensión (p. ej. .bashrc): no tiene extensión
    base=${nombre#.}
    if [[ $base != *.* ]]; then
        echo "Omitido (sin extensión): $nombre"
        omitidos=$((omitidos + 1))
        continue
    fi

    ext=${nombre##*.}
    if [[ -z $ext ]]; then
        echo "Omitido (extensión vacía): $nombre"
        omitidos=$((omitidos + 1))
        continue
    fi

    ext=${ext,,}
    destino="$dir/$ext"

    if [[ -e $destino && ! -d $destino ]]; then
        echo "Error: '$destino' existe y no es un directorio; se omite '$nombre'." >&2
        errores=$((errores + 1))
        continue
    fi

    if ! mkdir -p -- "$destino"; then
        echo "Error: no se pudo crear '$destino'." >&2
        errores=$((errores + 1))
        continue
    fi

    if [[ -e $destino/$nombre ]]; then
        echo "Omitido (ya existe en destino): $ext/$nombre" >&2
        omitidos=$((omitidos + 1))
        continue
    fi

    if mv -n -- "$ruta" "$destino/"; then
        echo "Movido: $nombre -> $ext/"
        movidos=$((movidos + 1))
    else
        echo "Error: no se pudo mover '$nombre'." >&2
        errores=$((errores + 1))
    fi
done < <(find "$dir" -mindepth 1 -maxdepth 1 -type f -print0)

echo "Resumen: $movidos movidos, $omitidos omitidos, $errores errores."

[[ $errores -eq 0 ]]
