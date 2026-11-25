#!/usr/bin/env bash
# Leccion 11 — #!/bin/sh no es bash: el script que solo falla en el contenedor.
cd "$(mktemp -d)" || exit 1

cat > bashismos.sh <<'FIN'
#!/bin/sh
RAMA="feature/pago"
if [[ $RAMA == feature/* ]]; then
  echo "  es una rama de feature"
fi
set -o pipefail
NOMBRES=(web-01 web-02)
echo "  ${NOMBRES[0]^^}"
FIN

echo "== 11.1 · Por que el script pasa en tu maquina =="
echo "  El shebang dice #!/bin/sh. Y aqui:"
echo "    sh -c 'echo \$BASH_VERSION'  ->  $(sh -c 'echo "${BASH_VERSION:-no es bash}"')"
echo "  En esta maquina (y en muchas) /bin/sh ES bash, asi que el script funciona:"
sh bashismos.sh 2>&1 | sed 's/^/  /'
echo "  En Debian y Ubuntu, /bin/sh es dash. En Alpine, busybox. Ahi NO funciona."

echo
echo "== 11.2 · Lo que no existe en un sh de verdad =="
echo "  [[ ]] · arrays · \${VAR^^} · \${VAR//a/b} · (( )) · local · función() con 'function'"
echo "  set -o pipefail · echo -e · read -a · <<< (here-string) · < <(...) · \${!VAR}"
echo "  En dash, '[[' se lee como un comando que no existe: 'not found', y el if falla."

echo
echo "== 11.3 · Detectarlos sin tener ese shell delante =="
buscar_bashismos() {
  local archivo="$1" n=0
  while IFS= read -r linea_n; do
    n=$((n + 1))
    echo "  $linea_n"
  done < <(grep -nE '\[\[|\]\]|\(\(|\blocal\b|\$\{[A-Za-z_]+\^\^|\$\{[A-Za-z_]+\/\/|=\(|<<<|pipefail|echo -e' "$archivo")
  echo "  -> $n lineas sospechosas en $archivo"
}
echo "  una comprobacion casera (grep) sobre bashismos.sh:"
buscar_bashismos bashismos.sh
echo "  Y se deja una: la linea 8, \${NOMBRES[0]^^}, que el grep casero no caza."
echo "  Esa es la lección: un grep hecho a mano siempre se deja algo."
echo "  Lo serio es shellcheck: lee el shebang y avisa de cada bashismo (SC2039/SC3010),"
echo "  sin ejecutar nada. Es el primer paso de cualquier pipeline que toque bash."

echo
echo "== 11.4 · El shebang, y lo que cambia entre maquinas aunque uses bash =="
echo "  #!/usr/bin/env bash    <- busca bash en el PATH (mejor que /bin/bash fijo)"
echo "  bash de esta maquina: $BASH_VERSION"
echo "  macOS trae bash 3.2 (de 2007) por licencia: sin arrays asociativos, sin \${VAR^^}"
echo "  Y GNU y BSD no comparten opciones: sed -i, readlink -f, stat -c, date -d"
echo "  date -d '1 hour ago'  ->  $(date -d '1 hour ago' '+%H:%M' 2>/dev/null || echo 'en BSD/macOS no existe: es date -v-1H')"

echo
echo "== 11.5 · La regla =="
echo "  Si el script usa bashismos (y casi todos los usan), el shebang dice bash."
echo "  Si tiene que correr en el contenedor mas pelado que haya, se escribe en POSIX"
echo "  y se comprueba: shellcheck -s sh script.sh"
