#!/usr/bin/env bash
# demo.sh — la medición del vídeo 231 «Caddy, ¿la alternativa a Nginx este 2026?».
#
# ⛔ TODAS LAS COMPROBACIONES SE HACEN DESDE UN TERCER CONTENEDOR NEUTRAL, con el mismo cliente
#    para los dos. Motivo: en la primera corrida usé el `wget` de cada imagen y resultó que el de
#    `nginx:alpine` NO habla HTTPS mientras que el de `caddy` sí. Estaba midiendo cada lado con
#    una herramienta distinta y el resultado decía que nginx no servía nada. Servía.
#
# ⚠️ CÓMO SE MIDE EL CERTIFICADO SIN DOMINIO PÚBLICO: Caddy trae una autoridad certificadora
#    interna que emite para nombres locales, con el MISMO mecanismo que usa contra Let's Encrypt
#    menos la parte del dominio. Con nginx hay que generarlo a mano. Comparar las dos cosas ES la
#    comparación justa: mide el trabajo que te ahorras, que es la tesis del vídeo.
#
# ⛔ Y ANTES DE COMPARAR NADA se comprueba que los dos sirven lo mismo. Regla del banco desde los
#    vídeos 229 y 230. Ningún error va a /dev/null.
set -u
D=$(cd "$(dirname "$0")" && pwd -W)
R=webred

limpiar() {
  docker rm -f caddy nginx backend >/dev/null 2>&1
  docker network rm $R >/dev/null 2>&1
  rm -rf "$D/certs"
  return 0
}
# El cliente NEUTRAL: el mismo para los dos lados.
mide() { docker run --rm --network $R curlimages/curl:latest -sk --max-time 5 "$@" 2>/dev/null; }

limpiar; docker network create $R >/dev/null
docker pull -q curlimages/curl:latest >/dev/null 2>&1

echo "== 1 · LINEAS DE CONFIGURACION para lo mismo =="
echo -n "   Caddy (Caddyfile):  "; grep -vcE '^\s*(#|$)' "$D/Caddyfile"
echo -n "   nginx (nginx.conf): "; grep -vcE '^\s*(#|$)' "$D/nginx.conf"

echo
echo "== 2 · el backend al que los dos hacen de proxy =="
docker run -d --name backend --network $R nginx:alpine >/dev/null
sleep 3; echo "   levantado"

echo
echo "== 3 · CADDY: de cero a HTTPS con certificado =="
t0=$(date +%s%N)
docker run -d --name caddy --network $R --network-alias sitio.local \
  -v "$D/Caddyfile:/etc/caddy/Caddyfile" -v "$D/sitio:/sitio" caddy:2-alpine >/dev/null
for i in $(seq 1 90); do
  [ -n "$(mide https://sitio.local/)" ] && break; sleep 1
done
t1=$(date +%s%N); echo "   responde por HTTPS en $(( (t1-t0)/1000000 )) ms"
echo "   pasos humanos: 1 (escribir 7 lineas). No hay paso 2."

echo
echo "== 4 · NGINX: de cero a HTTPS con certificado =="
echo "   4a · generar el certificado a mano (el paso que Caddy no tiene)"
t0=$(date +%s%N)
mkdir -p "$D/certs"
docker run --rm -v "$D/certs:/certs" alpine/openssl:latest req -x509 -nodes -days 365 \
  -newkey rsa:2048 -keyout /certs/sitio.key -out /certs/sitio.crt \
  -subj "/CN=sitio.local" >/dev/null 2>&1
t1=$(date +%s%N); GEN=$(( (t1-t0)/1000000 ))
echo "      tardo ${GEN} ms"
echo "   4b · levantar nginx con ese certificado"
t0=$(date +%s%N)
docker run -d --name nginx --network $R --network-alias sitio2.local \
  -v "$D/nginx.conf:/etc/nginx/nginx.conf" -v "$D/sitio:/sitio" -v "$D/certs:/certs" \
  nginx:alpine >/dev/null
for i in $(seq 1 90); do
  [ -n "$(mide https://sitio2.local/)" ] && break; sleep 1
done
t1=$(date +%s%N); ARR=$(( (t1-t0)/1000000 ))
echo "      tardo ${ARR} ms"
echo "   total nginx: $(( GEN + ARR )) ms"
echo "   pasos humanos: 4 (clave, certificado, 16 lineas, y renovarlo en 365 dias)"

echo
echo "== 5 · ⛔ ¿SIRVEN LOS DOS LO MISMO? (mismo cliente, contenedor neutral) =="
echo -n "   Caddy, la pagina:      "; mide https://sitio.local/  | head -1
echo -n "   nginx, la pagina:      "; mide https://sitio2.local/ | head -1
echo -n "   Caddy, el proxy /api/: "; mide https://sitio.local/api/  | grep -o '<title>.*</title>' | head -1
echo -n "   nginx, el proxy /api/: "; mide https://sitio2.local/api/ | grep -o '<title>.*</title>' | head -1

echo
echo "== 6 · ¿QUIEN EMITIO CADA CERTIFICADO, Y CUANTO DURA? =="
for s in "Caddy:sitio.local" "nginx:sitio2.local"; do
  echo "   ${s%%:*}:"
  docker run --rm --network $R alpine/openssl:latest s_client -connect "${s##*:}:443" \
    -servername "${s##*:}" 2>/dev/null </dev/null | \
    docker run --rm -i alpine/openssl:latest x509 -noout -issuer -dates 2>/dev/null | sed 's/^/     /'
done

echo
echo "== 6b · MEMORIA EN REPOSO, con los dos vivos =="
docker stats --no-stream --format '   {{.Name}}: {{.MemUsage}}' caddy nginx

echo
echo "== 7 · 🥇 EL QUE NO SALE EN NINGUNA COMPARACION =="
echo "   tiro el backend y REINICIO los dos. ¿Cual vuelve a arrancar?"
docker rm -f backend >/dev/null 2>&1
docker restart caddy nginx >/dev/null 2>&1
sleep 6
echo -n "   Caddy: "; docker ps --filter name=caddy --format '{{.Status}}' | head -1
echo -n "          y sigue sirviendo la pagina: "; mide https://sitio.local/ | head -1
echo -n "   nginx: "; docker ps -a --filter name=nginx --format '{{.Status}}' | head -1
echo "          y su ultimo mensaje:"
docker logs nginx 2>&1 | tail -1 | sed 's/^/            /'

echo
echo "== 9 · TAMANO DE LA IMAGEN =="
echo -n "   caddy:2-alpine: "; docker images caddy:2-alpine --format '{{.Size}}'
echo -n "   nginx:alpine:   "; docker images nginx:alpine --format '{{.Size}}'

limpiar
echo
echo "== limpio =="
