#!/bin/bash
# Demo del vídeo 798 (cultura-devops): respaldo de Postgres a S3 con Python. Corre en Git Bash; crea y borra
# SOLO lo suyo: contenedores y red cd798-*, etiqueta demo=cd798. Todos con --rm y --cpus 1.
# Sin cronómetro a propósito: se mide memoria pico (ru_maxrss del proceso de Python) y tamaños, no tiempos.
#   bash canales/cultura-devops/recursos/pruebas-respaldo-postgres-s3-python/correr.sh > SALIDA-crudo.txt
cd "$(dirname "$0")" || exit 1
export MSYS_NO_PATHCONV=1
RED=cd798-red
ET="--label demo=cd798"
PG=postgres:18.6-alpine

limpiar() {
  docker rm -f -v cd798-origen cd798-destino cd798-moto >/dev/null 2>&1
  docker network rm $RED >/dev/null 2>&1
}
limpiar
docker network create $ET $RED >/dev/null
for c in cd798-origen cd798-destino; do
  docker run -d --rm --cpus 1 $ET --name $c --network $RED -e POSTGRES_PASSWORD=demo $PG >/dev/null
done
docker run -d --rm --cpus 1 $ET --name cd798-moto --network $RED motoserver/moto:latest >/dev/null
for c in cd798-origen cd798-destino; do
  until docker exec $c pg_isready -U postgres -q 2>/dev/null; do sleep 1; done
done
sleep 3
docker build -q -t cd798-respaldo . >/dev/null || exit 1

job() {
  docker run --rm --cpus 1 $ET --network $RED \
    -e PGHOST=cd798-origen -e PGHOST_DESTINO=cd798-destino -e PGUSER=postgres -e PGPASSWORD=demo \
    -e AWS_ENDPOINT_URL=http://cd798-moto:5000 -e AWS_REGION=us-east-1 \
    -e AWS_ACCESS_KEY_ID=test -e AWS_SECRET_ACCESS_KEY=test -e BUCKET=respaldos-demo \
    cd798-respaldo sh -c "$1"
}
paso() { echo; echo "\$ $1"; job "$1" 2>&1; echo "(código de salida: $?)"; }

echo "== versiones"
job 'pg_dump --version; psql --version; python3 --version; python3 -c "import boto3; print(\"boto3\", boto3.__version__)"' 2>&1
docker exec cd798-moto python -c "import moto; print('moto', moto.__version__)" 2>&1
echo "contenedores con --cpus 1"

echo; echo "== datos de origen (semilla.sql)"
docker exec -i cd798-origen psql -q -U postgres < semilla.sql >/dev/null
docker exec cd798-origen psql -At -U postgres -d tienda -c "SELECT 'clientes ' || (SELECT count(*) FROM clientes) || ' · pedidos ' || (SELECT count(*) FROM pedidos) || ' · tamaño de la base tienda: ' || pg_size_pretty(pg_database_size('tienda'))"

paso 'respaldo bucket'

echo; echo "== 1. streaming: pg_dump -Fc directo a S3 por partes (y la variante sin compresión de pg_dump + gzip en Python)"
paso 'respaldo respaldar --fecha 2026-11-05T0300 --modo fc'
paso 'respaldo respaldar --fecha 2026-11-05T0301 --modo z0+gzip'
paso 'respaldo respaldar --fecha 2026-11-05T0304 --modo z0+gzip-corto'
paso 'respaldo restaurar --clave respaldos/tienda/2026-11-05T0304.dump.gz'

echo; echo "== 2. el ingenuo: todo el pg_dump a memoria y después put_object"
paso 'respaldo ingenuo --fecha 2026-11-05T0302'

echo; echo "== 3a. pg_dump falla al empezar (la base no existe)"
paso 'respaldo sin-wait --base no_existe --fecha 2026-11-05T0400'
paso 'respaldo respaldar --base no_existe --fecha 2026-11-05T0401'
paso 'respaldo listar --base no_existe'

echo; echo "== 3b. pg_dump muere a la mitad (se corta su conexión a los 2 s)"
CORTE='(sleep 2; psql -qAt -d tienda -c "SELECT count(pg_terminate_backend(pid)) || '"'"' conexión de pg_dump cortada'"'"' FROM pg_stat_activity WHERE application_name = '"'"'pg_dump'"'"'") & '
paso "${CORTE}respaldo sin-wait --fecha 2026-11-05T0402; rc=\$?; wait; exit \$rc"
paso "${CORTE}respaldo respaldar --fecha 2026-11-05T0403; rc=\$?; wait; exit \$rc"
paso 'respaldo listar'
paso 'respaldo restaurar --clave respaldos/tienda/2026-11-05T0402.dump'

echo; echo "== 4. retención: 12 respaldos de inventario repartidos en 10 días"
for f in 2026-10-27T0300 2026-10-28T0300 2026-10-29T0300 2026-10-30T0300 2026-10-31T0300 2026-11-01T0300 \
         2026-11-02T0300 2026-11-02T1500 2026-11-03T0300 2026-11-04T0300 2026-11-05T0300 2026-11-05T1500; do
  job "respaldo respaldar --base inventario --fecha $f" >/dev/null 2>&1
done
paso 'respaldo listar --base inventario'
paso 'respaldo retener --base inventario --ultimos 3 --dias 7'
paso 'respaldo retener --base inventario --ultimos 3 --dias 7 --borrar'
paso 'respaldo listar --base inventario'

echo; echo "== 5. el doble de datos: memoria con streaming y con el ingenuo"
docker exec cd798-origen psql -q -U postgres -d tienda -c "INSERT INTO pedidos SELECT g, 1 + (g % 50000), round((random() * 500)::numeric, 2), timestamptz '2026-01-01' + g * interval '7 seconds', md5(g::text) || md5((g * 7)::text) FROM generate_series(2000001, 4000000) g" >/dev/null
docker exec cd798-origen psql -At -U postgres -d tienda -c "SELECT 'pedidos: ' || count(*) || ' · tamaño de la base: ' || pg_size_pretty(pg_database_size('tienda')) FROM pedidos"
paso 'respaldo respaldar --fecha 2026-11-05T0500 --modo fc'
paso 'respaldo respaldar --fecha 2026-11-05T0501 --modo z0+gzip'
paso 'respaldo ingenuo --fecha 2026-11-05T0502'

echo; echo "== 6. el respaldo solo vale si restaura: a una base nueva, y se compara"
paso 'respaldo restaurar --clave respaldos/tienda/2026-11-05T0500.dump'
paso 'respaldo verificar'
paso 'respaldo restaurar --clave respaldos/tienda/2026-11-05T0501.dump.gz'
paso 'respaldo verificar'

limpiar
echo; echo "== limpieza: contenedores y red cd798-* borrados"
