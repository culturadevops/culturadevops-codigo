#!/bin/bash
# Ayudantes del banco «Jenkins práctico». Se carga con `. ./comun.sh` desde ejecutar.sh.
# Todo lo que se crea lleva el prefijo jk-a- y se borra con limpiar(): contenedores con --rm,
# la red por nombre. La imagen jk-a-jenkins:1 se queda para repetir el banco.
export MSYS_NO_PATHCONV=1
IMG=jk-a-jenkins:1
AGENTE_IMG=jenkins/agent:3395.v6e5377b_0fb_3c-5-jdk21
INBOUND_IMG=jenkins/inbound-agent:3395.v6e5377b_0fb_3c-5-jdk21
RED=jk-a-red
JK=jk-a-jenkins
ADMIN_PASS=admin-de-prueba
AQUI_WIN=$(cygpath -w "$PWD")

ms() { date +%s%3N; }

construir_imagen() { docker build -q -t $IMG . >/dev/null || exit 1; }

red() { docker network inspect $RED >/dev/null 2>&1 || docker network create --subnet 10.231.7.0/24 $RED >/dev/null; }

# arrancar_jenkins <carpeta-casc> [opciones extra de docker run]: contenedor nuevo, sin volumen con nombre.
# El VOLUME /var/jenkins_home de la imagen es anónimo y --rm lo borra con el contenedor.
arrancar_jenkins() {
  local casc="$1"; shift
  docker run -d --rm --name $JK --hostname $JK --network $RED --ulimit core=1 \
    -e ADMIN_PASS=$ADMIN_PASS -v "$AQUI_WIN\\$casc:/var/jenkins_home/casc:ro" "$@" $IMG >/dev/null
}

# espera_jenkins: hasta que /login conteste 200 (o 300 s). Devuelve los ms que tardó.
espera_jenkins() {
  local t0=$(ms)
  for i in $(seq 1 600); do
    c=$(docker exec $JK curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/login 2>/dev/null)
    [ "$c" = "200" ] && { echo $(( $(ms) - t0 )); return 0; }
    sleep 0.5
  done
  echo "TIMEOUT"; return 1
}

cli_jar() { docker exec $JK curl -s -o /tmp/jenkins-cli.jar http://localhost:8080/jnlpJars/jenkins-cli.jar; }
CLI() { docker exec -i $JK java -jar /tmp/jenkins-cli.jar -s http://jk-a-jenkins:8080/ -webSocket -auth admin:$ADMIN_PASS "$@" 2>&1 | tr -d '\r'; }
# API REST como admin, desde dentro del contenedor (el puerto no se publica).
API() { docker exec $JK curl -s -g -u admin:$ADMIN_PASS "$@" | tr -d '\r'; }

parar_jenkins() { docker rm -f -v $JK >/dev/null 2>&1; }

limpiar() {
  docker ps -aq --filter "name=^jk-a-" | xargs -r docker rm -f -v >/dev/null 2>&1
  # agentes que creó el docker-plugin de ESTE Jenkins (nombre aleatorio): se borran con sus volúmenes
  docker ps -aq --filter "label=com.nirima.jenkins.plugins.docker.JenkinsServerUrl=http://jk-a-jenkins:8080/" | xargs -r docker rm -f -v >/dev/null 2>&1
  docker network rm $RED >/dev/null 2>&1
  true
}

# mediana de una lista de números (uno por línea)
mediana() { sort -n | awk '{a[NR]=$1} END{ if(NR%2) print a[(NR+1)/2]; else print int((a[NR/2]+a[NR/2+1])/2) }'; }

candado() { until mkdir <proyecto>/_logs/banco.lock 2>/dev/null; do sleep 2; done; echo "jk-a $$ $(date)" > <proyecto>/_logs/banco.lock/dueño-jk-a.txt; }
soltar_candado() { rm -f <proyecto>/_logs/banco.lock/dueño-jk-a.txt; rmdir <proyecto>/_logs/banco.lock 2>/dev/null; true; }
