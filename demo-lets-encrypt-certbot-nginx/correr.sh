#!/bin/bash
# Demo de «Certificado SSL gratis con Let's Encrypt (certbot + nginx)» (cultura-devops, 2026-10-23). Lo llama ejecutar.sh.
# «pebble» = la CA de PRUEBA oficial de Let's Encrypt (habla el mismo protocolo, ACME). «web» = Debian + nginx + certbot.
# «cliente» = un navegador de mentira (curl) que solo confía en la raíz de Pebble. Nada sale a internet.
set -u
W() { docker exec web "$@" 2>&1; }
CL() { docker exec cliente "$@" 2>&1; }
SERVER="https://pebble:14000/dir"

echo "### 1 · Antes: el sitio solo tiene HTTP"
echo "web\$ cat /etc/nginx/sites-available/tienda"
W cat /etc/nginx/sites-available/tienda
echo "\$ curl -s http://tienda.example.com/"
CL curl -s http://tienda.example.com/
echo "\$ curl https://tienda.example.com/"
CL curl -sS -m 5 https://tienda.example.com/

echo
echo "### 2 · certbot --nginx"
echo "web\$ certbot --version"
W certbot --version
W cp /etc/nginx/sites-available/tienda /tmp/tienda.antes
echo "web\$ certbot --nginx -d tienda.example.com -m admin@example.com --agree-tos --no-eff-email --redirect -n --server $SERVER"
docker exec -e REQUESTS_CA_BUNDLE=/pebble.minica.pem web certbot --nginx -d tienda.example.com -m admin@example.com --agree-tos \
  --no-eff-email --redirect -n --server "$SERVER" 2>&1

echo
echo "### 3 · Lo que certbot le cambió a la configuración de nginx"
echo "web\$ diff /tmp/tienda.antes /etc/nginx/sites-available/tienda"
W diff /tmp/tienda.antes /etc/nginx/sites-available/tienda
echo "web\$ nginx -t"
W nginx -t

echo
echo "### 4 · Después: HTTP redirige y HTTPS funciona"
echo "\$ curl -sI http://tienda.example.com/ | head -3"
CL sh -c "curl -sI http://tienda.example.com/ | head -3 | tr -d '\r'"
echo "\$ curl -s https://tienda.example.com/   # el cliente confía en la raíz de Pebble"
CL curl -s --cacert /pebble-raiz.pem https://tienda.example.com/
echo "\$ curl https://tienda.example.com/   # un cliente que NO confía en Pebble"
CL sh -c "curl -sS https://tienda.example.com/ 2>&1 | head -1"

echo
echo "### 5 · El certificado"
echo "web\$ ls /etc/letsencrypt/live/tienda.example.com/"
W ls /etc/letsencrypt/live/tienda.example.com/
echo "web\$ openssl x509 -in /etc/letsencrypt/live/tienda.example.com/cert.pem -noout -subject -issuer -dates -ext subjectAltName"
W openssl x509 -in /etc/letsencrypt/live/tienda.example.com/cert.pem -noout -subject -issuer -dates -ext subjectAltName
echo "web\$ certbot certificates"
docker exec -e REQUESTS_CA_BUNDLE=/pebble.minica.pem web certbot certificates 2>&1 | grep -vE "^Saving debug log|^- - - -|^$"

echo
echo "### 6 · La renovación: certbot renew --dry-run"
echo "web\$ certbot renew --dry-run --no-random-sleep-on-renew   # el ensayo va SIEMPRE al staging de Let's Encrypt (y esta red no tiene internet)"
docker exec -e REQUESTS_CA_BUNDLE=/pebble.minica.pem web certbot renew --dry-run --no-random-sleep-on-renew 2>&1 | grep -vE "^Saving debug log|^- - - -|^$"
echo "web\$ certbot renew --dry-run --no-random-sleep-on-renew --server $SERVER   # el ensayo, contra la CA de prueba"
docker exec -e REQUESTS_CA_BUNDLE=/pebble.minica.pem web certbot renew --dry-run --no-random-sleep-on-renew --server "$SERVER" 2>&1 | grep -vE "^Saving debug log|^- - - -|^$"
echo "web\$ certbot renew --no-random-sleep-on-renew   # sin forzar: todavía no toca"
docker exec -e REQUESTS_CA_BUNDLE=/pebble.minica.pem web certbot renew --no-random-sleep-on-renew 2>&1 | grep -vE "^Saving debug log|^- - - -|^$"
echo "web\$ certbot renew --force-renewal --no-random-sleep-on-renew   # una renovación de verdad"
docker exec -e REQUESTS_CA_BUNDLE=/pebble.minica.pem web certbot renew --force-renewal --no-random-sleep-on-renew 2>&1 | grep -vE "^Saving debug log|^- - - -|^$"
echo "web\$ openssl x509 -in /etc/letsencrypt/live/tienda.example.com/cert.pem -noout -dates"
W openssl x509 -in /etc/letsencrypt/live/tienda.example.com/cert.pem -noout -dates

echo
echo "### 7 · Quién renueva solo: el temporizador que instala el paquete"
echo "web\$ cat /lib/systemd/system/certbot.timer"
W cat /lib/systemd/system/certbot.timer
echo "web\$ grep -v '^#' /etc/cron.d/certbot | grep ."
W sh -c "grep -v '^#' /etc/cron.d/certbot | grep ."
echo "web\$ cat /etc/letsencrypt/renewal/tienda.example.com.conf | grep -E 'authenticator|installer|server'"
W sh -c "grep -E 'authenticator|installer|server' /etc/letsencrypt/renewal/tienda.example.com.conf"

echo
echo "### 8 · Cuando el desafío falla: un dominio que no apunta a este servidor"
echo "web\$ certbot --nginx -d www.tienda.example.com -m admin@example.com --agree-tos --no-eff-email -n --server $SERVER"
docker exec -e REQUESTS_CA_BUNDLE=/pebble.minica.pem web certbot --nginx -d www.tienda.example.com -m admin@example.com --agree-tos \
  --no-eff-email -n --server "$SERVER" 2>&1 | grep -vE "^Saving debug log|^- - - -|^$"
