#!/bin/sh
# crono.sh <etiqueta> <orden...> — cinco pasadas, en milisegundos. Una sola pasada no es un dato.
et="$1"; shift
printf "  %-26s" "$et"; total=0
for i in 1 2 3 4 5; do
  ini=$(date +%s%N); "$@" >/dev/null 2>&1; fin=$(date +%s%N)
  ms=$(( (fin - ini) / 1000000 )); printf " %6s" "$ms"; total=$(( total + ms ))
done
printf "   media %s ms\n" "$(( total / 5 ))"
