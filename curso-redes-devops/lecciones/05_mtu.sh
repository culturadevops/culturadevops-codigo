#!/bin/sh
# Lección 5 · El MTU: el fallo que solo aparece con respuestas grandes.
#
# Entre el cliente y el servidor hay un tramo con un MTU más pequeño (una VPN, un túnel, la red de
# un proveedor). Lo normal es que el router avise con un ICMP «fragmentation needed» y el
# servidor mande paquetes más pequeños. Pero si ese ICMP se filtra (un firewall «que bloquea el
# ping»), los paquetes grandes desaparecen sin aviso. Lo pequeño funciona. Lo grande se cuelga.
# El health check, que es pequeño, dice que todo va bien.
#
# Cada escenario monta el camino desde cero: el servidor RECUERDA el MTU que aprende, y dentro de
# un contenedor no se puede vaciar esa memoria (/proc/sys es de solo lectura). Una prueba detrás de
# otra sobre el mismo servidor daría por bueno lo que no lo es (le pasó a la primera versión).
. /curso/comun.sh


pedir() { # bytes -> «HTTP 200 · N bytes», y si se cuelga, lo dice
  r=$(docker exec red-cliente sh -c "curl -s -m 4 -o /dev/null -w '%{http_code} %{size_download}' http://10.82.0.10/$1; echo \" \$?\"")
  set -- $r
  if [ "$3" = 0 ]; then echo "HTTP $1 · $2 bytes"
  else echo "HTTP $1 · $2 bytes · colgado: curl se rinde a los 4 s (código $3)"; fi
}
tamanos() { for n in "$@"; do printf '  %7s bytes -> %s\n' "$n" "$(pedir "$n")"; done; }

titulo "5.1 · La trampa: el router tira los ICMP «fragmentation needed»"
montar_mtu "$TIRA_ICMP"
echo "  MTU del cliente: 1500 · salida del router hacia el cliente: $(docker exec red-router cat /sys/class/net/eth0/mtu)"
tamanos 400 1000 1300 1400 1500 3000 200000

titulo "5.2 · Encontrarlo: ping desde el servidor, con «no fragmentar»"
for s in 1000 1252 1253 1472; do
  if docker exec red-servidor ping -c1 -W1 -M do -s $s 10.81.0.10 >/dev/null 2>&1; then r="responde"; else r="NADA (ni un error)"; fi
  printf '  ping -M do -s %-5s (%s bytes en el cable) -> %s\n' "$s" "$((s + 28))" "$r"
done

titulo "5.3 · Arreglo 1: dejar pasar ese ICMP"
montar_mtu ""
tamanos 1400 200000
echo "  el servidor aprendió: $(docker exec red-servidor ip route get 10.81.0.10 | grep -o 'mtu [0-9]*')"

titulo "5.4 · Arreglo 2, si el firewall no es tuyo: ajustar el MSS de TCP en el router"
montar_mtu "$TIRA_ICMP && $AJUSTA_MSS"
tamanos 1400 200000
limpiar
