#!/bin/sh
# Mide de una tacada lo que necesitan las lecciones 4 a 12 del curso.
#
# ⛔ REGLA DE SEGURIDAD, sin excepciones: todo lo que se provoca aquí va contra
# `lab-wazuh-victima`, que es un contenedor del propio laboratorio y existe para ser atacado.
# Ni a la máquina anfitriona, ni a la red de casa, ni a nada de internet.
#
# ⚠️ Entre provocar el evento y contar las alertas hay que ESPERAR: el agente envía por lotes y
# el manager tarda unos segundos en decidir. Medir sin esperar da ceros y parece que no funciona.
export MSYS_NO_PATHCONV=1
cd "$(dirname "$0")"

M="docker exec lab-wazuh-manager"
V="docker exec lab-wazuh-victima"

antes() { $M sh -c 'wc -l < /var/ossec/logs/alerts/alerts.log' 2>/dev/null | tr -d '\r'; }
reglas() {   # $1 = línea desde la que mirar
  $M sh -c "tail -n +$1 /var/ossec/logs/alerts/alerts.log | grep -oE \"Rule: [0-9]+ \\(level [0-9]+\\) -> '[^']*'\" | sort | uniq -c | sort -rn | head -8"
}

echo "══════════════════════════════════════════════════════════════"
echo " L05 · el ruido de base: qué reglas saltan sin hacer nada"
echo "══════════════════════════════════════════════════════════════"
$M sh -c "grep -oE \"Rule: [0-9]+ \\(level [0-9]+\\)\" /var/ossec/logs/alerts/alerts.log | sort | uniq -c | sort -rn | head -10"
echo
echo "  alertas totales acumuladas: $(antes)"
echo "  por nivel:"
$M sh -c "grep -oE '\\(level [0-9]+\\)' /var/ossec/logs/alerts/alerts.log | sort | uniq -c | sort -k2 -t'l'"

echo
echo "══════════════════════════════════════════════════════════════"
echo " L07 · FIM: tocar un fichero vigilado"
echo "══════════════════════════════════════════════════════════════"
n0=$(antes)
$V sh -c 'echo "cambio del laboratorio $(date +%s)" >> /etc/hosts' >/dev/null 2>&1
echo "  modificado /etc/hosts en la víctima. Esperando al escaneo…"
$V sh -c '/var/ossec/bin/agent_control -r 2>/dev/null || true' >/dev/null 2>&1
sleep 45
echo "  reglas nuevas:"
reglas $((n0 + 1)) | sed 's/^/    /'

echo
echo "══════════════════════════════════════════════════════════════"
echo " L08 · fuerza bruta por SSH contra la víctima del laboratorio"
echo "══════════════════════════════════════════════════════════════"
n1=$(antes)
echo "  10 intentos con contraseña mala contra el usuario becario…"
$V sh -c 'for i in 1 2 3 4 5 6 7 8 9 10; do
    (sleep 0.2; echo "malaclave$i") | timeout 6 ssh -o StrictHostKeyChecking=no \
       -o PreferredAuthentications=password -o PubkeyAuthentication=no \
       becario@127.0.0.1 exit >/dev/null 2>&1
  done; true' >/dev/null 2>&1
sleep 40
echo "  reglas que saltaron:"
reglas $((n1 + 1)) | sed 's/^/    /'

echo
echo "══════════════════════════════════════════════════════════════"
echo " L13 · lo que cuesta"
echo "══════════════════════════════════════════════════════════════"
docker stats --no-stream --format "  {{.Name}}  {{.MemUsage}}  cpu {{.CPUPerc}}" \
  lab-wazuh-indexer lab-wazuh-manager lab-wazuh-dashboard lab-wazuh-victima 2>/dev/null
echo "  alertas totales al terminar: $(antes)"
