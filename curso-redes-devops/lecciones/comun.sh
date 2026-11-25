# Lo que comparten las lecciones. Corren en un contenedor docker:cli con el socket de Docker:
# crean sus redes y contenedores con el prefijo «red-» y los borran al terminar.
IMG=curso-red:1

titulo() { printf '\n== %s ==\n' "$1"; }

limpiar() {
  docker ps -aq --filter name=red- | xargs -r docker rm -f >/dev/null 2>&1
  docker network ls -q --filter name=red- | xargs -r docker network rm >/dev/null 2>&1
}

# esperar_http URL [intentos]: hasta que conteste algo (o se acaben los intentos).
esperar_puerto() { # contenedor puerto
  for _ in $(seq 1 50); do docker exec "$1" sh -c "nc -z 127.0.0.1 $2 || nc -z 0.0.0.0 $2" 2>/dev/null && return 0; sleep 0.2; done
  return 1
}

# Desde «tu máquina»: el anfitrión de Docker, que en Docker Desktop es host.docker.internal.
# Imprime «HTTP 200» o el error de curl tal cual.
desde_fuera() {
  r=$(docker run --rm $IMG curl -sS -m 3 -o /dev/null -w '%{http_code}' "http://host.docker.internal:$1/" 2>&1)
  case "$r" in curl:*) echo "$r" | head -1 ;; *) echo "HTTP $r" ;; esac
}

# El camino de la lección 5: cliente -> router (MTU 1280 hacia el cliente) -> servidor.
# Monta todo desde cero (el servidor RECUERDA el MTU aprendido y aquí no se puede borrar).
montar_mtu() { # [reglas del router]
  limpiar
  docker network create --subnet 10.81.0.0/24 red-a >/dev/null    # la del cliente
  docker network create --subnet 10.82.0.0/24 red-b >/dev/null    # la del servidor
  docker run -d --name red-router --network red-a --ip 10.81.0.254 --cap-add NET_ADMIN \
    --sysctl net.ipv4.ip_forward=1 $IMG sleep 600 >/dev/null
  docker network connect --ip 10.82.0.254 red-b red-router
  docker run -d --name red-servidor --network red-b --ip 10.82.0.10 --cap-add NET_ADMIN $IMG \
    sh -c 'mkdir -p /w && for n in 400 1000 1300 1400 1500 3000 200000; do head -c $n /dev/zero | tr "\0" "x" > /w/$n; done && exec python3 -m http.server 80 -d /w' >/dev/null
  docker run -d --name red-cliente --network red-a --ip 10.81.0.10 --cap-add NET_ADMIN ${CURSO_HOST:+-v "$CURSO_HOST/lecciones:/curso:ro"} $IMG sleep 600 >/dev/null
  docker exec red-cliente ip route add 10.82.0.0/24 via 10.81.0.254
  docker exec red-servidor ip route add 10.81.0.0/24 via 10.82.0.254
  # El tramo estrecho: la salida del router hacia el cliente, con MTU 1280.
  docker exec red-router ip link set dev eth0 mtu 1280
  [ -n "${1:-}" ] && docker exec red-router sh -c "$1"
  for _ in $(seq 1 30); do docker exec red-cliente curl -s -m 1 -o /dev/null http://10.82.0.10/400 && break; sleep 0.3; done
}
TIRA_ICMP="iptables -A OUTPUT -p icmp --icmp-type fragmentation-needed -j DROP"
AJUSTA_MSS="iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu"
