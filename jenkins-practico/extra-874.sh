#!/bin/bash
# Complemento de SALIDA-874: los volúmenes que declara la imagen del agente efímero. Escribe SALIDA-874-volumenes.md
cd "$(dirname "$0")" || exit 1
. ./comun.sh
{
echo "# SALIDA 874 (complemento) — volúmenes de la imagen del agente"
echo
echo "> Corrida del $(date '+%Y-%m-%d %H:%M')."
echo
echo '```'
echo "\$ docker image inspect $AGENTE_IMG --format '{{json .Config.Volumes}}'"
docker image inspect $AGENTE_IMG --format '{{json .Config.Volumes}}'
echo "\$ docker run -d --name jk-a-sin-removevolumes $AGENTE_IMG sleep 1 ; docker rm jk-a-sin-removevolumes   # borrar SIN -v"
ANTES=$(docker volume ls -q -f dangling=true | sort)
docker run -d --ulimit core=1 --name jk-a-sin-removevolumes --entrypoint sleep $AGENTE_IMG 1 >/dev/null; sleep 3
VOLS=$(docker inspect jk-a-sin-removevolumes --format '{{range .Mounts}}{{.Name}} {{end}}')
docker rm jk-a-sin-removevolumes >/dev/null
echo "volúmenes huérfanos nuevos: $(comm -13 <(echo "$ANTES") <(docker volume ls -q -f dangling=true | sort) | grep -c .)"
for v in $VOLS; do docker volume rm $v >/dev/null && echo "(borrado a mano: volumen anónimo ${v:0:12}…)"; done
echo '```'
} > SALIDA-874-volumenes.md
cat SALIDA-874-volumenes.md
