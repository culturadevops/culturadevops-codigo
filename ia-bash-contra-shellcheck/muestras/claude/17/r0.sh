#!/usr/bin/env bash
# Copia a DEST los archivos de DIR que no existan en DEST o que sean más nuevos.
# Uso: script.sh DIR DEST
set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "Uso: $0 DIR DEST" >&2
    exit 1
fi

src=$1
dest=$2

if [[ ! -d "$src" ]]; then
    echo "Error: '$src' no es un directorio" >&2
    exit 1
fi

mkdir -p -- "$dest"

# Rutas absolutas para evitar problemas con rutas relativas
src=$(cd -- "$src" && pwd -P)
dest=$(cd -- "$dest" && pwd -P)

# Evitar copiar un directorio dentro de sí mismo
case "$dest/" in
    "$src/"*)
        echo "Error: DEST no puede estar dentro de DIR" >&2
        exit 1
        ;;
esac

copiados=0
errores=0

# Crear la estructura de directorios (incluidos los vacíos)
while IFS= read -r -d '' d; do
    rel=${d#"$src"}
    rel=${rel#/}
    [[ -z "$rel" ]] && continue
    mkdir -p -- "$dest/$rel" || errores=$((errores + 1))
done < <(find "$src" -type d -print0)

# Copiar archivos nuevos o más recientes
while IFS= read -r -d '' f; do
    rel=${f#"$src"/}
    target="$dest/$rel"

    if [[ ! -e "$target" && ! -L "$target" ]] || [[ "$f" -nt "$target" ]]; then
        mkdir -p -- "$(dirname -- "$target")"
        if cp -a -- "$f" "$target"; then
            echo "Copiado: $rel"
            copiados=$((copiados + 1))
        else
            echo "Error al copiar: $rel" >&2
            errores=$((errores + 1))
        fi
    fi
done < <(find "$src" \( -type f -o -type l \) -print0)

echo "Archivos copiados: $copiados"
if [[ $errores -gt 0 ]]; then
    echo "Errores: $errores" >&2
    exit 1
fi
exit 0
