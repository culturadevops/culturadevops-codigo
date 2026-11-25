#!/bin/bash
# Demos del vídeo 696 de cultura-devops:
#   «Bind for 0.0.0.0:PORT failed: port is already allocated»
# Se provoca el choque de puertos de las tres formas reales y se encuentra al culpable.
# Parte Linux dentro de un docker-in-docker (ss/lsof limpios). Parte Windows: directa en el host
# (netstat -ano), llamando a powershell.exe.
#   bash canales/cultura-devops/recursos/docker-error-port-already-allocated/correr.sh
set -u
export MSYS_NO_PATHCONV=1
cd "$(dirname "$0")"
NGX=nginx:1.29-alpine
DIND=docker:29.6.2-dind

limpiar() {
  docker rm -f v696-dind >/dev/null 2>&1
  powershell.exe -NoProfile -Command "docker rm -f v696-a v696-b v696-c v696-d *> \$null" >/dev/null 2>&1
}
trap limpiar EXIT

# D: ejecuta dentro del dind mostrando el comando
D() { echo "\$ $*"; docker exec v696-dind sh -c "$*" 2>&1; }

linux_demos() {
echo "### Versión (dentro del docker-in-docker Linux)"
docker exec v696-dind sh -c 'echo "$ docker version --format ..."; docker version --format "cliente {{.Client.Version}} · servidor {{.Server.Version}}"'
echo

echo "=================== A · El error: dos contenedores quieren el mismo puerto ==================="
D 'docker run -d --name web1 -p 8080:80 nginx:1.29-alpine >/dev/null && echo "web1 arriba en 8080"'
D 'docker run -d --name web2 -p 8080:80 nginx:1.29-alpine; echo exit=$?'
echo

echo "=================== B · Encontrar al culpable ==================="
echo "--- quién publica ese puerto, según Docker:"
D 'docker ps --filter publish=8080 --format "table {{.Names}}\t{{.Ports}}"'
echo "--- quién escucha en el host, con ss:"
D 'ss -ltnp "sport = :8080"'
echo "--- o con lsof:"
D 'lsof -nP -iTCP:8080 -sTCP:LISTEN'
echo

echo "=================== C · Los dos arreglos ==================="
echo "--- arreglo 1: publicar en OTRO puerto del host (izquierda = host, derecha = contenedor)"
D 'docker run -d --name web3 -p 8081:80 nginx:1.29-alpine >/dev/null && docker port web3'
echo "--- arreglo 2: si web1 sobraba, pararlo y liberar el 8080"
D 'docker rm -f web1 >/dev/null && docker run -d --name web4 -p 8080:80 nginx:1.29-alpine >/dev/null && docker port web4'
D 'docker rm -f web2 web3 web4 >/dev/null 2>&1; echo limpiado'
echo

echo "=================== D · Causa 2: un proceso del host (no un contenedor) ocupa el puerto ==================="
echo "--- un servidor cualquiera escuchando en 8082 (aquí, nc):"
D '(nc -lk -p 8082 -e true &) ; sleep 1; echo "nc escuchando en 8082"'
D 'docker run -d --name web5 -p 8082:80 nginx:1.29-alpine; echo exit=$?'
echo "(mensaje distinto: address already in use. docker ps --filter publish no muestra nada...)"
D 'docker ps --filter publish=8082 --format "{{.Names}}"; echo "(vacío: no es un contenedor)"'
echo "--- ...pero ss/lsof sí dan con el proceso del host:"
D 'ss -ltnp "sport = :8082"'
D 'lsof -nP -iTCP:8082 -sTCP:LISTEN'
D 'pkill nc 2>/dev/null; docker rm -f web5 >/dev/null 2>&1; echo limpiado'
echo

echo "=================== E · Causa 3: un compose viejo que quedó levantado ==================="
D 'mkdir -p /tmp/tienda && printf "services:\n  cache:\n    image: nginx:1.29-alpine\n    ports:\n      - 8083:80\n" > /tmp/tienda/compose.yaml'
D 'cd /tmp/tienda && docker compose up -d 2>&1 | tail -1'
echo "(te olvidas de que sigue arriba y mañana otro proyecto pide el 8083)"
D 'docker run -d --name web6 -p 8083:80 nginx:1.29-alpine; echo exit=$?'
echo "--- el culpable lleva etiquetas de compose: te dicen qué proyecto y en qué carpeta pararlo"
D 'docker ps --filter publish=8083 --format "{{.Names}}"'
D 'docker inspect -f "proyecto={{index .Config.Labels \"com.docker.compose.project\"}} carpeta={{index .Config.Labels \"com.docker.compose.project.working_dir\"}}" $(docker ps -q --filter publish=8083)'
D 'cd /tmp/tienda && docker compose down -v 2>&1 | tail -1'
D 'docker rm -f web6 >/dev/null 2>&1; echo limpiado'
}

