#!/bin/sh
# Lección 3 · El DNS que resolvía a lo viejo.
#
# nginx con `proxy_pass http://backend:8000;` resuelve «backend» UNA vez, al arrancar, y se queda
# esa IP para siempre. Redespliegas el backend, cambia de IP, y nginx sigue mandando al sitio
# viejo. Si esa IP la ha cogido OTRO servicio, nginx le manda tus peticiones a él. Con un 200.
. /curso/comun.sh
limpiar
docker network create --subnet 10.77.0.0/24 red-c >/dev/null

servicio() { # nombre texto [ip]
  ip=${3:+--ip $3}
  # shellcheck disable=SC2086
  docker run -d --name "$1" --network red-c $ip $IMG \
    sh -c "mkdir -p /w && echo '$2' > /w/index.html && exec python3 -m http.server 8000 -d /w" >/dev/null
}
proxy() { # nombre config
  docker run -d --name "$1" --network red-c $IMG sh -c "printf '%s\n' '$2' > /etc/nginx/conf.d/p.conf && exec nginx -g 'daemon off;'" >/dev/null
}
pedir() { docker exec "$1" curl -s -m 3 http://127.0.0.1/ || echo "(sin respuesta)"; }
ip_de() { docker inspect -f '{{(index .NetworkSettings.Networks "red-c").IPAddress}}' "$1"; }

servicio red-backend "soy el backend v1" 10.77.0.10
sleep 1
proxy red-nginx-fijo 'server { listen 80; location / { proxy_pass http://red-backend:8000; } }'
proxy red-nginx-dinamico 'server { listen 80; resolver 127.0.0.11 valid=2s; set $b red-backend; location / { proxy_pass http://$b:8000; } }'
sleep 2

titulo "3.1 · Todo bien: los dos nginx llegan al backend"
echo "  red-backend está en $(ip_de red-backend)"
echo "  nginx (proxy_pass fijo):     $(pedir red-nginx-fijo)"
echo "  nginx (resolver + variable): $(pedir red-nginx-dinamico)"

titulo "3.2 · Se redespliega el backend, y otro servicio coge su IP vieja"
docker rm -f red-backend >/dev/null
servicio red-facturas "soy FACTURAS, otro servicio" 10.77.0.10
servicio red-backend "soy el backend v2"
sleep 3
echo "  red-backend (v2) está ahora en $(ip_de red-backend) · en $(ip_de red-facturas) está red-facturas"
echo "  nginx (proxy_pass fijo):     $(pedir red-nginx-fijo)   <- HTTP $(docker exec red-nginx-fijo curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1/)"
echo "  nginx (resolver + variable): $(pedir red-nginx-dinamico)"
echo "  getent hosts red-backend:    $(docker exec red-nginx-fijo getent hosts red-backend)"

titulo "3.3 · Lo que dice el DNS de Docker, con su TTL"
docker exec red-nginx-fijo dig +noall +answer red-backend @127.0.0.11 | sed 's/^/  /'
limpiar
