#!/bin/sh
# Corre DENTRO del nodo k8s-a-control-plane. Durante un rollout, cuenta cada ~0,25 s los pods de una
# etiqueta por versión de imagen y estado, y escribe cada CAMBIO con los ms desde que empezó.
#   v=viejos (imagen distinta de la nueva) · n=nuevos (imagen nueva) · L=listos · S=sin listo · T=terminando
# Termina cuando todos los pods son de la imagen nueva, listos, ninguno terminando y van <replicas>.
# Uso: sh cuenta.sh <ns> <selector> <imagen-nueva> <replicas> <segundos-maximo>
ns=$1; sel=$2; nueva=$3; rep=$4; max=$5
export KUBECONFIG=/etc/kubernetes/admin.conf
t0=$(date +%s%3N); prev=""; maxtot=0; minlis=999; fin=""
while :; do
  dt=$(( $(date +%s%3N) - t0 ))
  [ $dt -gt $((max * 1000)) ] && { fin="(se acabó el tiempo: ${max} s)"; break; }
  l=$(kubectl get pods -n "$ns" -l "$sel" -o jsonpath='{range .items[*]}{.spec.containers[0].image} {.status.containerStatuses[0].ready} {.metadata.deletionTimestamp}{"\n"}{end}' 2>/dev/null |
      awk -v nueva="$nueva" '
        NF==0 {next}
        { term = ($3 != ""); nu = ($1 == nueva); lis = ($2 == "true") }
        term {T++; next}
        nu && lis {nL++} nu && !lis {nS++} !nu && lis {vL++} !nu && !lis {vS++}
        END {printf "viejos %d listos + %d no · nuevos %d listos + %d no · terminando %d|%d|%d|%d\n", vL, vS, nL, nS, T, vL+vS+nL+nS+T, vL+nL, (vL+vS+T==0 && nS==0)}')
  linea=${l%%|*}; resto=${l#*|}; tot=${resto%%|*}; resto=${resto#*|}; lis=${resto%%|*}; listo=${resto#*|}
  [ "$tot" -gt "$maxtot" ] && maxtot=$tot
  [ "$lis" -lt "$minlis" ] && minlis=$lis
  if [ "$linea" != "$prev" ]; then printf '%6d ms  %s\n' "$dt" "$linea"; prev="$linea"; fi
  if [ "$listo" = "1" ] && [ "$lis" = "$rep" ] && [ $dt -gt 1500 ]; then fin="completo en ${dt} ms"; break; fi
  sleep 0.25
done
echo "RESUMEN: $fin · máximo de pods a la vez: $maxtot · mínimo de pods listos: $minlis"
