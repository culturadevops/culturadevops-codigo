#!/bin/bash
# Banco del monitor de disponibilidad en Python (cultura-devops 799). Desde Git Bash:
#   bash canales/cultura-devops/recursos/pruebas-monitor-uptime-python/ejecutar.sh
# Todo es local, en la red de Docker cd799-red: los sitios y el «Discord» son contenedores de este banco.
# ⛔ Nada se envía a Discord de verdad. Todos los contenedores con --rm y --cpus 1; al final se borra la red.
cd "$(dirname "$0")" || exit 1
export MSYS_NO_PATHCONV=1
IMG=cd799-py:1
RED=cd799-red
WEBHOOK="http://cd799-discord:9000/api/webhooks/123/token-falso"

limpiar() { docker rm -f cd799-sitios cd799-api cd799-discord >/dev/null 2>&1; docker network rm $RED >/dev/null 2>&1; }
marca() { docker exec cd799-discord python -c "import json,urllib.request as u;u.urlopen(u.Request('http://127.0.0.1:9000/marca',data=json.dumps({'texto':'$1'}).encode(),method='POST'))"; }
api_on() { docker run -d --rm --cpus 1 --name cd799-api --network $RED $IMG python -m http.server 8000 >/dev/null; }

corrida() {  # $1 = modo · $2 = LIMITAR (429 en el primer aviso)
  docker run -d --rm --cpus 1 --name cd799-discord --network $RED -e LIMITAR="$2" $IMG python discord_falso.py >/dev/null
  api_on; sleep 2
  echo "\$ python monitor.py $1"
  docker run --rm --cpus 1 --name cd799-monitor --network $RED -e DISCORD_WEBHOOK_URL="$WEBHOOK" -e SEGUNDOS=20 \
    $IMG python monitor.py "$1" > "_mon-$1.log" 2>&1 &
  PID=$!
  sleep 6;  marca "api se apaga (docker stop cd799-api)"; docker stop -t 1 cd799-api >/dev/null
  sleep 7;  marca "api vuelve (docker run cd799-api)"; api_on
  wait $PID
  cat "_mon-$1.log"; rm -f "_mon-$1.log"
  echo
  echo "--- lo que vio el Discord falso (su propio reloj) ---"
  docker logs cd799-discord 2>&1
  if [ "$1" = estados ]; then
    echo
    echo "--- el primer aviso, tal cual llegó (GET /recibido) ---"
    docker exec cd799-discord python -c "import json,urllib.request as u;print(json.dumps(json.load(u.urlopen('http://127.0.0.1:9000/recibido'))[0],ensure_ascii=False,indent=2))"
  fi
  docker rm -f cd799-discord cd799-api >/dev/null 2>&1
  echo
}

limpiar
docker build -q -t $IMG . >/dev/null || exit 1
docker network create $RED >/dev/null
docker run -d --rm --cpus 1 --name cd799-sitios --network $RED $IMG python sitios.py >/dev/null
sleep 2
{
  echo "# SALIDA — monitor de disponibilidad en Python (cultura-devops 799)"
  echo
  echo "> Corrida del $(date '+%Y-%m-%d %H:%M'). python:3.13.17-slim + httpx 0.28.1, cada contenedor con --cpus 1, red local cd799-red."
  echo "> Sitios: web (siempre 200) · api (contenedor aparte: se apaga con docker stop y vuelve) · pagos (500 una sí, una no) · lento (tarda 3 s)."
  echo "> El «Discord» es un servidor FALSO local que imita el webhook (POST JSON → 204; 429 con retry_after si LIMITAR=1)."
  echo "> No se usa ningún webhook real: nada se envía a Discord."
  echo
  echo '```'
  docker run --rm --cpus 1 $IMG python -c "import sys,httpx;print('Python',sys.version.split()[0],'· httpx',httpx.__version__)"
  echo
  corrida ingenuo ""
  corrida estados 1
  echo "\$ python monitor.py rondas"
  docker run --rm --cpus 1 --network $RED $IMG python monitor.py rondas 2>&1
  echo
  echo "\$ python monitor.py sin-timeout"
  docker run --rm --cpus 1 --network $RED $IMG python monitor.py sin-timeout 2>&1
  echo
  echo "\$ DISCORD_WEBHOOK_URL= python monitor.py entorno; echo \"salida: \$?\""
  docker run --rm --cpus 1 --network $RED -e DISCORD_WEBHOOK_URL= $IMG python monitor.py entorno 2>&1
  echo "salida: $?"
  echo '```'
} > SALIDA.md
limpiar
docker ps -a --filter name=cd799 --format '{{.Names}}'
cat SALIDA.md
