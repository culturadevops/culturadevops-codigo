#!/bin/sh
# Lección 6 · ¿Quién te está hablando? La IP que ves no es la del cliente.
#
# Tu aplicación limita peticiones por IP, o deja pasar solo a la oficina. Detrás de un proxy, todas
# las peticiones llegan desde la IP del proxy: o bloqueas a todo el mundo a la vez, o dejas pasar a
# todo el mundo. Sin un error. La IP real viaja en una cabecera, si el proxy la pone... y solo
# vale si el que la pone es TU proxy: cualquiera puede escribir esa cabecera.
. /curso/comun.sh
limpiar
docker network create --subnet 10.90.0.0/24 red-p >/dev/null

# La aplicación: contesta con la IP que ve y la cabecera X-Forwarded-For que le llega.
APP='
import http.server
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        xff = self.headers.get("X-Forwarded-For", "-")
        cuerpo = f"veo {self.client_address[0]} · X-Forwarded-For: {xff}\n".encode()
        self.send_response(200); self.end_headers(); self.wfile.write(cuerpo)
    def log_message(self, *a): pass
http.server.HTTPServer(("0.0.0.0", 8000), H).serve_forever()'
docker run -d --name red-app --network red-p --ip 10.90.0.10 $IMG python3 -c "$APP" >/dev/null
proxy() { # nombre config
  docker run -d --name "$1" --network red-p --ip "$2" $IMG sh -c "printf '%s\n' '$3' > /etc/nginx/conf.d/p.conf && exec nginx -g 'daemon off;'" >/dev/null
}
proxy red-proxy-pelado 10.90.0.20 'server { listen 80; location / { proxy_pass http://10.90.0.10:8000; } }'
proxy red-proxy-xff    10.90.0.21 'server { listen 80; location / { proxy_pass http://10.90.0.10:8000; proxy_set_header X-Forwarded-For $remote_addr; } }'
cliente() { # ip url [cabecera]
  docker run --rm --network red-p --ip "$1" $IMG curl -s -m 3 ${3:+-H "$3"} "$2"
}
sleep 2

titulo "6.1 · Directo a la aplicación: cada cliente con su IP"
for ip in 10.90.0.101 10.90.0.102; do echo "  cliente $ip -> $(cliente $ip http://10.90.0.10:8000/)"; done

titulo "6.2 · Detrás de un proxy: todos son el proxy"
for ip in 10.90.0.101 10.90.0.102; do echo "  cliente $ip -> $(cliente $ip http://10.90.0.20/)"; done

titulo "6.3 · El proxy pone la IP real en X-Forwarded-For"
for ip in 10.90.0.101 10.90.0.102; do echo "  cliente $ip -> $(cliente $ip http://10.90.0.21/)"; done

titulo "6.4 · La trampa de la trampa: la cabecera la puede escribir cualquiera"
echo "  cliente 10.90.0.101, directo, con X-Forwarded-For: 10.0.0.1 (la IP «de la oficina»)"
echo "    -> $(cliente 10.90.0.101 http://10.90.0.10:8000/ 'X-Forwarded-For: 10.0.0.1')"
echo "  lo mismo a través del proxy, que REESCRIBE la cabecera con \$remote_addr"
echo "    -> $(cliente 10.90.0.101 http://10.90.0.21/ 'X-Forwarded-For: 10.0.0.1')"
limpiar
