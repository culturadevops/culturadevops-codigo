#!/usr/bin/env bash
# Modo de prueba: muestra los comandos useradd que se ejecutarían para cada
# usuario listado en FILE, sin ejecutar nada.
set -euo pipefail

usage() {
    echo "Uso: $(basename "$0") FILE" >&2
    exit 1
}

[[ $# -eq 1 ]] || usage
file=$1

if [[ ! -f $file || ! -r $file ]]; then
    echo "Error: no se puede leer el archivo '$file'" >&2
    exit 1
fi

# Nombres válidos según la convención habitual de Debian (NAME_REGEX por defecto)
valid_re='^[a-z_][a-z0-9_-]*\$?$'

declare -A seen=()
line_no=0
count=0
errors=0

while IFS= read -r line || [[ -n $line ]]; do
    line_no=$((line_no + 1))

    # Quitar CR (archivos con fin de línea Windows) y espacios alrededor
    user=${line%$'\r'}
    user=${user#"${user%%[![:space:]]*}"}
    user=${user%"${user##*[![:space:]]}"}

    # Saltar líneas vacías y comentarios
    [[ -z $user || $user == \#* ]] && continue

    if (( ${#user} > 32 )); then
        echo "Aviso (línea $line_no): '$user' supera 32 caracteres, se omite" >&2
        errors=$((errors + 1))
        continue
    fi

    if [[ ! $user =~ $valid_re ]]; then
        echo "Aviso (línea $line_no): nombre de usuario no válido '$user', se omite" >&2
        errors=$((errors + 1))
        continue
    fi

    if [[ -n ${seen[$user]+x} ]]; then
        echo "Aviso (línea $line_no): '$user' duplicado, se omite" >&2
        continue
    fi
    seen[$user]=1

    if getent passwd "$user" >/dev/null 2>&1; then
        echo "# '$user' ya existe en el sistema; no se crearía"
        continue
    fi

    printf 'useradd -m -s /bin/bash %q\n' "$user"
    count=$((count + 1))
done < "$file"

echo "# Modo de prueba: $count comando(s) generado(s), no se ejecutó nada." >&2

(( errors == 0 )) || exit 2
