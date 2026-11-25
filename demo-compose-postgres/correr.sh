#!/bin/bash
# Demo de «Docker Compose con PostgreSQL» (cultura-devops, 2026-10-20). Corre desde Git Bash, dentro de esta carpeta.
# Proyecto de Compose propio (demopg / demoviejo): solo crea y borra SUS contenedores y SUS volúmenes.
set -u
export COMPOSE_PROJECT_NAME=demopg
dc() { docker compose --progress quiet "$@" 2>&1; }

echo "### 1 · El compose de los tutoriales viejos, con postgres:18"
echo "\$ cat compose-tutorial-viejo.yaml"
grep -v '^#' compose-tutorial-viejo.yaml
echo "\$ docker compose -f compose-tutorial-viejo.yaml up -d"
docker compose -p demoviejo --progress quiet -f compose-tutorial-viejo.yaml up -d 2>&1
sleep 8
echo "\$ docker compose -f compose-tutorial-viejo.yaml ps -a"
docker compose -p demoviejo -f compose-tutorial-viejo.yaml ps -a --format 'table {{.Service}}\t{{.Status}}' 2>&1
echo "\$ docker compose -f compose-tutorial-viejo.yaml logs db"
docker compose -p demoviejo -f compose-tutorial-viejo.yaml logs --no-log-prefix db 2>&1 | grep -v '^\s*$' | head -14
docker compose -p demoviejo -f compose-tutorial-viejo.yaml down -v >/dev/null 2>&1

echo
echo "### 2 · El compose bueno"
echo "\$ cat compose.yaml"
cat compose.yaml
echo "\$ cat initdb/01-tablas.sql"
cat initdb/01-tablas.sql

echo
echo "### 3 · Levantar: la app espera a que la base esté sana"
echo "\$ docker compose up -d --wait db"
dc up -d --wait db
echo "\$ docker compose ps"
docker compose ps --format 'table {{.Service}}\t{{.Status}}\t{{.Ports}}' 2>&1
echo "\$ docker compose run --rm app"
dc run --rm app

echo
echo "### 4 · ¿Los datos sobreviven a down?"
echo "\$ docker compose exec db psql -U tienda -c \"INSERT INTO productos (nombre, precio) VALUES ('audifonos', 40.00);\""
dc exec db psql -U tienda -c "INSERT INTO productos (nombre, precio) VALUES ('audifonos', 40.00);"
echo "\$ docker compose down"
dc down
echo "\$ docker compose up -d --wait db && docker compose run --rm app"
dc up -d --wait db
dc run --rm app
echo "\$ docker volume ls --filter name=demopg"
docker volume ls --filter name=demopg 2>&1

echo
echo "### 5 · Cambiar la clave en el compose NO cambia la clave de la base"
echo "\$ CLAVE_DB=clave2 docker compose up -d --wait db"
CLAVE_DB=clave2 dc up -d --wait db
echo "\$ CLAVE_DB=clave2 docker compose run --rm app"
CLAVE_DB=clave2 dc run --rm app
echo "\$ docker compose exec db psql -U tienda -c \"ALTER USER tienda PASSWORD 'clave2';\""
dc exec db psql -U tienda -c "ALTER USER tienda PASSWORD 'clave2';"
echo "\$ CLAVE_DB=clave2 docker compose run --rm app"
CLAVE_DB=clave2 dc run --rm app

echo
echo "### 6 · Respaldo con pg_dump"
echo "\$ docker compose exec db pg_dump -U tienda tienda > respaldo.sql"
docker compose exec -T db pg_dump -U tienda tienda > respaldo.sql 2>/dev/null
echo "\$ grep -A5 'COPY public.productos' respaldo.sql"
grep -A5 'COPY public.productos' respaldo.sql

echo
echo "### 7 · down -v borra el volumen: los datos se van"
echo "\$ docker compose down -v"
dc down -v
echo "\$ docker compose up -d --wait db && docker compose run --rm app"
CLAVE_DB=clave2 dc up -d --wait db
CLAVE_DB=clave2 dc run --rm app
echo "\$ docker compose exec db psql -U tienda -c \"SELECT nombre FROM productos ORDER BY id;\""
dc exec db psql -U tienda -c "SELECT nombre FROM productos ORDER BY id;"
CLAVE_DB=clave2 dc down -v >/dev/null
rm -f respaldo.sql
