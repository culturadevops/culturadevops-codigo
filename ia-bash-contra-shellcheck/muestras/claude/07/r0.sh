#!/usr/bin/env bash
# Comprime con gzip cada archivo .log de DIR (sin subcarpetas) que no esté comprimido.
# Uso: script.sh DIR

set -u

usage() {
    echo "Uso: $(basename "$0") DIR" >&2
    exit 2
}

[ "$#" -eq 1 ] || usage

dir=$1

if [ ! -d "$dir" ]; then
    echo "Error: '$dir' no es un directorio" >&2
    exit 1
fi

if [ ! -r "$dir" ] || [ ! -w "$dir" ] || [ ! -x "$dir" ]; then
    echo "Error: permisos insuficientes en '$dir'" >&2
    exit 1
fi

shopt -s nullglob dotglob

comprimidos=0
omitidos=0
errores=0

for f in "$dir"/*.log; do
    # Solo archivos regulares, no enlaces simbólicos
    if [ -L "$f" ] || [ ! -f "$f" ]; then
        continue
    fi

    # Omitir si ya existe la versión comprimida
    if [ -e "$f.gz" ]; then
        echo "Omitido (ya existe $f.gz): $f"
        omitidos=$((omitidos + 1))
        continue
    fi

    # Omitir si el contenido ya está en formato gzip (magic bytes 1f 8b)
    magic=$(head -c 2 -- "$f" 2>/dev/null | od -An -tx1 | tr -d ' \n')
    if [ "$magic" = "1f8b" ]; then
        echo "Omitido (contenido ya comprimido): $f"
        omitidos=$((omitidos + 1))
        continue
    fi

    if gzip -- "$f"; then
        echo "Comprimido: $f -> $f.gz"
        comprimidos=$((comprimidos + 1))
    else
        echo "Error al comprimir: $f" >&2
        errores=$((errores + 1))
    fi
done

echo "Resumen: $comprimidos comprimidos, $omitidos omitidos, $errores errores"

[ "$errores" -eq 0 ] || exit 1
exit 0
