#!/usr/bin/env bash
# ensayo.sh — el simulacro de restauración, de principio a fin.
#
#   1. COPIA     roles + base de datos, y la «huella» de cada tabla (filas y md5) tomada en la
#                MISMA instantánea que la copia: así se compara con lo que la copia vio, no con lo
#                que hay ahora (que ya cambió).
#   2. RESTAURA  en un servidor nuevo, aparte, con --exit-on-error. Cronometrado (RTO).
#   3. VERIFICA  la huella de cada tabla restaurada contra la de la copia.
#   4. INFORMA   y sale con 0 (todo bien), 1 (restaura pero los datos no cuadran) o 2 (ni copia ni
#                restaura).
#
# Uso:  ensayo.sh [-d BASE] [-x "opciones extra de pg_dump"] [-r] [-c DIR]
#         -c DIR  no hace copia: ensaya la que ya hay en DIR (la que dejaría tu cron)
#         -r      rompe la copia a propósito antes de restaurar (para ver el código 2)
set -uo pipefail
BASE=tienda; EXTRA=""; ROMPER=0; DIR=""
while getopts "d:x:rc:" o; do
  case $o in d) BASE=$OPTARG ;; x) EXTRA=$OPTARG ;; r) ROMPER=1 ;; c) DIR=$OPTARG ;; *) exit 2 ;; esac
done
MIN=1024
SRV=/tmp/ensayo-srv; PUERTO=5435
fallo() { echo "  ✗ $*"; echo "  RESULTADO: no hay copia que sirva (código 2)"; exit 2; }
ms() { date +%s%3N; }

# huella de cada tabla: «tabla filas md5», ordenada. Se lee de stdin una conexión ya abierta.
SQL_HUELLA="SELECT format('%s %s %s', c.relname,
  (xpath('/row/n/text()', query_to_xml(format('SELECT count(*) AS n FROM %I', c.relname), false, true, '')))[1],
  (xpath('/row/h/text()', query_to_xml(format('SELECT md5(coalesce(string_agg(t::text, ''|'' ORDER BY t::text), '''')) AS h FROM %I t', c.relname), false, true, '')))[1])
  FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE c.relkind = 'r' AND n.nspname = 'public' ORDER BY 1;"

echo "ensayo de restauración · base de datos «$BASE» · $(date -u +'%Y-%m-%d %H:%M:%SZ')"

# ── 1 · COPIA ─────────────────────────────────────────────────────────────────────────────
if [ -z "$DIR" ]; then
  DIR=$(mktemp -d /copias/ensayo-XXXX)
  # Una sesión que abre una instantánea y la mantiene viva mientras pg_dump la usa.
  rm -f /tmp/ensayo.fifo && mkfifo /tmp/ensayo.fifo
  psql -qAtX -d "$BASE" < /tmp/ensayo.fifo > "$DIR/sesion.out" 2>&1 &
  SES=$!
  exec 3>/tmp/ensayo.fifo
  echo "BEGIN ISOLATION LEVEL REPEATABLE READ; SELECT pg_export_snapshot();" >&3
  for _ in $(seq 1 50); do grep -q . "$DIR/sesion.out" 2>/dev/null && break; sleep 0.1; done
  SNAP=$(grep -E '^[0-9A-F]+-[0-9A-F]+-[0-9]+$' "$DIR/sesion.out" | head -1)
  [ -n "$SNAP" ] || fallo "no se pudo abrir la instantánea: $(head -1 "$DIR/sesion.out")"
  date +%s > "$DIR/hora"
  # shellcheck disable=SC2086
  pg_dump -Fc --snapshot="$SNAP" $EXTRA -f "$DIR/base.dump" "$BASE" 2>"$DIR/pg_dump.err" \
    || { exec 3>&-; fallo "pg_dump: $(head -1 "$DIR/pg_dump.err")"; }
  echo "$SQL_HUELLA" >&3
  echo "COMMIT;" >&3
  exec 3>&-; wait $SES
  grep -vE '^(BEGIN|COMMIT|[0-9A-F]+-[0-9A-F]+-[0-9]+)$' "$DIR/sesion.out" > "$DIR/huella"
  pg_dumpall --globals-only -f "$DIR/roles.sql" 2>"$DIR/roles.err" || fallo "pg_dumpall: $(head -1 "$DIR/roles.err")"
fi
[ -f "$DIR/base.dump" ] || fallo "en $DIR no hay base.dump"
[ "$(stat -c %s "$DIR/base.dump")" -ge $MIN ] || fallo "base.dump tiene $(stat -c %s "$DIR/base.dump") bytes: está vacía"
echo "  1 · copia: $(( $(stat -c %s "$DIR/base.dump") / 1024 )) KB · $(wc -l < "$DIR/huella") tablas en la huella"
if [ $ROMPER = 1 ]; then
  truncate -s $(( $(stat -c %s "$DIR/base.dump") / 2 )) "$DIR/base.dump"
  echo "    (rota a propósito: cortada por la mitad)"
fi

# ── 2 · RESTAURA en un servidor nuevo ───────────────────────────────────────────────────────
rm -rf $SRV && mkdir -p $SRV && chown postgres $SRV
su postgres -c "initdb -D $SRV -U admin --auth=trust >/dev/null && pg_ctl -D $SRV -o '-p $PUERTO -k /tmp' -l $SRV.log -w start >/dev/null" \
  || fallo "no arranca el servidor de ensayo"
trap 'su postgres -c "pg_ctl -D $SRV stop -m fast" >/dev/null 2>&1' EXIT
N=(-h /tmp -p $PUERTO -U admin)
t0=$(ms)
psql "${N[@]}" -qX -d postgres -f "$DIR/roles.sql" 2>&1 | grep -v 'role "admin" already exists' | sed 's/^/    /'
psql "${N[@]}" -qX -d postgres -c "CREATE DATABASE $BASE"
pg_restore "${N[@]}" -d "$BASE" --exit-on-error "$DIR/base.dump" 2>"$SRV.err" \
  || fallo "pg_restore: $(grep -m1 -E 'error|ERROR' "$SRV.err" | sed 's/^pg_restore: //')"
t1=$(ms)
echo "  2 · restaurada en un servidor nuevo en $((t1 - t0)) ms"

# ── 3 · VERIFICA ──────────────────────────────────────────────────────────────────────────
echo "$SQL_HUELLA" | psql "${N[@]}" -qAtX -d "$BASE" > $SRV.huella
malas=0
echo "  3 · verificación, tabla por tabla:"
while read -r tabla filas md5; do
  r=$(grep "^$tabla " $SRV.huella)
  rf=$(echo "$r" | awk '{print $2}'); rm5=$(echo "$r" | awk '{print $3}')
  if [ "$rf" = "$filas" ] && [ "$rm5" = "$md5" ]; then
    printf '      %-12s %8s filas  ✓\n' "$tabla" "$filas"
  else
    printf '      %-12s %8s filas en la copia, %s restauradas  ✗\n' "$tabla" "$filas" "${rf:-0}"
    malas=$((malas + 1))
  fi
done < "$DIR/huella"

# ── 4 · INFORME ───────────────────────────────────────────────────────────────────────────
edad=$(( $(date +%s) - $(cat "$DIR/hora") ))
echo "  4 · RTO medido: $((t1 - t0)) ms · RPO: lo escrito en los últimos $edad s (la edad de la copia)"
if [ $malas -gt 0 ]; then
  echo "  RESULTADO: restaura, pero $malas tabla(s) no cuadran (código 1)"; exit 1
fi
echo "  RESULTADO: la copia sirve (código 0)"
