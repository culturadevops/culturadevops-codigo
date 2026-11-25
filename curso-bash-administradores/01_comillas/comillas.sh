#!/usr/bin/env bash
# Leccion 1 — Las comillas no son estilo: son lo que separa una palabra de cinco.
cd "$(mktemp -d)" || exit 1

echo "== 1.1 · Un archivo con un espacio en el nombre =="
touch "informe final.log"
ARCHIVO="informe final.log"
echo "  ARCHIVO=$ARCHIVO"
echo "  sin comillas, bash parte por espacios:"
for palabra in $ARCHIVO; do echo "    palabra: <$palabra>"; done
echo "  con comillas, es UNA:"
for palabra in "$ARCHIVO"; do echo "    palabra: <$palabra>"; done

echo
echo "== 1.2 · LA TRAMPA: en esa carpeta hay mas archivos =="
touch informe final.log
ls
echo "  y ahora: rm \$ARCHIVO"
set -x
rm $ARCHIVO
{ set +x; } 2>/dev/null
echo "  lo que queda:"
ls
echo "  Borro 'informe' y 'final.log', que no tenian nada que ver,"
echo "  y el que querias borrar sigue ahi."

echo
echo "== 1.3 · Con comillas, una sola palabra =="
set -x
rm "$ARCHIVO"
{ set +x; } 2>/dev/null
echo "  quedan: $(ls | wc -l) archivos"

echo
echo "== 1.4 · Y el * que se cuela =="
touch uno.log dos.log tres.log
PATRON="*"
echo '  PATRON="*"  y en la carpeta hay uno.log dos.log tres.log'
set -x
echo $PATRON
echo "$PATRON"
{ set +x; } 2>/dev/null
echo "  Sin comillas, bash cambia el * por los nombres ANTES de ejecutar el comando."
echo "  Si eso llega a un rm, borras lo que haya."

echo
echo "== 1.5 · Los dos sitios donde NO hacen falta =="
if [[ $ARCHIVO == *final* ]]; then echo "  dentro de [[ ... ]] no hay partido de palabras"; fi
VACIA=
if [ -n $VACIA ]; then echo "  [ -n \$VACIA ]   dice que NO esta vacia   <- mentira"; fi
if [ -n "$VACIA" ]; then echo "  mal"; else echo "  [ -n \"\$VACIA\" ] dice que si lo esta   <- correcto"; fi
echo "  Sin comillas, [ -n \$VACIA ] se convierte en [ -n ], y '-n' como texto es no vacio."
echo "  Regla practica: entrecomilla SIEMPRE, menos dentro de [[ ]] y (( ))."
