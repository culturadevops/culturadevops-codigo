#!/bin/bash
# Construye la imagen y corre las 4 demos de la tanda evergreen de Linux (cultura-devops, 2026-10-23). Desde Git Bash:
#   bash canales/cultura-devops/recursos/demo-linux-evergreen/ejecutar.sh
# Deja SALIDA-comandos.md, SALIDA-bash.md, SALIDA-disco.md y SALIDA-entorno.md con la salida literal, y borra el contenedor.
cd "$(dirname "$0")" || exit 1
export MSYS_NO_PATHCONV=1
docker build -q -t demo-linux-evergreen:1 . >/dev/null || exit 1
VERSION=$(docker run --rm demo-linux-evergreen:1 sh -c '. /etc/os-release; echo "$PRETTY_NAME, $(bash --version | head -1)"')
for demo in comandos bash disco entorno; do
  docker rm -f demo-linux >/dev/null 2>&1
  docker run -d --name demo-linux --hostname servidor \
    --tmpfs /datos:rw,size=20m --tmpfs /inodos:rw,size=50m,nr_inodes=200 \
    -v "$PWD/$demo.sh:/demo.sh:ro" demo-linux-evergreen:1 >/dev/null
  {
    echo "# SALIDA — $demo (cultura-devops, tanda evergreen de Linux)"
    echo
    echo "> Corrida del $(date '+%Y-%m-%d %H:%M') en un contenedor: $VERSION."
    echo
    echo '```'
    if [ $demo = comandos ]; then docker exec -u ana -w /home/ana demo-linux bash /demo.sh; else docker exec demo-linux bash /demo.sh; fi
    echo '```'
  } > "SALIDA-$demo.md"
  docker rm -f demo-linux >/dev/null 2>&1
done
ls -l SALIDA-*.md
