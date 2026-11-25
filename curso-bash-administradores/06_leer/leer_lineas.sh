#!/usr/bin/env bash
# Leccion 6 — Leer un archivo linea a linea: for in $(cat ...) no lo hace.
cd "$(mktemp -d)" || exit 1

cat > servidores.txt <<'FIN'
web-01   produccion   Servidor de la tienda
web-02   produccion
db-01    datos        Base de datos principal

cache-01 produccion
FIN

echo "== 6.1 · El archivo =="
cat -A servidores.txt | sed 's/\$$/ <- fin de linea/' | sed 's/^/  /'

echo
echo "== 6.2 · LA TRAMPA: for linea in \$(cat archivo) =="
n=0
for linea in $(cat servidores.txt); do n=$((n + 1)); done
echo "  vueltas del bucle: $n   <- el archivo tiene 5 lineas"
echo "  bash partio por ESPACIOS, no por lineas. Cada palabra es una vuelta."

echo
echo "== 6.3 · while IFS= read -r =="
n=0
while IFS= read -r linea; do
  n=$((n + 1))
  echo "  $n: <$linea>"
done < servidores.txt
echo "  vueltas: $n"
echo "  IFS= evita que se coman los espacios · -r que las barras se interpreten"

echo
echo "== 6.4 · La ultima linea sin salto: el que se pierde =="
printf 'web-01\nweb-02\nweb-03' > sin_salto.txt      # sin \n al final
n=0; while IFS= read -r l; do n=$((n + 1)); done < sin_salto.txt
echo "  con 'while read': $n de 3   <- read devuelve falso en la ultima"
n=0; while IFS= read -r l || [[ -n $l ]]; do n=$((n + 1)); done < sin_salto.txt
echo "  con '|| [[ -n \$l ]]': $n de 3"

echo
echo "== 6.5 · LA TRAMPA 2: la tuberia se lleva las variables =="
total=0
cat servidores.txt | while IFS= read -r l; do total=$((total + 1)); done
echo "  despues de 'cat ... | while ...':  total=$total   <- se quedo en 0"
echo "  La tuberia crea un SUBSHELL: lo que cambies ahi dentro no sale."
total=0
while IFS= read -r l; do total=$((total + 1)); done < servidores.txt
echo "  redirigiendo con < :                total=$total"
total=0
while IFS= read -r l; do total=$((total + 1)); done < <(grep -c . servidores.txt > /dev/null; cat servidores.txt)
echo "  o con sustitucion de proceso < <(...): total=$total"

echo
echo "== 6.6 · Partir cada linea en campos, sin cortar =="
while IFS=$' \t' read -r nombre entorno resto; do
  [[ -z $nombre ]] && continue
  printf '  %-10s %-12s %s\n' "$nombre" "$entorno" "${resto:-(sin descripcion)}"
done < servidores.txt
echo "  El ultimo campo del read se queda con TODO lo que sobra: por eso la descripcion"
echo "  con espacios no se parte."
