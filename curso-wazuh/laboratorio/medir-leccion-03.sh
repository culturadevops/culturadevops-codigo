#!/bin/sh
# Mide los huecos que quedaron sin rellenar en la lección 03 (los `TT_*` del builder).
#
# ⛔ Todo esto se hace contra `lab-wazuh-victima`, que es un contenedor del propio laboratorio.
#    Ni a la máquina anfitriona, ni a la red de casa, ni a nada de internet.
#
# ⚠️ La clave del agente NO se imprime entera: se enseña solo su forma (cuántos caracteres).
#    Es una clave de laboratorio y da igual, pero una clave en pantalla en un vídeo es un hábito
#    que no se coge.
#
# ⚠️ DOS TROPIEZOS QUE YA DIERON NÚMEROS FALSOS, y por eso el guion está escrito así:
#    1. Cronometrar la reconexión SIN esperar primero a que el agente se caiga da 0 s: el manager
#       todavía lo tiene por Active cuando miras. Hay que esperar a Disconnected y luego a Active.
#    2. Contar «una alerta más en el fichero» NO es «llegó mi alerta»: puede ser cualquier otra.
#       Hay que buscar la regla concreta, no el contador.
export MSYS_NO_PATHCONV=1
cd "$(dirname "$0")"

M="docker exec lab-wazuh-manager"
V="docker exec lab-wazuh-victima"

estado() {   # lo que el manager dice del agente 005
  $M /var/ossec/bin/agent_control -l 2>/dev/null | tr -d '\r' \
    | grep "ID: 005" | sed 's/.*, //'
}

echo "══════════════════════════════════════════════════════════════"
echo " TT_ID · el número que le tocó al agente"
echo "══════════════════════════════════════════════════════════════"
$M /var/ossec/bin/agent_control -l 2>/dev/null | tr -d '\r' | sed 's/^/  /'

echo "══════════════════════════════════════════════════════════════"
echo " TT_CLAVE · la forma de la línea de client.keys (sin la clave)"
echo "══════════════════════════════════════════════════════════════"
$V sh -c 'awk "{print \$1, \$2, \$3, \"clave de\", length(\$4), \"caracteres\"}" /var/ossec/etc/client.keys' \
  2>/dev/null | tr -d '\r' | sed 's/^/  /'

echo
echo "══════════════════════════════════════════════════════════════"
echo " TT_LLEGA · del intento fallido a la alerta 5760 en el servidor"
echo "══════════════════════════════════════════════════════════════"
echo "  (el agente lleva rato estable, que si no el número sale inflado)"
n0=$($M sh -c 'wc -l < /var/ossec/logs/alerts/alerts.log' 2>/dev/null | tr -d '\r')
t0=$(date +%s)
$V sh -c '(sleep 0.2; echo "malaclave") | timeout 8 ssh -o StrictHostKeyChecking=no \
   -o PreferredAuthentications=password -o PubkeyAuthentication=no \
   becario@127.0.0.1 exit' >/dev/null 2>&1
echo "  intento lanzado. Buscando la regla 5760, no el contador…"
i=0
while [ $i -lt 180 ]; do
  if $M sh -c "tail -n +$((n0 + 1)) /var/ossec/logs/alerts/alerts.log | grep -q 'Rule: 5760'" 2>/dev/null; then
    break
  fi
  sleep 2
  i=$((i + 2))
done
echo "  la alerta 5760 aparece en: $(($(date +%s) - t0)) s"
echo
echo "  la alerta, literal:"
$M sh -c "tail -n +$((n0 + 1)) /var/ossec/logs/alerts/alerts.log | grep -B2 -A4 'Rule: 5760' | head -14" \
  2>/dev/null | tr -d '\r' | sed 's/^/    /'

echo
echo "══════════════════════════════════════════════════════════════"
echo " TT_RECONEXION · reinicio el agente y cronometro hasta Active"
echo "══════════════════════════════════════════════════════════════"
echo "  estado antes del reinicio: $(estado)"
$V /var/ossec/bin/wazuh-control restart >/dev/null 2>&1
t0=$(date +%s)
# 1) esperar a que el manager se entere de que se ha caído
i=0
while [ $i -lt 120 ]; do
  case "$(estado)" in *Disconnected*|*Never*) break;; esac
  sleep 1
  i=$((i + 1))
done
echo "  el manager lo da por caído a los: $(($(date +%s) - t0)) s"
# 2) esperar a que vuelva
i=0
while [ $i -lt 300 ]; do
  case "$(estado)" in *Active*) break;; esac
  sleep 2
  i=$((i + 2))
done
echo "  vuelve a estar Active a los: $(($(date +%s) - t0)) s (desde el reinicio)"
