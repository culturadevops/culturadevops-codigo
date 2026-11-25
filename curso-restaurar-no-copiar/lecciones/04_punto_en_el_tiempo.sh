#!/usr/bin/env bash
# Lección 4 · Volver a un segundo concreto: la restauración a un punto en el tiempo.
#
# Un DELETE sin WHERE a las 17:02. La copia de la noche es de las 3:00: restaurarla es perder
# catorce horas de pedidos. Con una copia base + el WAL archivado (el diario de cada cambio),
# Postgres se reconstruye hasta el segundo ANTERIOR al error, y para ahí.
#
# Y la trampa: si el archivado del WAL falla, Postgres no se cae ni avisa en tu terminal. Solo lo
# apunta en su registro y en pg_stat_archiver. Tienes copia base... y un diario con huecos.
source /curso/comun.sh

vender() { psql -q -c "INSERT INTO pedidos (cliente, total) SELECT 'web', 9.99 FROM generate_series(1,$1)"; }

titulo "4.1 · La copia base, y la tienda sigue vendiendo"
sembrar 1000 >/dev/null
rm -rf /copias/base && mkdir -p /copias/base
pg_basebackup -D /copias/base -Fp -X stream -c fast
echo "  copia base hecha con $(filas tienda) pedidos"
pg_dump -Fc -f /copias/noche.dump tienda          # y la «copia de la noche», para comparar
for i in 1 2 3; do vender 100; sleep 1; done
BUENO=$(psql -tAc "SELECT now()")
CUANTOS=$(filas tienda)
echo "  $BUENO -> todo bien, $CUANTOS pedidos"
sleep 1

titulo "4.2 · El desastre: un DELETE sin WHERE, y la tienda no se entera"
psql -q -c "DELETE FROM pedidos"
echo "  $(psql -tAc "SELECT now()") -> DELETE FROM pedidos;  quedan $(filas tienda)"
vender 50; sleep 1; vender 50
psql -q -c "SELECT pg_switch_wal()" -o /dev/null
sleep 3   # archive_timeout=1: que el último trozo de WAL llegue al archivo

titulo "4.3 · Restaurar la copia de la noche"
base_nueva noche
pg_restore -d noche /copias/noche.dump
echo "  pedidos: $(filas noche) de $CUANTOS -> se pierden $((CUANTOS - $(filas noche)))"

titulo "4.4 · Restaurar hasta el segundo anterior al DELETE"
rm -rf /tmp/pitr /tmp/pitr.log && cp -a /copias/base /tmp/pitr && chown -R postgres /tmp/pitr && chmod 700 /tmp/pitr
touch /tmp/pitr/recovery.signal
cat >> /tmp/pitr/postgresql.auto.conf <<CONF
restore_command = 'cp /archivo/%f %p'
recovery_target_time = '$BUENO'
recovery_target_action = 'promote'
archive_mode = off
CONF
t0=$(ahora_ms)
su postgres -c "pg_ctl -D /tmp/pitr -o '-p 5434 -k /tmp' -l /tmp/pitr.log -w start" >/dev/null
for _ in $(seq 1 150); do [ "$(psql -h /tmp -p 5434 -d tienda -tAc 'SELECT pg_is_in_recovery()' 2>/dev/null)" = "f" ] && break; sleep 0.2; done
t1=$(ahora_ms)
RECUP=$(psql -h /tmp -p 5434 -d tienda -tAc "SELECT count(*) FROM pedidos")
echo "  pedidos: $RECUP de $CUANTOS -> se pierden $((CUANTOS - RECUP)) · tardó $((t1 - t0)) ms"
echo "  (y los 100 vendidos DESPUÉS del DELETE tampoco están: esos hay que rescatarlos aparte)"
grep -E "recovery stopping|starting point-in-time" /tmp/pitr.log | sed -E 's/^.*(LOG|LOG:) +//; s/^/  log: /'
su postgres -c "pg_ctl -D /tmp/pitr stop -m fast" >/dev/null

titulo "4.5 · La trampa: el archivado que falla en silencio"
# Lo que le pasó a este laboratorio la primera vez: la carpeta del archivo, sin permiso de escritura.
chmod 555 /archivo
antes=$(psql -tAc "SELECT failed_count FROM pg_stat_archiver")
vender 100; psql -q -c "SELECT pg_switch_wal()" -o /dev/null; sleep 4
psql -tAc "SELECT '  pg_stat_archiver: fallos ' || $antes || ' -> ' || failed_count || ' · último archivado: ' || coalesce(last_archived_wal,'-') || ' · último fallido: ' || coalesce(last_failed_wal,'-') FROM pg_stat_archiver"
echo "  y la tienda: sigue vendiendo, $(filas tienda) pedidos, ni un error"
chmod 755 /archivo
