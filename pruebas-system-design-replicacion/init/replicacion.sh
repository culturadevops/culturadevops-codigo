#!/bin/sh
# Se ejecuta una vez, al crear el primario: el usuario de replicación y su permiso en pg_hba.conf.
set -e
psql -v ON_ERROR_STOP=1 -U postgres -d tienda <<'SQL'
CREATE ROLE replicador WITH REPLICATION LOGIN PASSWORD 'replica-lab';
CREATE TABLE pedidos (id bigserial PRIMARY KEY, total int NOT NULL, creado timestamptz DEFAULT now());
CREATE TABLE carga (id bigserial PRIMARY KEY, relleno text);
SQL
echo "host replication replicador all scram-sha-256" >> "$PGDATA/pg_hba.conf"
