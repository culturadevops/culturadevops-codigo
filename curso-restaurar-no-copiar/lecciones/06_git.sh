#!/usr/bin/env bash
# Lección 6 · El repositorio: lo que NO viaja en un clon.
#
# «El código está en git, no hace falta copia.» Se te muere el portátil, clonas, y faltan cosas.
# No da ningún error: clone funciona perfecto. Simplemente, lo que no estaba en el remoto no está.
source /curso/comun.sh
set -u
rm -rf /tmp/git && mkdir -p /tmp/git && cd /tmp/git
git init -q --bare origen.git
git clone -q origen.git trabajo 2>/dev/null && cd trabajo

# Un día normal de trabajo.
echo "app" > app.py && echo ".env" > .gitignore && git add . && git commit -qm "la app" && git push -q origin main
echo "DB_PASSWORD=la-de-produccion" > .env                                  # ignorado, a propósito
printf '#!/bin/sh\necho "revisando secretos..."\n' > .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
git switch -qc arreglo-urgente && echo "fix" >> app.py && git commit -qam "arreglo a medias" >/dev/null 2>&1
git switch -q main
echo "experimento" >> app.py && git stash -q
git tag v1.4-candidata

inventario() {
  local d=$1
  printf '  %-34s %s\n' "rama arreglo-urgente (sin subir)" "$(git -C "$d" rev-parse -q --verify arreglo-urgente >/dev/null && echo sí || echo NO)"
  # git stash list lee el REFLOG de refs/stash, y el reflog no viaja en ningún bundle ni clon.
  local stash=NO
  if git -C "$d" stash list | grep -q .; then stash=sí
  elif git -C "$d" rev-parse -q --verify refs/stash >/dev/null; then stash="solo el último (stash list sale vacío)"
  fi
  printf '  %-34s %s\n' "stash (el experimento)" "$stash"
  printf '  %-34s %s\n' "etiqueta v1.4-candidata" "$(git -C "$d" rev-parse -q --verify refs/tags/v1.4-candidata >/dev/null && echo sí || echo NO)"
  printf '  %-34s %s\n' ".env (ignorado por git)" "$( [ -f "$d/.env" ] && echo sí || echo NO)"
  printf '  %-34s %s\n' "hook pre-commit" "$( [ -x "$d/.git/hooks/pre-commit" ] && echo sí || echo NO)"
}

titulo "6.1 · El portátil de hoy"
inventario /tmp/git/trabajo

# Lo que se copia (6.3) se hace ANTES del desastre.
git bundle create -q /copias/trabajo.bundle --all
git ls-files --others --ignored --exclude-standard -z | tar --null -czf /copias/ignorados.tgz -T - .git/hooks
cd /tmp/git && rm -rf trabajo

titulo "6.2 · El portátil se muere. Lo normal: git clone"
git clone -q origen.git clonado 2>/dev/null
echo "  git clone: código de salida $?"
inventario /tmp/git/clonado

titulo "6.3 · Lo correcto: git bundle --all + los ficheros ignorados y los hooks"
echo "  copias: trabajo.bundle $(( $(bytes /copias/trabajo.bundle) )) bytes · ignorados.tgz $(bytes /copias/ignorados.tgz) bytes"
git clone -q /copias/trabajo.bundle desde-copia 2>/dev/null
cd desde-copia
git fetch -q --update-head-ok /copias/trabajo.bundle 'refs/*:refs/*'   # todas las referencias, no solo main
tar -xzf /copias/ignorados.tgz
inventario /tmp/git/desde-copia