windows_demos() {
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command '
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$ErrorActionPreference = "SilentlyContinue"
function Show($c) { Write-Output "`$ $c" }

Write-Output "=================== F · En Windows: dos contenedores y netstat -ano para el culpable ==================="
Show "docker run -d --name v696-a -p 29087:80 nginx:1.29-alpine"
docker run -d --name v696-a -p 29087:80 nginx:1.29-alpine | Out-Null
Write-Output "v696-a arriba en 29087"
Show "docker run -d --name v696-b -p 29087:80 nginx:1.29-alpine"
docker run -d --name v696-b -p 29087:80 nginx:1.29-alpine
Write-Output ("exit=" + $LASTEXITCODE)
Write-Output ""
Write-Output "--- quién tiene el puerto, con netstat -ano (la última columna es el PID):"
Show "netstat -ano | findstr :29087"
netstat -ano | findstr ":29087"
Write-Output "--- en Windows ese PID es el backend de Docker Desktop, no el contenedor:"
$owner = (Get-NetTCPConnection -LocalPort 29087 -State Listen | Select-Object -First 1).OwningProcess
Show ("tasklist /FI ""PID eq $owner""")
tasklist /FI "PID eq $owner" | Select-Object -Skip 3
Write-Output "--- el culpable real (el contenedor) lo da docker ps --filter publish:"
Show "docker ps --filter publish=29087 --format ""{{.Names}}"""
docker ps --filter publish=29087 --format "{{.Names}}"
docker rm -f v696-a v696-b | Out-Null
Write-Output ""

Write-Output "--- OJO (medido): en Windows, un proceso del host en 0.0.0.0 NO choca con el contenedor"
$f = Join-Path $env:TEMP "v696hold.py"
Set-Content -Path $f -Encoding ascii -Value "import socket,time`ns=socket.socket(socket.AF_INET,socket.SOCK_STREAM)`ns.bind((''0.0.0.0'',29088))`ns.listen()`ntime.sleep(60)"
$py = Start-Process python -ArgumentList $f -PassThru -WindowStyle Hidden
Start-Sleep 2
Show "docker run -d --rm --name v696-c -p 29088:80 nginx:1.29-alpine"
docker run -d --rm --name v696-c -p 29088:80 nginx:1.29-alpine | Out-Null
Write-Output ("exit=" + $LASTEXITCODE + "  (arrancó: Docker Desktop reenvía por la red de WSL, convive con el proceso del host)")
netstat -ano | findstr "LISTENING" | findstr ":29088"
docker rm -f v696-c | Out-Null
Stop-Process -Id $py.Id -Force
Remove-Item $f -EA SilentlyContinue
Write-Output ""

Write-Output "--- donde SÍ choca un proceso del host en Windows: publicar en una interfaz concreta (127.0.0.1)"
$l = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, 29089)
$l.Start()
Write-Output "(un proceso escucha en 127.0.0.1:29089)"
Show "docker run -d --rm --name v696-d -p 127.0.0.1:29089:80 nginx:1.29-alpine"
docker run -d --rm --name v696-d -p 127.0.0.1:29089:80 nginx:1.29-alpine
Write-Output ("exit=" + $LASTEXITCODE)
Write-Output "--- netstat -ano y tasklist dan con el proceso del host:"
netstat -ano | findstr "LISTENING" | findstr ":29089"
$owner2 = (Get-NetTCPConnection -LocalPort 29089 -State Listen | Select-Object -First 1).OwningProcess
tasklist /FI "PID eq $owner2" | Select-Object -Skip 3
$l.Stop()
docker rm -f v696-d *> $null
' 2>&1
}

docker rm -f v696-dind >/dev/null 2>&1
docker run -d --privileged --rm --name v696-dind -e DOCKER_TLS_CERTDIR= $DIND >/dev/null
for i in $(seq 1 40); do docker exec v696-dind docker info >/dev/null 2>&1 && break; sleep 1; done
docker exec v696-dind sh -c 'apk add -q iproute2 lsof 2>&1 | tail -1 >/dev/null; true'
docker save $NGX | docker exec -i v696-dind docker load -q >/dev/null

{
  echo "# SALIDA · docker-error-port-already-allocated (vídeo 696, cultura-devops)"
  echo
  echo "Ejecutado el $(date +%F) con \`bash correr.sh\` desde Git Bash en Windows 11 + Docker Desktop. La parte Linux corre en un docker-in-docker (\`$DIND\`, \`--privileged --rm\`) para tener \`ss\` y \`lsof\` limpios; la parte Windows corre directa en el host. Salida literal."
  echo
  echo '```'
  linux_demos
  echo
  windows_demos
  echo '```'
} > SALIDA.md
echo "SALIDA.md escrito"
