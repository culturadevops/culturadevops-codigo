#!/usr/bin/env bash
set -euo pipefail

usage() {
    echo "Uso: $(basename "$0") DIR" >&2
    exit 2
}

[[ $# -eq 1 ]] || usage

dir=$1

if [[ ! -d $dir ]]; then
    echo "Error: '$dir' no es un directorio" >&2
    exit 1
fi

if [[ ! -w $dir ]]; then
    echo "Error: no hay permiso de escritura en '$dir'" >&2
    exit 1
fi

cd -- "$dir"

tmp=$(mktemp ".SHA256SUMS.tmp.XXXXXX")
trap 'rm -f -- "$tmp"' EXIT

find . -mindepth 1 -maxdepth 1 -type f \
    ! -name 'SHA256SUMS' \
    ! -name '.SHA256SUMS.tmp.*' \
    -printf '%P\0' \
    | LC_ALL=C sort -z \
    | xargs -0 -r sha256sum -- > "$tmp"

chmod 644 -- "$tmp"
mv -f -- "$tmp" SHA256SUMS
trap - EXIT

echo "Generado: $(pwd)/SHA256SUMS ($(grep -c '' SHA256SUMS) archivos)"
