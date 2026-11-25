#!/bin/sh
# Lección 1 · Escuchar en 127.0.0.1 o en 0.0.0.0: el «en mi máquina sí» más famoso.
#
# La aplicación escucha en 127.0.0.1, que es lo que trae por defecto media docena de frameworks
# «por seguridad». En tu portátil funciona. En el contenedor, publicas el puerto con -p y desde
# fuera... respuesta vacía. Docker reenvía al contenedor, pero dentro nadie escucha en esa
# dirección: 127.0.0.1 del contenedor es SOLO el contenedor.
. /curso/comun.sh
limpiar

titulo "1.1 · Dentro del contenedor, todo bien"
docker run -d --name red-app -p 18001:8000 $IMG python3 -m http.server 8000 --bind 127.0.0.1 >/dev/null
esperar_puerto red-app 8000
echo "  curl desde DENTRO:  HTTP $(docker exec red-app curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/)"
echo "  escuchando en:      $(docker exec red-app ss -ltnH | awk '{print $4}')"

titulo "1.2 · Desde fuera, con el puerto publicado"
echo "  docker port:        $(docker port red-app 8000 | head -1)"
echo "  curl desde FUERA:   $(desde_fuera 18001)"

titulo "1.3 · Lo correcto: escuchar en 0.0.0.0 (todas las interfaces DEL CONTENEDOR)"
docker rm -f red-app >/dev/null
docker run -d --name red-app -p 18001:8000 $IMG python3 -m http.server 8000 --bind 0.0.0.0 >/dev/null
esperar_puerto red-app 8000
echo "  escuchando en:      $(docker exec red-app ss -ltnH | awk '{print $4}')"
echo "  curl desde FUERA:   $(desde_fuera 18001)"

titulo "1.4 · Y la otra cara: -p 18001:8000 publica en TODAS las interfaces de la máquina"
echo "  -p 18001:8000            -> $(docker port red-app 8000 | head -1)"
docker rm -f red-app >/dev/null
docker run -d --name red-app -p 127.0.0.1:18001:8000 $IMG python3 -m http.server 8000 --bind 0.0.0.0 >/dev/null
echo "  -p 127.0.0.1:18001:8000  -> $(docker port red-app 8000 | head -1)"
limpiar
