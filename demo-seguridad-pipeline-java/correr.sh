#!/bin/sh
# Lanza la demo en Docker y guarda la salida en SALIDA.md. El repositorio de maven y la base de trivy quedan en volúmenes aparte.
cd "$(dirname "$0")"
D="$(pwd -W 2>/dev/null || pwd)"
T="docker run --rm -v $D:/demo -v demo-trivy-cache:/root/.cache aquasec/trivy:0.75.0"
{ echo '# Salida real — seguridad en el pipeline para Java'; echo; echo "Ejecutado el $(date -u +%Y-%m-%dT%H:%MZ)."; echo; echo '```'
  MSYS_NO_PATHCONV=1 docker run --rm -v "$D:/demo" -v demo-java-m2:/root/.m2 maven:3.9-eclipse-temurin-21 sh /demo/ejecutar.sh
  echo
  echo "### 3 · trivy (dependencias del pom.xml) sobre la app vulnerable, solo HIGH y CRITICAL"
  echo "\$ trivy fs --scanners vuln --severity HIGH,CRITICAL --exit-code 1 app/"
  MSYS_NO_PATHCONV=1 $T --version | head -1
  MSYS_NO_PATHCONV=1 $T fs --quiet --scanners vuln --severity HIGH,CRITICAL --exit-code 1 /demo/app; echo "código de salida de trivy: $?"
  echo
  echo "### 4 · trivy sobre la app arreglada"
  echo "\$ trivy fs --scanners vuln --severity HIGH,CRITICAL --exit-code 1 app-arreglada/"
  MSYS_NO_PATHCONV=1 $T fs --quiet --scanners vuln --severity HIGH,CRITICAL --exit-code 1 /demo/app-arreglada; echo "código de salida de trivy: $?"
  echo
  echo "### 5 · trivy buscando secretos en el código (la clave de Stripe)"
  echo "\$ trivy fs --scanners secret --exit-code 1 app/src/"
  MSYS_NO_PATHCONV=1 $T fs --quiet --scanners secret --exit-code 1 /demo/app/src; echo "código de salida de trivy: $?"
  echo '```'; } > SALIDA.md 2>&1
