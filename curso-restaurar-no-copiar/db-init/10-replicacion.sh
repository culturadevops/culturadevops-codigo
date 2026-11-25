#!/bin/sh
# pg_basebackup desde el operador es una conexion de REPLICACION, y la imagen oficial solo las
# acepta en local. Esta linea la abre a la red del laboratorio (y solo a ella).
echo "host replication all all scram-sha-256" >> "$PGDATA/pg_hba.conf"
