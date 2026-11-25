#!/bin/bash
# Banco de ejecución del 704. Corre DENTRO de un contenedor desechable (docker run --rm --network none).
# Cada script se ejecuta dos veces, cada vez en su propio directorio de mktemp:
#   control  -> S="_"  (nombres sin espacios)
#   espacios -> S=" "  (los mismos nombres con espacios)
# Entrada: /h/tareas.sh y /h/lista.txt (líneas «etiqueta id ruta_del_script»). Salida: una línea TSV por pasada.
set -u
source /h/tareas.sh

fixture() {  # crea el accesorio dentro de $BASE; usa $S
  mkdir -p "$D/sub${S}carpeta" "$D/carpeta${S}sin${S}nada" "$DEST"
  printf 'linea de app 1\nERROR en app: uno\nlinea de app 2\nERROR en app: dos\n' > "$D/app.log"
  printf 'inicio del servidor\nERROR primero: conexion rechazada\naviso: memoria\nERROR segundo: timeout\nERROR tercero: disco lleno\nfin\n' \
    > "$D/error${S}del${S}servidor.log"
  { yes 'linea antigua de registro' | head -n 8000; echo 'ERROR viejo'; } > "$D/registro${S}antiguo.log"
  touch -d '40 days ago' "$D/registro${S}antiguo.log"
  printf 'linea del otro archivo\nERROR en otro archivo\n' > "$D/sub${S}carpeta/otro${S}archivo.log"
  for i in 1 1 1 1 1 2 2 2 3 3 4 5; do
    echo "10.0.0.$i - - [29/Oct/2026:10:00:00 +0000] \"GET / HTTP/1.1\" 200 512 \"-\" \"curl/8.0\""
  done > "$D/acceso${S}del${S}sitio.log"
  printf 'Informe final del mes  \nTodo en orden \nFin\n' > "$D/informe${S}final.txt"
  cp "$D/informe${S}final.txt" "$D/sub${S}carpeta/copia${S}del${S}informe.txt"
  printf 'nota uno\r\nnota dos\r\n' > "$D/notas${S}de${S}junio.txt"
  printf 'apunte\n' > "$D/sub${S}carpeta/apuntes${S}de${S}clase.txt"
  head -c 2048 /dev/urandom > "$D/foto${S}de${S}perfil.JPG"
  head -c 122880 /dev/zero > "$D/sub${S}carpeta/volcado${S}grande.dat"
  printf '# configuracion\nnombre_app=Mi App\npuerto=8080\nruta_datos=/srv/datos%sde%sapp\n' "$S" "$S" > "$D/config.conf"
  printf 'respaldo viejo\n' > "$D/copia${S}vieja.bak"; touch -d '40 days ago' "$D/copia${S}vieja.bak"
  printf 'temporal\n' > "$D/sub${S}carpeta/temp${S}de${S}trabajo.tmp"
  printf '#!/bin/sh\necho hola\n' > "$D/sub${S}carpeta/mi${S}script.sh"; chmod 644 "$D/sub${S}carpeta/mi${S}script.sh"
  printf 'nombre,correo\nAna Perez,ana@ejemplo.com\nLuis Gomez,luis@ejemplo.com\n' > "$D/sub${S}carpeta/usuarios.csv"
  printf 'sleep\nnoexiste-xyz\n' > "$D/servicios${S}a${S}vigilar.txt"
  printf '%s\n%s\n' "$D/informe${S}final.txt" "$D/no${S}existe.txt" > "$D/rutas.txt"
  printf 'ana\nluis\n' > "$D/nuevos${S}usuarios.txt"
  mkdir -p "$BASE/.paq"; echo dentro > "$BASE/.paq/dentro.txt"
  tar -czf "$D/paquete${S}de${S}prueba.tar.gz" -C "$BASE/.paq" dentro.txt; rm -r -- "$BASE/.paq"
  ln -s /no/existe "$D/enlace${S}roto"; ln -s "informe${S}final.txt" "$D/enlace${S}bueno"
  for i in 1 2 3 4; do
    tar -czf "$DEST/respaldo-2020010${i}-000000.tar.gz" -T /dev/null; touch -d "2020-01-0${i}" "$DEST/respaldo-2020010${i}-000000.tar.gz"
  done
  printf 'viejo\n' > "$DEST/informe${S}final.txt"; touch -d '2020-01-01' "$DEST/informe${S}final.txt"
}

while read -r etiqueta id ruta; do
  [ -n "$id" ] || continue
  for modo in control espacios; do
    if [ "$modo" = control ]; then S="_"; else S=" "; fi
    BASE=$(mktemp -d); TMPO=$(mktemp -d)
    D="$BASE/datos${S}de${S}prueba"; DEST="$BASE/destino${S}final"
    export S D DEST
    fixture
    OUT="$TMPO/out"; ERR="$TMPO/err"
    "pre_$id"
    ( cd "$BASE" && timeout 20 bash -c 'source /h/tareas.sh; run_'"$id"' "$0"' "$ruta" ) </dev/null >"$OUT" 2>"$ERR"
    RC=$?
    if ( export OUT ERR RC; "check_$id" ) >/dev/null 2>&1; then ok=1; else ok=0; fi
    err1=$(head -c 300 "$ERR" | tr '\t\n' '  ')
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$etiqueta" "$id" "$modo" "$RC" "$ok" "$err1"
    pkill -f 'sleep 300' 2>/dev/null
    rm -rf -- "$BASE" "$TMPO"
  done
done < /h/lista.txt
