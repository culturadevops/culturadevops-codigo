#!/usr/bin/env bash
# diagnostico.sh — «no funciona»: ¿qué capa? De abajo arriba, y para en la primera que falla.
#
#   1 DNS     ¿resuelve el nombre? ¿a qué IP?
#   2 TCP     ¿hay alguien escuchando en ese puerto?
#   3 TLS     ¿la cadena se verifica? ¿tiene SAN? ¿cuántos días le quedan?
#   4 HTTP    ¿contesta? ¿con qué código, y en cuánto?
#   5 CUERPO  ¿llega la respuesta ENTERA? (la que se cuelga a medias es el MTU, lección 5)
#
# Sale con 0 si todo va bien, o con el número de la capa que falla.
# Uso: diagnostico.sh URL [--ca fichero.pem]
set -uo pipefail
URL=$1; shift
CA=""
[ "${1:-}" = "--ca" ] && CA=$2
esquema=${URL%%://*}; resto=${URL#*://}; hostport=${resto%%/*}
host=${hostport%%:*}; puerto=${hostport##*:}
[ "$puerto" = "$hostport" ] && { [ "$esquema" = https ] && puerto=443 || puerto=80; }
ms() { date +%s%3N; }
ok()   { printf '  %-7s ✓ %s\n' "$1" "$2"; }
mal()  { printf '  %-7s ✗ %s\n' "$1" "$2"; echo "  -> falla la capa $3 ($1)"; exit "$3"; }
aviso(){ printf '  %-7s ! %s\n' "$1" "$2"; }

echo "diagnóstico de $URL"

# 1 · DNS
t0=$(ms); ip=$(getent ahostsv4 "$host" | awk 'NR==1 {print $1}'); t1=$(ms)
[ -n "$ip" ] || mal DNS "«$host» no resuelve" 1
ok DNS "$host -> $ip ($((t1 - t0)) ms)"

# 2 · TCP
t0=$(ms)
nc -z -w 3 "$ip" "$puerto" 2>/dev/null || mal TCP "nadie escucha en $ip:$puerto (o un firewall lo tira)" 2
ok TCP "$ip:$puerto abierto ($(( $(ms) - t0 )) ms)"

# 3 · TLS
CURL_CA=()
if [ "$esquema" = https ]; then
  [ -n "$CA" ] && CURL_CA=(--cacert "$CA")
  sc=$(openssl s_client -connect "$ip:$puerto" -servername "$host" -verify_hostname "$host" \
        ${CA:+-CAfile "$CA"} -showcerts </dev/null 2>/dev/null)
  codigo=$(echo "$sc" | sed -n 's/.*Verify return code: \([0-9]*\) (\(.*\))/\1 \2/p' | tail -1)
  [ "${codigo%% *}" = 0 ] || mal TLS "verificación: ${codigo#* }" 3
  hoja=$(echo "$sc" | awk '/BEGIN CERTIFICATE/{n++} n==1' | sed '/END CERTIFICATE/q')
  san=$(echo "$hoja" | openssl x509 -noout -ext subjectAltName 2>/dev/null | tail -n +2 | tr -d ' ')
  fin=$(echo "$hoja" | openssl x509 -noout -enddate | cut -d= -f2)
  dias=$(( ( $(date -d "$fin" +%s) - $(date +%s) ) / 86400 ))
  enviados=$(echo "$sc" | grep -c 'BEGIN CERTIFICATE')
  [ -n "$san" ] || mal TLS "sin SAN: curl y openssl lo aceptan, Go lo rechaza (lección 4)" 3
  ok TLS "verificado · $san · $enviados certificados en la cadena · caduca en $dias días"
  [ "$dias" -lt 30 ] && aviso TLS "menos de 30 días"
fi

# 4 · HTTP: solo la cabecera (HEAD); el cuerpo es la capa 5
r=$(curl -sS -m 5 "${CURL_CA[@]}" -I -o /dev/null -D /tmp/cab -w '%{http_code} %{time_starttransfer}' "$URL" 2>&1) \
  || mal HTTP "$(echo "$r" | head -1 | sed 's/^curl: //')" 4
codigo=${r%% *}
[ "$codigo" -lt 500 ] || mal HTTP "contesta $codigo" 4
ok HTTP "$codigo en ${r#* } s"

# 5 · CUERPO entero
largo=$(grep -i '^content-length:' /tmp/cab | tr -dc '0-9')
r=$(curl -s -m 8 "${CURL_CA[@]}" -o /dev/null -w '%{size_download} %{time_total}' "$URL"; echo " $?")
set -- $r
if [ "$3" != 0 ]; then
  mal CUERPO "llegaron $1 de ${largo:-?} bytes y se colgó (código $3): pequeño sí, grande no -> mira el MTU" 5
fi
ok CUERPO "$1 bytes en $2 s"
echo "  -> todo bien (0)"
