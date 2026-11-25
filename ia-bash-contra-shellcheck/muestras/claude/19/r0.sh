#!/usr/bin/env bash
#
# Busca archivos duplicados (mismo contenido) dentro de DIR y sus subcarpetas
# e imprime cada grupo de rutas duplicadas, separados por una línea en blanco.
#
# Uso: script.sh DIR

set -euo pipefail

usage() {
    echo "Uso: $(basename "$0") DIR" >&2
    exit 2
}

[[ $# -eq 1 ]] || usage

dir=$1

if [[ ! -d "$dir" ]]; then
    echo "Error: '$dir' no es un directorio" >&2
    exit 1
fi

if [[ ! -r "$dir" || ! -x "$dir" ]]; then
    echo "Error: no se puede leer el directorio '$dir'" >&2
    exit 1
fi

declare -a paths=()        # índice -> ruta
declare -A size_idx=()     # tamaño -> lista de índices
declare -A size_count=()   # tamaño -> número de archivos
declare -A hash_idx=()     # hash -> lista de índices
declare -A hash_count=()   # hash -> número de archivos

# 1) Agrupar por tamaño (barato): solo archivos regulares, sin seguir enlaces.
i=0
while IFS= read -r -d '' entry; do
    size=${entry%%/*}
    path=${entry#*/}
    paths[i]=$path
    size_idx[$size]+="$i "
    size_count[$size]=$(( ${size_count[$size]:-0} + 1 ))
    i=$((i + 1))
done < <(find "$dir" -type f -printf '%s/%p\0' 2>/dev/null)

# 2) Para tamaños con más de un archivo, calcular el hash del contenido.
for size in "${!size_count[@]}"; do
    (( size_count[$size] > 1 )) || continue
    for idx in ${size_idx[$size]}; do
        f=${paths[idx]}
        if ! out=$(sha256sum -- "$f" 2>/dev/null); then
            echo "Aviso: no se pudo leer '$f'" >&2
            continue
        fi
        h=${out%% *}
        h=${h#\\}   # sha256sum antepone '\' si el nombre tiene caracteres escapados
        key="$size:$h"
        hash_idx[$key]+="$idx "
        hash_count[$key]=$(( ${hash_count[$key]:-0} + 1 ))
    done
done

# 3) Imprimir los grupos con más de un archivo.
groups=0
while IFS= read -r key; do
    [[ -n "$key" ]] || continue
    (( hash_count[$key] > 1 )) || continue
    groups=$((groups + 1))
    size=${key%%:*}
    (( groups > 1 )) && echo
    echo "Grupo $groups (${hash_count[$key]} archivos, $size bytes):"
    for idx in ${hash_idx[$key]}; do
        printf '  %s\n' "${paths[idx]}"
    done
done < <(printf '%s\n' "${!hash_count[@]}" | sort -t: -k1,1nr -k2,2)

if (( groups == 0 )); then
    echo "No se encontraron archivos duplicados en '$dir'."
fi

exit 0
