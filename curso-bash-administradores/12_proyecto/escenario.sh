#!/usr/bin/env bash
# Leccion 12 — respaldo.sh contra seis situaciones, incluidas las que fallan.
set -uo pipefail
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="$(mktemp -d)"
cd "$BASE" || exit 1

mkdir -p "datos de la tienda"/{pedidos,clientes}      # con espacios, a proposito
for i in 1 2 3; do
  printf 'pedido %s\n' "$i" > "datos de la tienda/pedidos/pedido-$i.json"
done
printf 'nombre;correo\n' > "datos de la tienda/clientes/clientes.csv"
mkdir copias

paso() {
  echo
  echo "== $1 =="
  shift
  echo "  \$ respaldo.sh $*"
  bash "$AQUI/respaldo.sh" "$@" 2>&1 | sed 's/^/  /'
  echo "  [codigo ${PIPESTATUS[0]}]"
}

paso "1 · Sin opciones: te dice TODO lo que falta"
paso "2 · Con un --conservar que no es un numero" --origen "$BASE/datos de la tienda" --destino "$BASE/copias" --conservar tres
paso "3 · Simulacro" --origen "$BASE/datos de la tienda" --destino "$BASE/copias" --dry-run
echo "  copias creadas por el simulacro: $(ls -1 copias/respaldo-*.tar.gz 2>/dev/null | wc -l)"

paso "4 · La copia de verdad (el origen lleva espacios en el nombre)" --origen "$BASE/datos de la tienda" --destino "$BASE/copias"

echo
echo "== 5 · Cuatro copias mas, conservando 3 =="
for i in 1 2 3 4; do
  sleep 1
  bash "$AQUI/respaldo.sh" --origen "$BASE/datos de la tienda" --destino "$BASE/copias" --conservar 3 2>&1 |
    grep -E "hecha|rotacion|quedan" | sed 's/^/    /'
done
echo "  en la carpeta: $(ls -1 copias/respaldo-*.tar.gz | wc -l) copias"

echo
echo "== 6 · Con otra copia en curso (el cerrojo esta puesto) =="
mkdir -p copias/.respaldo.lock
bash "$AQUI/respaldo.sh" --origen "$BASE/datos de la tienda" --destino "$BASE/copias" 2>&1 | sed 's/^/  /'
echo "  [codigo ${PIPESTATUS[0]}]"
rmdir copias/.respaldo.lock

echo
echo "== 7 · Si el origen no existe (el cron apuntaba a la carpeta vieja) =="
bash "$AQUI/respaldo.sh" --origen "$BASE/no-existe" --destino "$BASE/copias" 2>&1 | sed 's/^/  /'
echo "  [codigo ${PIPESTATUS[0]}]"
echo "  temporales y cerrojos que han quedado: $(ls -a copias | grep -c '^\.\(trabajo\|respaldo\)' || true)"

cd /
rm -rf "$BASE"
