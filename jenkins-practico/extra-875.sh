#!/bin/bash
# Complemento de SALIDA-875: arrancar Jenkins DESDE CERO con el YAML roto (numExecutor). En correr-875.sh el contenedor
# llevaba --rm y al caerse se borró con sus logs; aquí va sin --rm para leerlos, y se borra a mano (con -v) al final.
cd "$(dirname "$0")" || exit 1
. ./comun.sh
limpiar; red
rm -rf 875/_roto; mkdir -p 875/_roto
sed 's/^  numExecutors: 0/  numExecutor: 0/' 875/jenkins.yaml > 875/_roto/jenkins.yaml
{
echo "# SALIDA 875 (complemento) — arrancar desde cero con el YAML roto"
echo
echo "> Corrida del $(date '+%Y-%m-%d %H:%M'). Misma imagen jk-a-jenkins:1; jenkins.yaml con numExecutors → numExecutor."
echo
echo '```'
echo "\$ docker run -d --name jk-a-jenkins ... (YAML con numExecutor)"
docker run -d --name $JK --network $RED --ulimit core=1 -e ADMIN_PASS=$ADMIN_PASS --env-file "$AQUI_WIN\\875\\secretos.env" \
  -v "$AQUI_WIN\\875\\_roto:/var/jenkins_home/casc:ro" $IMG >/dev/null
T0=$(ms)
for i in $(seq 1 120); do
  [ "$(docker inspect -f '{{.State.Running}}' $JK)" = "false" ] && break
  c=$(docker exec $JK curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/login 2>/dev/null)
  [ "$c" = "200" ] && break
  sleep 1
done
echo "\$ docker ps -a --filter name=jk-a-jenkins"
echo "$(docker inspect -f '{{.State.Status}} (exit {{.State.ExitCode}})' $JK) · $(( ($(ms) - T0) / 1000 )) s después de arrancar · último /login: ${c:-sin respuesta}"
echo "\$ docker logs jk-a-jenkins | grep -E 'SEVERE|numExecutor' | head -3"
docker logs $JK 2>&1 | grep -E "SEVERE|numExecutor" | cut -c1-230 | head -3
echo '```'
} > SALIDA-875-yaml-roto.md
docker rm -f -v $JK >/dev/null
limpiar
rm -rf 875/_roto
cat SALIDA-875-yaml-roto.md
