#!/bin/bash
# Demo de «Postgres: vuelve al segundo antes del desastre» (cultura-devops, 2026-10-20). Corre DENTRO de postgres:18
# (lo lanza ejecutar.sh) como el usuario postgres. Sin red, sin nube: un servidor, su archivo de WAL y una copia base.
#   1 · servidor con archive_mode=on (cada segmento de WAL se copia a /archivo)
#   2 · copia base con pg_basebackup
#   3 · se trabaja: pedidos nuevos; se anota la hora
#   4 · el desastre: DELETE sin WHERE
#   5 · recuperación a un punto en el tiempo (recovery_target_time) en un servidor NUEVO
set -u
export PGDATA=/tmp/pg PGPORT=5432 PATH=/usr/lib/postgresql/18/bin:$PATH
B=/tmp/base A=/tmp/archivo R=/tmp/restaurado
rm -rf $PGDATA $B $A $R && mkdir -p $A
q() { psql -X -q -d tienda -c "$1"; }
qa() { psql -X -qtA -d tienda -c "$1"; }

echo "### 1 · Un Postgres que guarda su WAL"
initdb -U postgres -D $PGDATA >/dev/null 2>&1
cat >> $PGDATA/postgresql.conf <<EOF
wal_level = replica
archive_mode = on
archive_command = 'cp %p $A/%f'
archive_timeout = 10
EOF
pg_ctl -D $PGDATA -l /tmp/pg.log -w start >/dev/null
createdb tienda
echo "\$ psql -c 'SHOW archive_command'"
psql -X -qtA -c "SHOW archive_command"
q "CREATE TABLE pedidos (id serial PRIMARY KEY, cliente text, total int, creado timestamptz DEFAULT now())"
q "INSERT INTO pedidos (cliente, total) SELECT 'cliente-' || g, g * 10 FROM generate_series(1, 1000) g"
echo "\$ psql -c 'SELECT count(*) FROM pedidos'"
qa "SELECT count(*) FROM pedidos"

echo
echo "### 2 · La copia base"
echo "\$ pg_basebackup -D /tmp/base -X stream            # por defecto: espera un checkpoint «suave»"
{ time -p pg_basebackup -D $B -X stream ; } 2>&1 | grep real
rm -rf $B
echo "\$ pg_basebackup -D /tmp/base -X stream -c fast    # pide el checkpoint ya"
{ time -p pg_basebackup -D $B -X stream -c fast ; } 2>&1 | grep real
echo "\$ du -sh /tmp/base"
du -sh $B | cut -f1

echo
echo "### 3 · Se sigue trabajando después de la copia"
q "INSERT INTO pedidos (cliente, total) SELECT 'nuevo-' || g, g * 7 FROM generate_series(1, 500) g"
echo "\$ psql -c 'SELECT count(*) FROM pedidos'"
qa "SELECT count(*) FROM pedidos"
sleep 2
ANTES=$(qa "SELECT now()::timestamptz(0)")
echo "\$ psql -c 'SELECT now()'   # la hora buena, la que vamos a recuperar"
echo "$ANTES"
sleep 2

echo
echo "### 4 · El desastre"
echo "\$ psql -c 'DELETE FROM pedidos'   # sin WHERE"
psql -X -d tienda -c "DELETE FROM pedidos"
echo "\$ psql -c 'SELECT count(*) FROM pedidos'"
qa "SELECT count(*) FROM pedidos"
psql -X -qtA -c "SELECT pg_switch_wal()" >/dev/null
sleep 3
echo "\$ ls /tmp/archivo | wc -l   # segmentos de WAL archivados"
ls $A | grep -v backup | wc -l

echo
echo "### 5 · Volver al segundo antes del DELETE"
pg_ctl -D $PGDATA -m fast stop >/dev/null
cp -r $B $R && chmod 700 $R
cat >> $R/postgresql.conf <<EOF
restore_command = 'cp $A/%f %p'
recovery_target_time = '$ANTES'
recovery_target_action = 'promote'
archive_mode = off
EOF
touch $R/recovery.signal
echo "\$ cat recovery (lo que añado a postgresql.conf)"
echo "restore_command = 'cp /tmp/archivo/%f %p'"
echo "recovery_target_time = '$ANTES'"
echo "recovery_target_action = 'promote'"
echo "\$ touch recovery.signal && pg_ctl start"
pg_ctl -D $R -l /tmp/restaurado.log -w start >/dev/null
for i in $(seq 1 30); do [ "$(psql -X -qtA -c 'SELECT pg_is_in_recovery()')" = "f" ] && break; sleep 1; done
echo "\$ grep -E 'starting point-in-time|recovery stopping|archive recovery complete' postgresql.log"
grep -E "starting point-in-time recovery|recovery stopping|archive recovery complete" /tmp/restaurado.log | sed -E 's/^[0-9-]+ [0-9:.]+ [A-Z]+ \[[0-9]+\] //'
echo "\$ psql -c 'SELECT count(*), max(creado) FROM pedidos'"
qa "SELECT count(*), max(creado)::timestamptz(0) FROM pedidos"
pg_ctl -D $R -m fast stop >/dev/null
