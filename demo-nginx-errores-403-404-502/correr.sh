#!/bin/bash
# Demo de «Nginx: errores 403, 404 y 502 y cómo arreglarlos» (cultura-devops, 2026-10-23). Corre desde Git Bash, lo llama ejecutar.sh.
# Contenedores en una red propia: «web» (nginx), «app» (un backend en Python) y «cliente» (curl). Nada toca tu máquina.
set -u
W() { docker exec web "$@" 2>&1; }
codigo() { docker exec cliente curl -s -o /dev/null -w "%{http_code}\n" "http://web$1"; }
log() { W tail -n "${1:-1}" /var/log/nginx/demo-error.log | sed -E 's/^[0-9\/]+ [0-9:]+ //'; }
conf() { docker cp "conf/$1" web:/etc/nginx/conf.d/default.conf >/dev/null; W nginx -t >/dev/null && W nginx -s reload >/dev/null; sleep 1; }

conf base.conf
echo "### 0 · La configuración de partida"
echo "web\$ cat /etc/nginx/conf.d/default.conf"
W cat /etc/nginx/conf.d/default.conf
echo "web\$ nginx -t"
W nginx -t
echo "\$ curl -s -o /dev/null -w '%{http_code}' http://web/"
codigo /

echo
echo "### 1 · 403: una carpeta sin index.html"
W mkdir -p /usr/share/nginx/html/docs
W sh -c "echo 'manual' > /usr/share/nginx/html/docs/manual.txt"
echo "web\$ ls /usr/share/nginx/html/docs/"
W ls /usr/share/nginx/html/docs/
echo "\$ curl http://web/docs/"
codigo /docs/
echo "web\$ tail -n 1 /var/log/nginx/demo-error.log"
log
echo "web\$ echo '<h1>Docs</h1>' > /usr/share/nginx/html/docs/index.html"
W sh -c "echo '<h1>Docs</h1>' > /usr/share/nginx/html/docs/index.html"
echo "\$ curl http://web/docs/"
codigo /docs/

echo
echo "### 2 · 403: un archivo que nginx no puede leer"
W sh -c "echo '<h1>Reporte</h1>' > /usr/share/nginx/html/reporte.html && chmod 600 /usr/share/nginx/html/reporte.html"
echo "web\$ ls -l /usr/share/nginx/html/reporte.html"
W ls -l /usr/share/nginx/html/reporte.html
echo "\$ curl http://web/reporte.html"
codigo /reporte.html
echo "web\$ tail -n 1 /var/log/nginx/demo-error.log"
log
echo "web\$ ps -o user,args | grep 'nginx: '"
W sh -c "ps -o user,args | grep 'nginx: ' | grep -v grep | sort -u"
echo "web\$ chmod 644 /usr/share/nginx/html/reporte.html"
W chmod 644 /usr/share/nginx/html/reporte.html
echo "\$ curl http://web/reporte.html"
codigo /reporte.html

echo
echo "### 3 · 403: la carpeta, no el archivo"
W sh -c "mkdir -p /usr/share/nginx/html/privado && echo hola > /usr/share/nginx/html/privado/hola.html && chmod 644 /usr/share/nginx/html/privado/hola.html && chmod 700 /usr/share/nginx/html/privado"
echo "web\$ ls -ld /usr/share/nginx/html/privado; ls -l /usr/share/nginx/html/privado/hola.html"
W ls -ld /usr/share/nginx/html/privado
W ls -l /usr/share/nginx/html/privado/hola.html
echo "\$ curl http://web/privado/hola.html"
codigo /privado/hola.html
echo "web\$ tail -n 1 /var/log/nginx/demo-error.log"
log
echo "web\$ chmod 755 /usr/share/nginx/html/privado"
W chmod 755 /usr/share/nginx/html/privado
echo "\$ curl http://web/privado/hola.html"
codigo /privado/hola.html

echo
echo "### 4 · 404: el root mal escrito"
conf root-mal.conf
echo "web\$ grep root /etc/nginx/conf.d/default.conf"
W grep root /etc/nginx/conf.d/default.conf
echo "web\$ nginx -t"
W nginx -t
echo "\$ curl http://web/"
codigo /
echo "web\$ tail -n 1 /var/log/nginx/demo-error.log"
log
conf base.conf
echo "(root corregido a /usr/share/nginx/html)"
echo "\$ curl http://web/"
codigo /

echo
echo "### 5 · 404: una aplicación de una sola página (SPA)"
echo "\$ curl http://web/                 # la portada de la SPA"
codigo /
echo "\$ curl http://web/panel/usuarios   # una ruta que existe en JavaScript, no en el disco"
codigo /panel/usuarios
echo "web\$ tail -n 1 /var/log/nginx/demo-error.log"
log
conf spa.conf
echo "web\$ grep try_files /etc/nginx/conf.d/default.conf"
W grep try_files /etc/nginx/conf.d/default.conf
echo "\$ curl http://web/panel/usuarios"
codigo /panel/usuarios
echo "\$ curl http://web/no-existe.png   # ojo: con este try_files todo devuelve 200"
codigo /no-existe.png
conf spa-assets.conf
echo "web\$ grep -A2 'location' /etc/nginx/conf.d/default.conf | grep -v '^--'"
W sh -c "grep -A2 'location' /etc/nginx/conf.d/default.conf | grep -v '^--'"
echo "\$ curl http://web/panel/usuarios ; curl http://web/assets/no-existe.png"
codigo /panel/usuarios
codigo /assets/no-existe.png

echo
echo "### 6 · 502: el backend está caído"
conf spa-assets.conf
docker exec -d app python -m http.server 8080 --directory /srv
sleep 2
echo "\$ curl http://web/api/   # con el backend arriba"
codigo /api/
docker exec app pkill -f http.server
sleep 1
echo "(paro el backend)"
echo "\$ curl http://web/api/"
codigo /api/
echo "web\$ tail -n 1 /var/log/nginx/demo-error.log"
log
echo "web\$ curl -s -o /dev/null -w '%{http_code}' http://app:8080/   # ¿responde el backend desde nginx?"
W sh -c "curl -s -m 3 -o /dev/null -w '%{http_code}\n' http://app:8080/ || echo \"curl salió con código \$?\""

echo
echo "### 7 · 502: el puerto equivocado"
docker exec -d app python -m http.server 8080 --directory /srv
sleep 2
conf proxy-puerto-mal.conf
echo "web\$ grep proxy_pass /etc/nginx/conf.d/default.conf"
W grep proxy_pass /etc/nginx/conf.d/default.conf
echo "\$ curl http://web/api/"
codigo /api/
echo "web\$ tail -n 1 /var/log/nginx/demo-error.log"
log
conf spa-assets.conf
echo "(proxy_pass corregido a http://app:8080/)"
echo "\$ curl http://web/api/"
codigo /api/

echo
echo "### 8 · nginx -t antes de recargar"
echo "(a la config le falta el ; al final de proxy_pass)"
docker cp conf/sin-punto-y-coma.conf web:/tmp/prueba.conf >/dev/null
W cp /etc/nginx/conf.d/default.conf /tmp/bueno.conf
W cp /tmp/prueba.conf /etc/nginx/conf.d/default.conf
echo "web\$ nginx -t"
W nginx -t
W cp /tmp/bueno.conf /etc/nginx/conf.d/default.conf
echo "web\$ nginx -t   # con la configuración buena"
W nginx -t

echo
echo "### 9 · Dónde está el log en la imagen oficial de Docker"
echo "web\$ ls -l /var/log/nginx/"
W ls -l /var/log/nginx/
