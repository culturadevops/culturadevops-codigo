#!/bin/sh
# por-regla.sh - se ejecuta DENTRO de lab-wazuh-manager (docker cp + docker exec).
# Cuenta las alertas del agente victima-windows en alerts.json, agrupadas por regla.
#   sh /tmp/por-regla.sh total      -> solo el numero
#   sh /tmp/por-regla.sh reglas     -> "N  id nivel L  descripcion"
#   sh /tmp/por-regla.sh ultimas N  -> las N ultimas alertas del agente, compactas
F=/var/ossec/logs/alerts/alerts.json
case "$1" in
  total)
    grep -c '"name":"victima-windows"' "$F" 2>/dev/null || echo 0 ;;
  reglas)
    grep '"name":"victima-windows"' "$F" 2>/dev/null \
      | sed -n 's/.*"rule":{"level":\([0-9]*\),"description":"\([^"]*\)","id":"\([0-9]*\)".*/\3 nivel \1  \2/p' \
      | sort | uniq -c | sort -rn ;;
  ultimas)
    grep '"name":"victima-windows"' "$F" 2>/dev/null | tail -n "${2:-5}" \
      | sed -n 's/.*"timestamp":"\([^"]*\)".*"rule":{"level":\([0-9]*\),"description":"\([^"]*\)","id":"\([0-9]*\)".*/\1  \4 nivel \2  \3/p' ;;
esac
