#!/bin/sh
# Cronometra init, plan, apply y destroy. CINCO pasadas cada uno.
#
# ⚠️ Cinco y no una. En la serie «¿la alternativa a X?» la primera medición mintió tres veces
# seguidas: siempre era un arranque en frío. Una sola pasada no es un dato.
#
# ⚠️ `plan` se mide DOS veces distintas y no es lo mismo:
#     · plan sin cambios  -> lo que haces cien veces al día
#     · plan con cambios  -> tiene que consultar el estado real de lo que existe
#
# ⛔ El `destroy` del final deja la máquina como estaba: este laboratorio no se queda encendido.
export MSYS_NO_PATHCONV=1
cd "$(dirname "$0")/01-primer-recurso"

crono() {   # $1 = etiqueta, resto = orden
  et="$1"; shift
  printf "  %-22s" "$et"
  total=0
  for i in 1 2 3 4 5; do
    ini=$(date +%s%N)
    "$@" >/dev/null 2>&1
    fin=$(date +%s%N)
    ms=$(( (fin - ini) / 1000000 ))
    printf " %6s" "$ms"
    total=$(( total + ms ))
  done
  printf "   media %s ms\n" "$(( total / 5 ))"
}

echo "== con la infraestructura YA creada =="
crono "plan (sin cambios)"  tofu plan
crono "apply (sin cambios)" tofu apply -auto-approve

echo
echo "== el ciclo completo, una vez por pasada =="
printf "  %-22s" "destroy + apply"
total=0
for i in 1 2 3 4 5; do
  tofu destroy -auto-approve >/dev/null 2>&1
  ini=$(date +%s%N)
  tofu apply -auto-approve >/dev/null 2>&1
  fin=$(date +%s%N)
  ms=$(( (fin - ini) / 1000000 ))
  printf " %6s" "$ms"
  total=$(( total + ms ))
done
printf "   media %s ms  (solo el apply)\n" "$(( total / 5 ))"
