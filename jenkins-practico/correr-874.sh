#!/bin/bash
# Banco del vídeo 874 «Agentes de Jenkins en Docker: un contenedor nuevo por build». Desde Git Bash:
#   bash canales/cultura-devops/recursos/jenkins-practico/correr-874.sh   → escribe SALIDA-874.md
# Jenkins (jk-a-jenkins) con el socket de Docker montado: el docker-plugin crea un contenedor por build.
# Agente fijo (jk-a-fijo): un contenedor inbound-agent que vive todo el banco, como una VM de siempre.
cd "$(dirname "$0")" || exit 1
. ./comun.sh
N=${N:-10}   # corridas por lado para las medianas

consola() {  # job → consola sin trazas de Pipeline
  API "http://localhost:8080/job/$1/$2/consoleText" | grep -vE '^\[Pipeline\]|^Started by|^Running in Durability|^Resuming build' | sed '/^$/d'
}
construir() {  # job [params...] → espera y enseña la consola útil
  CLI build "$@" -s >/dev/null
  consola "$1" lastBuild
}

banco() {
echo "### 0 · Versiones"
echo "\$ jenkins --version · plugins · docker"
docker exec $JK sh -c 'java -jar /usr/share/jenkins/jenkins.war --version'
CLI list-plugins | grep -E "^(docker-plugin|configuration-as-code|workflow-aggregator|job-dsl) " | awk '{print $1, $NF}'
echo "docker (servidor) $(docker version --format '{{.Server.Version}}')"
echo "imagen del agente efímero: $AGENTE_IMG"
echo "imagen del agente fijo:    $INBOUND_IMG"
echo "plugins fijados en plugins.txt: $(wc -l < plugins.txt)"

echo
echo "### 1 · Jenkins habla con Docker por el socket"
echo "\$ docker run ... --group-add 0 -v /var/run/docker.sock:/var/run/docker.sock jk-a-jenkins:1"
echo "jk-a-jenkins\$ id ; ls -ln /var/run/docker.sock"
docker exec $JK sh -c 'id; ls -ln /var/run/docker.sock'
echo "jk-a-jenkins\$ curl --unix-socket /var/run/docker.sock http://docker/containers/json | contar"
docker exec $JK sh -c 'curl -s --unix-socket /var/run/docker.sock http://docker/containers/json' | python -c "import sys,json; c=json.load(sys.stdin); print(len(c), 'contenedores del host visibles desde Jenkins')"
echo
echo "# El riesgo: con el socket, Jenkins puede crear un contenedor que monte la raíz del host."
echo "# (Aquí solo LEE: ls de /etc del host, en solo lectura, y el contenedor se borra.)"
echo "jk-a-jenkins\$ POST /containers/create {Image: alpine, Cmd: [ls, /host/etc], Binds: [/:/host:ro]}"
ID=$(docker exec $JK sh -c 'curl -s --unix-socket /var/run/docker.sock -H "Content-Type: application/json" -X POST "http://docker/containers/create?name=jk-a-prueba-socket" -d "{\"Image\":\"alpine:3.22\",\"Cmd\":[\"sh\",\"-c\",\"ls /host/etc | head -5; echo ...; ls /host/etc | wc -l\"],\"HostConfig\":{\"Binds\":[\"/:/host:ro\"]}}"' | python -c "import sys,json;print(json.load(sys.stdin)['Id'])")
docker exec $JK sh -c "curl -s --unix-socket /var/run/docker.sock -X POST http://docker/containers/$ID/start; curl -s --unix-socket /var/run/docker.sock -X POST http://docker/containers/$ID/wait >/dev/null"
docker logs jk-a-prueba-socket 2>&1 | sed 's/^/  /'
docker rm -f jk-a-prueba-socket >/dev/null

echo
echo "### 2 · Agente FIJO: tres builds seguidos en el mismo agente"
echo "--- estado-fijo #1 (INSTALAR=true)"
construir estado-fijo -p INSTALAR=true
echo "--- estado-fijo #2 (INSTALAR=false: el Jenkinsfile ya no instala mi-linter)"
construir estado-fijo -p INSTALAR=false
echo "--- estado-fijo #3 (INSTALAR=false)"
construir estado-fijo -p INSTALAR=false
echo "jk-a-fijo\$ ls ~/agent/workspace/estado-fijo ; ls ~/bin"
docker exec jk-a-fijo sh -c 'ls ~/agent/workspace/estado-fijo | tr "\n" " "; echo; ls ~/bin'

echo
echo "### 3 · Agente EFÍMERO: lo mismo, un contenedor nuevo por build"
echo "--- estado-efimero #1 (INSTALAR=true)"
construir estado-efimero -p INSTALAR=true
H1=$(consola estado-efimero lastBuild | sed -n 's/.*contenedor: //p')
echo "--- estado-efimero #2 (INSTALAR=false)"
CLI build estado-efimero -p INSTALAR=false -s >/dev/null
T_FIN=$(ms)
consola estado-efimero lastBuild
H2=$(consola estado-efimero lastBuild | sed -n 's/.*contenedor: //p')
# ¿Cuánto tarda en desaparecer el contenedor del build #2 desde que termina?
for i in $(seq 1 240); do [ -z "$(docker ps -aq --filter id=$H2)" ] && break; sleep 0.25; done
echo
echo "\$ docker ps -a --filter id=$H1 ; docker ps -a --filter id=$H2"
docker ps -a --filter id=$H1 --format '{{.ID}} {{.Status}}'; docker ps -a --filter id=$H2 --format '{{.ID}} {{.Status}}'
echo "(vacío: los dos contenedores ya no existen; el del #2 desapareció $(( $(ms) - T_FIN )) ms después de terminar el build)"
echo "\$ jenkins list nodes"
API "http://localhost:8080/computer/api/json?tree=computer[displayName,offline]" | python -c "import sys,json; [print(' ', c['displayName'], 'offline' if c['offline'] else 'online') for c in json.load(sys.stdin)['computer']]"

echo
echo "### 4 · Cuánto cuesta el contenedor nuevo: $N builds vacíos por lado (pipeline de un solo sh)"
echo "# espera = desde que empieza el build hasta que corre el primer sh en el agente (API: timestamp; el sh imprime date +%s%3N)"
candado
for lado in fijo efimero; do
  : > ./_t_$lado
  for i in $(seq 1 $N); do
    CLI build vacio-$lado -s >/dev/null
    j=$(API "http://localhost:8080/job/vacio-$lado/lastBuild/api/json?tree=number,timestamp,duration,result")
    t_sh=$(API "http://localhost:8080/job/vacio-$lado/lastBuild/consoleText" | grep -E '^[0-9]{13}$' | head -1)
    echo "$j" | python -c "import sys,json; d=json.load(sys.stdin); print(d['number'], d['result'], int('$t_sh')-d['timestamp'], d['duration'])" >> ./_t_$lado
    [ $lado = efimero ] && sleep 3   # que el contenedor anterior termine de borrarse
  done
done
soltar_candado
for lado in fijo efimero; do
  echo "--- vacio-$lado: build resultado espera_ms duración_ms"
  cat ./_t_$lado | sed 's/^/  /'
  echo "  mediana espera: $(awk '{print $3}' ./_t_$lado | mediana) ms · mediana duración: $(awk '{print $4}' ./_t_$lado | mediana) ms"
done
rm -f ./_t_fijo ./_t_efimero

echo
echo "### 5 · ¿Quedó algo?"
sleep 5
echo "\$ docker ps -a --filter ancestor=$AGENTE_IMG"
echo "  contenedores del agente efímero vivos: $(docker ps -aq --filter ancestor=$AGENTE_IMG | wc -l)"
}

