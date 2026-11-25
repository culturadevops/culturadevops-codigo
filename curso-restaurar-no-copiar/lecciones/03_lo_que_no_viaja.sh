#!/usr/bin/env bash
# Lección 3 · Lo que pg_dump no lleva: los roles.
#
# pg_dump copia UNA base de datos. Los usuarios (roles) y sus contraseñas no son de ninguna base de
# datos: son del servidor entero. Restauras en un servidor nuevo y psql va escupiendo
# «role "app" does not exist»... y termina con código 0, porque por defecto psql sigue adelante
# con cada error. El script de restauración dice «hecho». La aplicación no puede entrar.
source /curso/comun.sh

# Un servidor de restauración limpio, levantado aquí al lado (puerto 5433), como el día del desastre.
nuevo_servidor() {
  rm -rf /tmp/nuevo && mkdir -p /tmp/nuevo && chown postgres /tmp/nuevo
  su postgres -c "initdb -D /tmp/nuevo -U admin --auth=trust >/dev/null && pg_ctl -D /tmp/nuevo -o '-p 5433 -k /tmp' -l /tmp/nuevo.log start >/dev/null"
}
parar_servidor() { su postgres -c "pg_ctl -D /tmp/nuevo stop -m fast >/dev/null"; }
EN_NUEVO=(-h /tmp -p 5433 -U admin)

# El original: la aplicación entra con su propio rol, dueño de sus tablas.
sembrar 1000 >/dev/null
psql -q -c "DROP ROLE IF EXISTS app" 2>/dev/null
psql -q -c "CREATE ROLE app LOGIN PASSWORD 'secreto-app'" -c "ALTER TABLE pedidos OWNER TO app"
pg_dump -f /copias/tienda.sql tienda

titulo "3.1 · Restaurar la copia en un servidor nuevo, como siempre"
nuevo_servidor
psql "${EN_NUEVO[@]}" -q -c "CREATE DATABASE tienda" postgres
psql "${EN_NUEVO[@]}" -q -o /dev/null -d tienda -f /copias/tienda.sql 2>&1 | sed 's/^/  /'
echo "  psql: código de salida ${PIPESTATUS[0]}"
echo "  pedidos restaurados: $(psql "${EN_NUEVO[@]}" -d tienda -tAc 'SELECT count(*) FROM pedidos')"
echo "  dueño de la tabla: $(psql "${EN_NUEVO[@]}" -d tienda -tAc "SELECT tableowner FROM pg_tables WHERE tablename='pedidos'")"
psql "${EN_NUEVO[@]}" -d tienda -tAc "SELECT 'rol app: ' || CASE WHEN EXISTS (SELECT 1 FROM pg_roles WHERE rolname='app') THEN 'existe' ELSE 'NO EXISTE' END" | sed 's/^/  /'
parar_servidor

titulo "3.2 · Lo mismo con ON_ERROR_STOP: el primer error para todo"
nuevo_servidor
psql "${EN_NUEVO[@]}" -q -c "CREATE DATABASE tienda" postgres
psql "${EN_NUEVO[@]}" -q -v ON_ERROR_STOP=1 -o /dev/null -d tienda -f /copias/tienda.sql 2>&1 | sed 's/^/  /'
echo "  psql: código de salida ${PIPESTATUS[0]}"
parar_servidor

titulo "3.3 · Lo correcto: copiar también los roles (pg_dumpall --globals-only)"
pg_dumpall --globals-only -f /copias/roles.sql
grep -c "CREATE ROLE" /copias/roles.sql | sed 's/^/  roles en la copia: /'
nuevo_servidor
# Sin ON_ERROR_STOP aquí, a propósito: el superusuario «admin» ya existe en el servidor nuevo
# (lo crea initdb) y ese es el único error que se espera. Se enseña, no se esconde.
psql "${EN_NUEVO[@]}" -q -d postgres -f /copias/roles.sql 2>&1 | sed 's/^/  /'
psql "${EN_NUEVO[@]}" -d postgres -tAc "SELECT 'rol app: ' || CASE WHEN EXISTS (SELECT 1 FROM pg_roles WHERE rolname='app') THEN 'existe' ELSE 'NO EXISTE' END" | sed 's/^/  /'
psql "${EN_NUEVO[@]}" -q -c "CREATE DATABASE tienda" postgres
psql "${EN_NUEVO[@]}" -q -v ON_ERROR_STOP=1 -o /dev/null -d tienda -f /copias/tienda.sql
echo "  psql: código de salida $?"
echo "  dueño de la tabla: $(psql "${EN_NUEVO[@]}" -d tienda -tAc "SELECT tableowner FROM pg_tables WHERE tablename='pedidos'")"
parar_servidor
