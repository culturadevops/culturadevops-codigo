#!/bin/sh
# Arranque de una réplica: copia base del primario (pg_basebackup -R deja la configuración de standby)
# y Postgres en modo réplica. cluster_name es el nombre con el que el primario la ve (r1, r2).
set -e
until pg_isready -q -h sd-primario -U postgres; do sleep 0.5; done
rm -rf "$PGDATA"/*
PGPASSWORD=replica-lab pg_basebackup -h sd-primario -U replicador -D "$PGDATA" -R -X stream -C -S "$NOMBRE"
chown -R postgres:postgres "$PGDATA"
chmod 700 "$PGDATA"
exec gosu postgres postgres -c hot_standby=on -c cluster_name="$NOMBRE"
