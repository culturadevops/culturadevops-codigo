# Una sola imagen para todos los papeles del laboratorio (cliente, servidor, proxy, router):
# Debian 13 con las herramientas de red de siempre.
FROM debian:trixie-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl openssl bind9-dnsutils iproute2 iptables \
      iputils-ping nginx-light python3 netcat-openbsd ca-certificates procps \
 && rm -rf /var/lib/apt/lists/* \
 && rm -f /etc/nginx/sites-enabled/default
