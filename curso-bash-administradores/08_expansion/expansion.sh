#!/usr/bin/env bash
# Leccion 8 — Expansiones: lo que bash cambia ANTES de ejecutar tu comando.
cd "$(mktemp -d)" || exit 1

echo "== 8.1 · El patron que no casa con nada =="
mkdir vacia && cd vacia || exit 1
echo "  en una carpeta sin .log:"
for f in *.log; do echo "    <$f>   <- el patron TAL CUAL, no una lista vacia"; done
echo "  Por eso 'for f in *.log; do rm \$f; done' intenta borrar un archivo llamado *.log"
shopt -s nullglob
n=0; for f in *.log; do n=$((n + 1)); done
echo "  con 'shopt -s nullglob': $n vueltas"
shopt -u nullglob
cd .. || exit 1

echo
echo "== 8.2 · La sustitucion se come los saltos del final =="
printf 'linea1\nlinea2\n\n\n' > salida.txt
CONTENIDO=$(cat salida.txt)
echo "  el archivo acaba con 3 saltos; \$(cat) devuelve ${#CONTENIDO} caracteres:"
printf '  <%s>\n' "$CONTENIDO"
echo "  Comodo casi siempre; te muerde cuando comparas hashes o firmas."

echo
echo "== 8.3 · Recortar rutas sin llamar a basename =="
RUTA="/srv/tienda/releases/v3/app.tar.gz"
echo "  \$RUTA                 $RUTA"
echo "  \${RUTA##*/}           ${RUTA##*/}          <- el nombre (lo mas largo por delante)"
echo "  \${RUTA%/*}            ${RUTA%/*}"
echo "  \${RUTA%%.*}           ${RUTA%%.*}"
echo "  \${RUTA##*.}           ${RUTA##*.}                       <- la extension"
echo "  # quita por delante, % por detras · doble = lo mas largo. Y no lanza un proceso."

echo
echo "== 8.4 · Reemplazar y cambiar mayusculas =="
NOMBRE="web-01.produccion.interno"
echo "  \${NOMBRE/./_}         ${NOMBRE/./_}      <- el primero"
echo "  \${NOMBRE//./_}        ${NOMBRE//./_}      <- todos"
echo "  \${NOMBRE^^}           ${NOMBRE^^}"
echo "  \${#NOMBRE}            ${#NOMBRE}"

echo
echo "== 8.5 · LA TRAMPA: la virgulilla entre comillas =="
echo "  ~/copias        ->  $(eval echo ~/copias)"
DESTINO="~/copias"
echo "  DESTINO=\"~/copias\"  ->  $DESTINO   <- no se expandio: es texto"
echo "  mkdir \"\$DESTINO\" crea una carpeta que se llama ~ . Usa \$HOME."
echo "  DESTINO=\"\$HOME/copias\"  ->  $HOME/copias"

echo
echo "== 8.6 · Llaves: sirven para crear, y para destrozar =="
mkdir -p copias/{diario,semanal,mensual}
echo "  mkdir -p copias/{diario,semanal,mensual}  ->  $(ls copias | tr '\n' ' ')"
echo "  echo backup-{1..3}.tar  ->  $(echo backup-{1..3}.tar)"
echo "  Se expanden ANTES que las variables: con una variable dentro NO funcionan."
N=3
echo "  N=3 · echo {1..\$N}  ->  $(eval echo "{1..$N}")   (hay que usar eval, o seq)"
