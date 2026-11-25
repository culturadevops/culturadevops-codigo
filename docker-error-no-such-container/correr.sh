#!/bin/bash
# Demos del vídeo 694 de cultura-devops: «Error response from daemon: No such container».
# Cada causa real se provoca de verdad y se arregla. Regenera SALIDA.md. Corre desde Git Bash:
#   bash canales/cultura-devops/recursos/docker-error-no-such-container/correr.sh
# Disciplina Docker: nombres v694-*, --rm donde no estorba a la demo, compose down -v, y limpieza al salir.
set -u
export MSYS_NO_PATHCONV=1
cd "$(dirname "$0")"
AQUI=$(pwd)
NGX=nginx:1.29-alpine
ALP=alpine:3.24.3
DIND=docker:29.6.2-dind
TMP=$(mktemp -d)
DH=tcp://127.0.0.1:23750

limpiar() {
  docker rm -f v694-web v694-guardada v694-tarea >/dev/null 2>&1
  [ -d "$TMP/v694-tienda" ] && (cd "$TMP/v694-tienda" && docker compose down -v >/dev/null 2>&1)
  docker rm -f v694-dind >/dev/null 2>&1
  docker context rm -f v694-dind >/dev/null 2>&1
  rm -rf -- "$TMP"
}
trap limpiar EXIT

# R: imprime el comando como en una terminal y lo ejecuta (stderr incluido).
R() { echo "\$ $*"; eval "$*" 2>&1; }

demos() {
echo "### Versión"
R "docker version --format 'cliente {{.Client.Version}} · servidor {{.Server.Version}}'"
echo

echo "=================== A · Causa 1: el nombre o el ID no es ese ==================="
docker run -d --name v694-web $NGX >/dev/null
R "docker logs v694-wbe"
R "docker exec v694-wbe nginx -v"
R "docker stop v694-wbe"
echo "--- el arreglo: pregúntale a Docker cómo se llama de verdad (el filtro name busca por trozo)"
R "docker ps -a --filter name=web --format 'table {{.Names}}\t{{.Status}}'"
R "docker exec v694-web nginx -v"
echo "--- con el ID basta un prefijo único; un ID que no existe da el mismo error"
ID=$(docker inspect -f '{{.Id}}' v694-web)
R "docker inspect -f '{{.Name}}' ${ID:0:4}"
R "docker logs 0000aaaa"
echo "--- inspect lo dice distinto"
R "docker inspect v694-wbe"
echo

echo "=================== B · Detenido NO es borrado (otro error distinto) ==================="
R "docker stop v694-web"
R "docker ps --filter name=v694-web --format '{{.Names}} {{.Status}}'"
echo "(docker ps no lo muestra: solo enseña los que están corriendo)"
R "docker ps -a --filter name=v694-web --format '{{.Names}} {{.Status}}'"
R "docker exec v694-web nginx -v"
R "docker start v694-web"
R "docker exec v694-web nginx -v"
R "docker rm -f v694-web"
echo

echo "=================== C · Causa 2: --rm lo borró al terminar ==================="
R "docker run --rm --name v694-tarea $ALP sh -c 'echo migracion hecha; exit 3'; echo exit=\$?"
R "docker logs v694-tarea"
R "docker ps -a --filter name=v694-tarea --format '{{.Names}} {{.Status}}'"
echo "(nada: con --rm, al salir el contenedor se borra con sus logs y su código de salida)"
echo "--- el arreglo: si vas a querer los logs, sin --rm"
R "docker run --name v694-guardada $ALP sh -c 'echo migracion hecha; exit 3'; echo exit=\$?"
R "docker logs v694-guardada"
R "docker inspect -f 'ExitCode={{.State.ExitCode}}' v694-guardada"
R "docker rm v694-guardada"
echo "--- borrarlo dos veces: la segunda ya no existe"
R "docker rm v694-guardada"
R "docker rm -f v694-guardada; echo exit=\$?"
echo "(con -f el mensaje sale igual, pero el código es 0: útil en scripts de limpieza)"
echo

echo "=================== D · Causa 3: Docker Compose le pone prefijo al nombre ==================="
mkdir -p "$TMP/v694-tienda" "$TMP/otra-carpeta"
cat > "$TMP/v694-tienda/compose.yaml" <<'EOF'
services:
  web:
    image: nginx:1.29-alpine
EOF
cd "$TMP/v694-tienda"
R "cat compose.yaml"
R "docker compose up -d 2>&1 | tail -1"
R "docker exec web nginx -v"
R "docker ps --filter label=com.docker.compose.project=v694-tienda --format '{{.Names}}'"
echo "(nombre = proyecto-servicio-número; el proyecto, por defecto, es el nombre de la carpeta)"
echo "--- arreglo 1: hablarle a Compose por el nombre del servicio"
R "docker compose exec web nginx -v"
echo "--- arreglo 2: el nombre completo"
R "docker exec v694-tienda-web-1 nginx -v"
echo "--- pero docker compose exec fuera de la carpeta no encuentra el proyecto"
cd "$TMP/otra-carpeta"
R "docker compose exec web nginx -v"
R "docker compose -p v694-tienda exec web nginx -v"
cd "$TMP/v694-tienda"
echo
echo "=================== E · Causa 4: el ID cambió al recrear ==================="
ID=$(docker compose ps -q web)
echo "(guardé el ID: ${ID:0:12})"
R "docker compose up -d --force-recreate 2>&1 | tail -1"
R "docker logs ${ID:0:12}"
R "docker compose ps -q web | cut -c1-12"
echo "(recrear = borrar y crear otro: ID nuevo. Guarda el nombre, no el ID)"
R "docker compose down -v 2>&1 | tail -1"
cd "$AQUI"
echo

echo "=================== F · Causa 5: estás hablando con otro daemon ==================="
docker run -d --privileged --rm --name v694-dind -e DOCKER_TLS_CERTDIR= -p 127.0.0.1:23750:2375 $DIND >/dev/null
for i in $(seq 1 40); do docker -H $DH info >/dev/null 2>&1 && break; sleep 1; done
docker save $ALP | docker -H $DH load -q >/dev/null
echo "(un segundo daemon de Docker, en $DH: otra máquina, otro contexto)"
R "docker -H $DH run -d --name v694-api $ALP sleep 600 | cut -c1-12"
R "docker exec v694-api echo hola"
R "docker context show"
R "docker context create v694-dind --docker host=$DH"
R "docker context ls --format '{{.Name}}\t{{.DockerEndpoint}}' | grep -E 'default|desktop|v694'"
R "DOCKER_CONTEXT=v694-dind docker exec v694-api echo hola"
R "docker --context v694-dind ps --format '{{.Names}} {{.Status}}'"
R "DOCKER_HOST=$DH docker exec v694-api echo hola"
echo "(docker context use v694-dind lo deja fijo; aquí uso la variable para no cambiar el contexto de la máquina)"
}

{
  echo "# SALIDA · docker-error-no-such-container (vídeo 694, cultura-devops)"
  echo
  echo "Ejecutado el $(date +%F) con \`bash correr.sh\` desde Git Bash en Windows 11 + Docker Desktop. Imágenes: $NGX, $ALP, $DIND (el segundo daemon de la causa 5). Todo lo de abajo es la salida literal."
  echo
  echo '```'
  demos
  echo '```'
} > SALIDA.md
echo "SALIDA.md escrito"