limpiar
construir_imagen
red
arrancar_jenkins 874 --group-add 0 -v /var/run/docker.sock:/var/run/docker.sock
ARR=$(espera_jenkins)
cli_jar
SECRET=$(echo 'println jenkins.model.Jenkins.get().getComputer("fijo").getJnlpMac()' | CLI groovy =)
docker run -d --rm --name jk-a-fijo --network $RED --ulimit core=1 -e JENKINS_URL=http://jk-a-jenkins:8080/ \
  -e JENKINS_SECRET=$SECRET -e JENKINS_AGENT_NAME=fijo -e JENKINS_WEB_SOCKET=true $INBOUND_IMG >/dev/null
for i in $(seq 1 60); do API http://localhost:8080/computer/fijo/api/json?tree=offline | grep -q '"offline":false' && break; sleep 1; done
{
  echo "# SALIDA 874 — Agentes de Jenkins en Docker (cultura-devops)"
  echo
  echo "> Corrida del $(date '+%Y-%m-%d %H:%M'). jk-a-jenkins:1 = jenkins/jenkins:2.580.2-lts-jdk21 + plugins.txt; configuración en 874/jenkins.yaml (JCasC) y 874/jobs.groovy (Job DSL). Jenkins arrancó en $ARR ms."
  echo
  echo '```'
  banco
  echo '```'
} > SALIDA-874.md 2>&1
limpiar
cat SALIDA-874.md
