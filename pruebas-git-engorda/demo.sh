#!/usr/bin/env bash
# demo.sh — la medición del vídeo 225 «Por qué tu repo de Git engorda».
#
# Todo en un contenedor con git oficial, desde un repositorio vacío. Lo que se demuestra:
#
#   1. un repo normal pesa nada
#   2. metes un binario grande y el repo crece
#   3. LO BORRAS y haces más commits... y el repo NO baja
#   4. `git gc` empaqueta: aquí sale el número que sorprende
#   5. qué es lo que ocupa de verdad, y cómo se pregunta
#   6. quitarlo de verdad, y el precio que tiene
set -u
cd /tmp && rm -rf repo && mkdir repo && cd repo
git init -q . && git config user.email a@b.c && git config user.name Prueba

peso() { du -sh .git 2>/dev/null | cut -f1; }
sueltos() { git count-objects -vH | grep -E '^(count|size|in-pack|size-pack):' | tr '\n' ' '; }

echo "== 1 · UN REPOSITORIO NORMAL, SOLO CÓDIGO =="
for i in $(seq 1 40); do
  printf 'package main\n// linea %d\nfunc main() {}\n' "$i" > "f$i.go"
done
git add -A && git commit -qm "el codigo del proyecto"
echo "   .git pesa: $(peso)"
echo "   $(sueltos)"

echo
echo "== 2 · ALGUIEN SUBE UN BINARIO DE 20 MB (una vez, hace tres años) =="
head -c 20000000 /dev/urandom > gordo.bin
git add -A && git commit -qm "subo el instalador, luego lo quito"
echo "   .git pesa: $(peso)"

echo
echo "== 3 · 🥇 LO BORRA, Y HACE 20 COMMITS MÁS =="
git rm -q gordo.bin && git commit -qm "quito el instalador, que no iba aqui"
for i in $(seq 1 20); do
  echo "// cambio $i" >> f1.go && git commit -qam "trabajo normal $i"
done
echo "   el fichero ya NO esta en el proyecto:"
ls gordo.bin 2>/dev/null || echo "     (no existe, borrado hace 20 commits)"
echo "   y sin embargo .git pesa: $(peso)"
echo "   ^ borrar un fichero no lo quita del repositorio. Git guarda HISTORIA,"
echo "     no la foto de hoy. Ese objeto sigue ahi para poder volver atras."

echo
echo "== 4 · 🥇 Y AHORA git gc, QUE ES DONDE SALTA LA SORPRESA =="
echo "   antes: $(sueltos)"
git gc -q --aggressive 2>/dev/null
echo "   despues: $(sueltos)"
echo "   .git pesa ahora: $(peso)"
echo "   ^ los objetos sueltos se juntan en un paquete y se comprimen unos contra otros."
echo "     Y el binario aleatorio NO se comprime: por eso sigue ahi entero."

echo
echo "== 5 · ¿QUÉ ES LO QUE OCUPA? La pregunta que casi nadie sabe hacer =="
PACK=$(ls .git/objects/pack/*.idx 2>/dev/null | head -1)
echo "   git verify-pack -v \$PACK | sort -k3 -n -r | head"
git verify-pack -v "$PACK" 2>/dev/null | grep -E '^[0-9a-f]{40}' \
  | sort -k3 -n -r | head -3 | awk '{printf "     %s  tipo=%-6s %10d bytes\n", substr($1,1,12), $2, $3}'
echo "   ^ el objeto mas gordo, con su tamano. Ahora ya sabes A QUE le echas la culpa."
echo -n "   y a qué fichero corresponde: "
GORDO=$(git verify-pack -v "$PACK" 2>/dev/null | grep -E '^[0-9a-f]{40}' | sort -k3 -n -r | head -1 | cut -d' ' -f1)
git rev-list --objects --all 2>/dev/null | grep "^$GORDO" | cut -d' ' -f2

echo
echo "== 6 · QUITARLO DE VERDAD, Y LO QUE CUESTA =="
ANTES=$(git rev-parse HEAD)
echo "   el commit actual es: ${ANTES:0:12}"
git filter-branch -f --index-filter 'git rm --cached --ignore-unmatch gordo.bin' \
  --prune-empty HEAD >/dev/null 2>&1
rm -rf .git/refs/original && git reflog expire --expire=now --all >/dev/null 2>&1
git gc -q --prune=now --aggressive 2>/dev/null
echo "   .git pesa ahora: $(peso)"
DESPUES=$(git rev-parse HEAD)
echo "   y el commit actual es: ${DESPUES:0:12}"
if [ "$ANTES" != "$DESPUES" ]; then
  echo "   ⛔ HA CAMBIADO. Y con el, TODOS los commits desde el que se toco."
  echo "      Eso rompe la copia de todo el que tenga el repositorio clonado."
fi
