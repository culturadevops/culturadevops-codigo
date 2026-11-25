#!/usr/bin/env bash
# Leccion 3 — La variable vacia: rm -rf "$DIR"/* cuando DIR no trae nada.
#
# ⚠️ NADA de lo que borra esta leccion sale de una carpeta temporal. El comando peligroso
#    de verdad (con la ruta ABSOLUTA) se ENSEÑA con echo delante: se ve lo que el shell
#    iba a ejecutar, y no se ejecuta. Escribir la version que se ejecuta de verdad, aunque
#    sea "para probar", es como se pierden maquinas.
RAIZ="$(mktemp -d)"
cd "$RAIZ" || exit 1

mkdir -p srv/tienda/releases/v3 srv/tienda/datos etc/nginx var/log
touch srv/tienda/datos/pedidos.db etc/nginx/nginx.conf var/log/app.log

echo "== 3.1 · La maquina de juguete, antes =="
find . | sort | sed 's/^/  /'

echo
echo "== 3.2 · El script de limpieza de toda la vida =="
cat > limpiar.sh <<'FIN'
#!/usr/bin/env bash
DIR="$1"
rm -rf "$DIR"/*
echo "  limpiado: ${DIR:-(vacio)}"
FIN
echo "  rm -rf \"\$DIR\"/*    <- con la variable puesta hace lo que dice:"
bash limpiar.sh "$RAIZ/srv/tienda/releases"
find srv | sort | sed 's/^/  /'

echo
echo "== 3.3 · LA TRAMPA: el dia que llega vacia =="
echo "  (un typo en el nombre, un \$1 que no llego, un 'source' que fallo antes)"
DIR=""
echo "  lo que el shell IBA a ejecutar (impreso, NO ejecutado):"
printf '    rm -rf %s/*
' "$DIR"
echo "  Eso no es un error de sintaxis ni da aviso: es un comando valido"
echo "  que borra la raiz. El shell no pregunta."

echo
echo "== 3.4 · El mismo fallo, ejecutado de verdad (dentro de la carpeta temporal) =="
cat > limpiar_relativo.sh <<'FIN'
#!/usr/bin/env bash
SUB="$1"
cd "$BASE" || exit 1
rm -rf "./$SUB"/*        # relativo: aqui el destrozo se queda en la carpeta de pruebas
FIN
echo "  BASE=<carpeta temporal>   SUB=\"\"   ->  rm -rf .//*"
BASE="$RAIZ" bash limpiar_relativo.sh ""
echo "  lo que queda de la maquina:"
find . | sort | sed 's/^/  /'
echo "  Se llevo srv, etc y var. En la maquina de verdad, con la ruta absoluta,"
echo "  se lleva lo mismo pero empezando por la raiz."

echo
echo "== 3.5 · Tres formas de que no pase =="
mkdir -p srv/tienda/releases/v3
cat > limpiar_bien.sh <<'FIN'
#!/usr/bin/env bash
set -euo pipefail
DIR="${1:?falta el directorio a limpiar}"        # 1) revienta si esta vacio
[[ -d $DIR ]] || { echo "  no es un directorio: $DIR" >&2; exit 2; }
case "$DIR" in
  /|/bin|/etc|/srv|/usr|/var|/home) echo "  me niego a limpiar $DIR" >&2; exit 2 ;;  # 2) lista negra
esac
cd "$DIR"                                         # 3) entra primero y borra desde dentro
rm -rf ./*
echo "  limpiado: $DIR"
FIN
echo "  sin argumento:"
bash limpiar_bien.sh 2>&1 | sed 's/^/  /'
echo "  codigo de salida: $(bash limpiar_bien.sh >/dev/null 2>&1; echo $?)"
echo "  con una ruta prohibida:"
bash limpiar_bien.sh / 2>&1 | sed 's/^/  /'
echo "  con la ruta buena:"
bash limpiar_bien.sh "$RAIZ/srv/tienda/releases" 2>&1 | sed 's/^/  /'

echo
echo "== 3.6 · Y el otro clasico: el espacio colado =="
echo '  rm -rf "$DIR /viejo"   <- un espacio dentro de las comillas: DOS rutas'
echo '  rm -rf "$DIR"/viejo    <- una sola'
echo "  Regla: \${DIR:?} en vez de \$DIR, y un echo delante hasta que lo veas bien."
rm -rf "$RAIZ"
