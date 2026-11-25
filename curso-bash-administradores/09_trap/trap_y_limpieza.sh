#!/usr/bin/env bash
# Leccion 9 — trap: dejar la maquina como estaba, aunque el script muera a mitad.
cd "$(mktemp -d)" || exit 1
BASE="$PWD"

echo "== 9.1 · LA TRAMPA: el temporal que se queda =="
cat > sin_trap.sh <<'FIN'
#!/usr/bin/env bash
set -euo pipefail
TMP=$(mktemp -d "$BASE/trabajo.XXXX")
echo "  trabajando en $(basename "$TMP")"
cp /no/existe/app.tar.gz "$TMP/"        # revienta aqui
rm -rf "$TMP"                            # ...y esto no se ejecuta nunca
FIN
BASE="$BASE" bash sin_trap.sh 2>&1 | sed 's/^/  /'
echo "  temporales que han quedado: $(ls -d "$BASE"/trabajo.* 2>/dev/null | wc -l)"
echo "  Multiplicalo por un cron cada 5 minutos y ahi tienes el disco lleno."

echo
echo "== 9.2 · Con trap EXIT, se limpia pase lo que pase =="
rm -rf "$BASE"/trabajo.*
cat > con_trap.sh <<'FIN'
#!/usr/bin/env bash
set -euo pipefail
TMP=$(mktemp -d "$BASE/trabajo.XXXX")
limpiar() { local c=$?; rm -rf "$TMP"; echo "  limpieza hecha (codigo $c)"; }
trap limpiar EXIT                        # se ejecuta al salir: bien, mal o matado
echo "  trabajando en $(basename "$TMP")"
cp /no/existe/app.tar.gz "$TMP/"
FIN
BASE="$BASE" bash con_trap.sh 2>&1 | sed 's/^/  /'
echo "  temporales que han quedado: $(ls -d "$BASE"/trabajo.* 2>/dev/null | wc -l)"

echo
echo "== 9.3 · El trap tambien salta con una señal =="
cat > matame.sh <<'FIN'
#!/usr/bin/env bash
trap 'echo "  me han matado: limpio y salgo"; exit 130' INT TERM
trap 'echo "  (EXIT: la limpieza final siempre pasa por aqui)"' EXIT
echo "  esperando..."
sleep 30
FIN
bash matame.sh & PID=$!
sleep 1
kill -TERM "$PID" 2>/dev/null
wait "$PID" 2>/dev/null
echo "  codigo con el que salio: $?"
echo "  Sin trap, un TERM deja la maquina a medias: el cerrojo puesto, el temporal lleno."

echo
echo "== 9.4 · trap ERR: enterarte de DONDE fallo =="
cat > con_err.sh <<'FIN'
#!/usr/bin/env bash
set -euo pipefail
trap 'echo "  fallo en la linea $LINENO: $BASH_COMMAND" >&2' ERR
echo "  paso 1"
false
echo "  paso 2 (no se ve)"
FIN
bash con_err.sh 2>&1 | sed 's/^/  /'

echo
echo "== 9.5 · Los temporales, siempre con mktemp =="
echo "  mal:  TMP=/tmp/copia.\$\$        <- predecible: otro puede crearlo antes (enlace)"
echo "  bien: TMP=\$(mktemp -d)          <- nombre al azar, y en Linux permisos 700"
T=$(mktemp -d)
echo "  permisos aqui: $(stat -c %a "$T" 2>/dev/null || echo "?") (esta grabado en Windows;"
echo "  en Linux mktemp -d da 700: solo tu entras)"
rmdir "$T"
echo "  y el trap EXIT de la primera linea del script, antes de crear nada mas."
