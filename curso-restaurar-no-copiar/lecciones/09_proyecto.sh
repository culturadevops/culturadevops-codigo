#!/usr/bin/env bash
# Lección 9 · El proyecto: ensayo.sh, el simulacro que se programa igual que la copia.
source /curso/comun.sh
sembrar 1000 >/dev/null
psql -q -c "DROP TABLE IF EXISTS facturas" -c "CREATE TABLE facturas AS SELECT g AS id, g * 1.21 AS importe FROM generate_series(1, 500) g"
# La tienda sigue vendiendo durante todo el ensayo: la huella tiene que ser la de la copia.
( while true; do psql -q -c "INSERT INTO pedidos (cliente, total) VALUES ('web', 9.99)" 2>/dev/null; sleep 0.05; done ) &
TIENDA=$!

titulo "9.1 · El ensayo, con la tienda vendiendo"
bash /curso/ensayo.sh; echo "  -> código de salida $?"

titulo "9.2 · La copia que «alguien» aligeró: --exclude-table-data=facturas"
bash /curso/ensayo.sh -x "--exclude-table-data=facturas"; echo "  -> código de salida $?"

titulo "9.3 · Una copia dañada"
bash /curso/ensayo.sh -r; echo "  -> código de salida $?"

titulo "9.4 · La copia que dejó el cron de la lección 1"
mkdir -p /copias/de-cron && cp /tmp/vacia.gz /copias/de-cron/base.dump 2>/dev/null || printf '' | gzip > /copias/de-cron/base.dump
bash /curso/ensayo.sh -c /copias/de-cron; echo "  -> código de salida $?"

kill $TIENDA; wait $TIENDA 2>/dev/null

exit 0
