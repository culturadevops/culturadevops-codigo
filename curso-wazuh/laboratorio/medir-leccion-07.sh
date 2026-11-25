#!/bin/sh
# L07 · FIM: qué vigila de fábrica, cómo se añade una ruta, y QUE cambió contra QUIÉN lo cambió.
#
# ⛔ Todo dentro de los contenedores del laboratorio. Nada fuera.
#
# ⚠️ El encargo pide «el antes y el después» de un fichero tocado en vivo. Eso solo sale si el
# fichero YA estaba en la base de FIM antes de tocarlo: si lo creas y lo tocas en el mismo minuto,
# la alerta es «added», no «modified», y no hay antes que enseñar.
export MSYS_NO_PATHCONV=1
cd "$(dirname "$0")"

M="docker exec lab-wazuh-manager"
V="docker exec lab-wazuh-victima"

echo "══════════════════════════════════════════════════════════════"
echo " 1 · qué vigila de fábrica (los <directories> del agente)"
echo "══════════════════════════════════════════════════════════════"
$V sh -c "grep -A2 '<syscheck>' /var/ossec/etc/ossec.conf | head -6; \
          grep -oE '<directories[^>]*>[^<]*</directories>' /var/ossec/etc/ossec.conf" \
  2>&1 | tr -d '\r' | sed 's/^/  /'

echo
echo "  cada cuánto pasa el escaneo completo:"
$V sh -c "grep -oE '<frequency>[0-9]+</frequency>' /var/ossec/etc/ossec.conf | head -2" \
  2>&1 | tr -d '\r' | sed 's/^/    /'
echo "  ¿está el tiempo real activado de fábrica?"
$V sh -c "grep -c 'realtime>yes' /var/ossec/etc/ossec.conf" 2>&1 | tr -d '\r' | sed 's/^/    realtime=yes en /'

echo
echo "══════════════════════════════════════════════════════════════"
echo " 2 · cuántos ficheros tiene ya en su base"
echo "══════════════════════════════════════════════════════════════"
$M sh -c 'ls /var/ossec/queue/db/*.db 2>/dev/null | head -3' 2>&1 | tr -d '\r' | sed 's/^/  /'
$V sh -c 'ls -la /var/ossec/queue/fim/db/ 2>/dev/null' 2>&1 | tr -d '\r' | sed 's/^/  /'

echo
echo "══════════════════════════════════════════════════════════════"
echo " 3 · TOCAR un fichero que YA estaba vigilado, y ver el antes/después"
echo "══════════════════════════════════════════════════════════════"
n0=$($M sh -c 'wc -l < /var/ossec/logs/alerts/alerts.log' | tr -d '\r')
echo "  alertas antes: $n0"
echo "  antes de tocarlo:"
$V sh -c 'ls -l /etc/hosts; md5sum /etc/hosts' 2>&1 | tr -d '\r' | sed 's/^/    /'
$V sh -c 'echo "10.0.0.99 impostor.local  # lo mete el laboratorio" >> /etc/hosts'
echo "  después de tocarlo:"
$V sh -c 'ls -l /etc/hosts; md5sum /etc/hosts' 2>&1 | tr -d '\r' | sed 's/^/    /'
echo "  forzando un escaneo y esperando la alerta…"
$V sh -c '/var/ossec/bin/agent_control -r 2>/dev/null || true' >/dev/null 2>&1
i=0
while [ $i -lt 300 ]; do
  if $M sh -c "tail -n +$((n0 + 1)) /var/ossec/logs/alerts/alerts.log | grep -q 'Rule: 550'" 2>/dev/null; then
    break
  fi
  sleep 5; i=$((i + 5))
done
echo "  tardó: $i s (0 = ya estaba, 300 = no llegó)"
echo
echo "  LA ALERTA ENTERA, que es lo que hay que enseñar:"
$M sh -c "tail -n +$((n0 + 1)) /var/ossec/logs/alerts/alerts.log | grep -A16 'Rule: 550' | head -22" \
  2>&1 | tr -d '\r' | sed 's/^/    /'

echo
echo "══════════════════════════════════════════════════════════════"
echo " 4 · lo que NO dice la alerta: quién lo hizo"
echo "══════════════════════════════════════════════════════════════"
echo "  ¿hay auditd en la víctima?"
$V sh -c 'which auditctl ausearch 2>/dev/null || echo "    no está instalado"' 2>&1 | tr -d '\r' | sed 's/^/  /'
echo "  campos de la alerta que hablan del autor:"
$M sh -c "tail -n +$((n0 + 1)) /var/ossec/logs/alerts/alerts.log | grep -A16 'Rule: 550' \
  | grep -iE 'user|audit|uid|process' | head -6" 2>&1 | tr -d '\r' | sed 's/^/    /'
echo "  (si no sale nada, ese es exactamente el dato de la lección)"

echo
echo "══════════════════════════════════════════════════════════════"
echo " 5 · lo que cuesta vigilar: el tamaño de la base de FIM"
echo "══════════════════════════════════════════════════════════════"
$V sh -c 'du -sh /var/ossec/queue/fim /var/ossec/queue/diff 2>/dev/null' 2>&1 | tr -d '\r' | sed 's/^/  /'
$V sh -c 'du -sh /var/ossec 2>/dev/null' 2>&1 | tr -d '\r' | sed 's/^/  total del agente: /'
