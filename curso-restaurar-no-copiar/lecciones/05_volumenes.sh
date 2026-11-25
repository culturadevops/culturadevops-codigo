#!/bin/sh
# Lección 5 · Los volúmenes de Docker: donde está lo que crees que está en la base de datos.
#
# Corre en el contenedor docker:cli con el socket de Docker montado (ver ejecutar_todo.py): habla
# con el Docker de la máquina, como lo harías tú.
#
# Trampas que no dan error:
#   - «Hice una copia del contenedor» (docker commit): la imagen NO lleva los volúmenes.
#   - docker compose down -v: la -v borra los volúmenes con nombre. Sin preguntar.
# Lo correcto: copiar el VOLUMEN, con el servicio parado, y probar a levantarlo.
set -u
P="curso-vol"
titulo() { printf '\n== %s ==\n' "$1"; }
pg_listo() { until docker exec "$1" pg_isready -U admin -d tienda -q 2>/dev/null && docker exec "$1" psql -U admin -d tienda -tAc 'select 1' >/dev/null 2>&1; do sleep 0.5; done; }
pedidos() { docker exec "$1" psql -U admin -d tienda -tAc "SELECT count(*) FROM pedidos" 2>&1 | head -1; }
limpiar() {
  docker rm -f "$P-app" "$P-copia" "$P-vuelta" >/dev/null 2>&1
  docker volume rm -f "$P-datos" "$P-datos2" "$P-datos3" "$P-copias" >/dev/null 2>&1
  docker image rm -f "$P-imagen" >/dev/null 2>&1
}
limpiar

# La aplicación: un Postgres con sus datos en un volumen con nombre, como en cualquier compose.
docker run -d --name "$P-app" -e POSTGRES_USER=admin -e POSTGRES_PASSWORD=admin -e POSTGRES_DB=tienda \
  -v "$P-datos:/var/lib/postgresql/data" postgres:17 >/dev/null
pg_listo "$P-app"
docker exec "$P-app" psql -q -U admin -d tienda -c \
  "CREATE TABLE pedidos AS SELECT g AS id, 'cliente-' || g AS cliente FROM generate_series(1, 1000) g"
echo "  la aplicación tiene $(pedidos "$P-app") pedidos"

titulo "5.1 · La trampa: «copio el contenedor» con docker commit"
docker commit "$P-app" "$P-imagen" >/dev/null && echo "  docker commit: hecho, imagen $P-imagen"
docker rm -f "$P-app" >/dev/null && docker volume rm "$P-datos" >/dev/null
echo "  (el desastre: se pierden el contenedor y su volumen)"
docker run -d --name "$P-copia" -v "$P-datos2:/var/lib/postgresql/data" "$P-imagen" >/dev/null
pg_listo "$P-copia"
echo "  levantado desde la imagen copiada -> pedidos: $(pedidos "$P-copia")"
docker image inspect "$P-imagen" --format '  la imagen declara el volumen {{range $k, $v := .Config.Volumes}}{{$k}}{{end}}: su contenido no viaja en ella'
docker rm -f "$P-copia" >/dev/null

titulo "5.2 · La otra trampa: docker compose down -v"
mkdir -p /tmp/demo && cat > /tmp/demo/compose.yml <<'YML'
services:
  db:
    image: postgres:17
    environment: {POSTGRES_USER: admin, POSTGRES_PASSWORD: admin, POSTGRES_DB: tienda}
    volumes: [datos:/var/lib/postgresql/data]
volumes:
  datos:
YML
docker compose -p "$P-demo" -f /tmp/demo/compose.yml up -d >/dev/null 2>&1
echo "  volúmenes antes:  $(docker volume ls -q --filter name=$P-demo | tr '\n' ' ')"
docker compose -p "$P-demo" -f /tmp/demo/compose.yml down >/dev/null 2>&1
echo "  tras «down»:      $(docker volume ls -q --filter name=$P-demo | tr '\n' ' ')"
docker compose -p "$P-demo" -f /tmp/demo/compose.yml down -v >/dev/null 2>&1
echo "  tras «down -v»:   $(docker volume ls -q --filter name=$P-demo | tr '\n' ' ')(ninguno, y sin preguntar)"

titulo "5.3 · Lo correcto: copiar el volumen, con la base de datos parada"
docker run -d --name "$P-app" -e POSTGRES_USER=admin -e POSTGRES_PASSWORD=admin -e POSTGRES_DB=tienda \
  -v "$P-datos:/var/lib/postgresql/data" postgres:17 >/dev/null
pg_listo "$P-app"
docker exec "$P-app" psql -q -U admin -d tienda -c \
  "CREATE TABLE pedidos AS SELECT g AS id, 'cliente-' || g AS cliente FROM generate_series(1, 1000) g"
t0=$(awk '{print int($1*1000)}' /proc/uptime)
docker stop "$P-app" >/dev/null
docker run --rm -v "$P-datos:/datos:ro" -v "$P-copias:/copia" alpine tar czf /copia/volumen.tgz -C /datos .
docker start "$P-app" >/dev/null
pg_listo "$P-app"
t1=$(awk '{print int($1*1000)}' /proc/uptime)
echo "  copia del volumen: $(( $(docker run --rm -v "$P-copias:/c" alpine stat -c %s /c/volumen.tgz) / 1024 )) KB · servicio parado: $((t1 - t0)) ms"
docker rm -f "$P-app" >/dev/null && docker volume rm "$P-datos" >/dev/null
echo "  (el mismo desastre)"
docker volume create "$P-datos3" >/dev/null
docker run --rm -v "$P-datos3:/datos" -v "$P-copias:/copia" alpine tar xzf /copia/volumen.tgz -C /datos
docker run -d --name "$P-vuelta" -v "$P-datos3:/var/lib/postgresql/data" postgres:17 >/dev/null
pg_listo "$P-vuelta"
echo "  levantado desde la copia del volumen -> pedidos: $(pedidos "$P-vuelta")"
limpiar
