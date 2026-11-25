#!/usr/bin/env bash
# Controlador del 878: como root y con el socket de Docker, para que `agent { docker }` lance contenedores hermanos
# (docker-workflow usa --volumes-from con este contenedor, así ven el mismo workspace y /repos).
set -euo pipefail
cd "$(dirname "$0")"
export MSYS_NO_PATHCONV=1
docker rm -f jk-b-jenkins-878 >/dev/null 2>&1 || true
docker run -d --rm --ulimit core=1 --name jk-b-jenkins-878 -u root -p 28078:8080 \
  -v //var/run/docker.sock:/var/run/docker.sock \
  -v "$(cygpath -w "$PWD/petclinic.git"):/repos/petclinic.git:ro" \
  -v "$(cygpath -w "$PWD/../jenkins/casc-878.yaml"):/casc/casc.yaml:ro" \
  jk-b-jenkins:2.580.2 >/dev/null
echo "jk-b-jenkins-878 en http://localhost:28078"
