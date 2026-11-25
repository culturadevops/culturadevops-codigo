#!/usr/bin/env bash
# demo.sh — la medición del vídeo 230 «Nomad, ¿la alternativa a Kubernetes este 2026?».
#
# ⚠️ LA ELECCIÓN QUE HAY QUE DECIR EN VOZ ALTA: se compara Nomad contra **k3s**, no contra un
#    Kubernetes de tres maestros ni contra un servicio gestionado. Motivo: k3s es la comparación
#    JUSTA — una sola pieza, pensada para lo mismo que un Nomad de un nodo. Comparar Nomad
#    contra un clúster de producción sería tramposo en un sentido, y contra un servicio
#    gestionado, en el otro. Se dice en el vídeo.
#
# ⛔ Y ANTES DE COMPARAR NADA se comprueba que los dos llegaron al MISMO estado: 2 réplicas
#    corriendo. En el vídeo 229 cuatro corridas dieron números plausibles y falsos por saltarse
#    justo esto.
set -u
D=$(cd "$(dirname "$0")" && pwd -W)

limpiar() {
  docker rm -f nomad k3s >/dev/null 2>&1
  # ⚠️ Y los contenedores que levantó Nomad: no son suyos hijos para Docker, así que sobreviven
  #    al borrar el agente y falsearían el recuento de la siguiente corrida.
  n=$(docker ps -aq --filter ancestor=nginx:alpine)
  [ -n "$n" ] && docker rm -f $n >/dev/null 2>&1
  return 0
}
limpiar

echo "== 1 · LINEAS DE CONFIGURACION para el mismo servicio =="
echo -n "   Nomad (web.nomad.hcl):  "; grep -vcE '^\s*(#|$)' "$D/web.nomad.hcl"
echo -n "   Kubernetes (web.k8s.yaml): "; grep -vcE '^\s*(#|$)' "$D/web.k8s.yaml"

echo
echo "== 2 · LO QUE TE BAJAS =="
docker pull -q hashicorp/nomad:1.9 >/dev/null 2>&1
docker pull -q rancher/k3s:v1.31.3-k3s1 >/dev/null 2>&1
echo -n "   imagen de Nomad: "; docker images hashicorp/nomad:1.9 --format '{{.Size}}'
echo -n "   imagen de k3s:   "; docker images rancher/k3s:v1.31.3-k3s1 --format '{{.Size}}'

echo
echo "== 3 · DE CERO A «EL SERVICIO RESPONDE» =="

echo "   --- Nomad ---"
t0=$(date +%s%N)
# ⚠️ `--cgroupns=private` y el guion de arranque: sin ellos Nomad muere al segundo con
#    «failed to create nomad cgroup: device or resource busy». Es la regla de cgroups v2 —un
#    grupo no puede tener procesos y delegar controladores a la vez— y no tiene NADA que ver
#    con Nomad contra Kubernetes. Va en el vídeo como tropiezo, no como diferencia.
docker run -d --name nomad --privileged --cgroupns=private \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$D:/w" -p 4646:4646 --entrypoint sh hashicorp/nomad:1.9 /w/arranca-nomad.sh >/dev/null
for i in $(seq 1 120); do
  docker exec nomad nomad node status 2>/dev/null | grep -q ready && break; sleep 1
done
docker exec nomad nomad job run /w/web.nomad.hcl >/dev/null 2>&1
for i in $(seq 1 180); do
  docker exec nomad nomad job status -short web 2>/dev/null | grep -q 'Status *= *running' && break; sleep 1
done
t1=$(date +%s%N); NOM=$(( (t1-t0)/1000000000 ))
echo "      listo en ${NOM} s"

echo "   --- k3s ---"
t0=$(date +%s%N)
docker run -d --name k3s --privileged -v "$D:/w" \
  rancher/k3s:v1.31.3-k3s1 server --disable-agent=false --disable=traefik,servicelb,metrics-server >/dev/null
for i in $(seq 1 240); do
  docker exec k3s kubectl get nodes 2>/dev/null | grep -q Ready && break; sleep 2
done
docker exec k3s kubectl apply -f /w/web.k8s.yaml 2>&1 | sed "s/^/      /"
for i in $(seq 1 240); do
  n=$(docker exec k3s kubectl get deploy web -o jsonpath='{.status.readyReplicas}' 2>/dev/null)
  [ "${n:-0}" -ge 2 ] && break; sleep 2
done
t1=$(date +%s%N); K3S=$(( (t1-t0)/1000000000 ))
echo "      listo en ${K3S} s"

echo
echo "== 4 · ⛔ ¿LLEGARON LOS DOS AL MISMO ESTADO? =="
echo -n "   Nomad, replicas sanas: "
docker exec nomad nomad job status -short web 2>/dev/null \
  | grep -A1 '^Task Group' | tail -1 | awk '{print $4}'
echo -n "   k3s, réplicas listas:          "
docker exec k3s kubectl get deploy web -o jsonpath='{.status.readyReplicas}' 2>/dev/null; echo
echo -n "   nginx que ve el Docker de la maquina (los de Nomad): "
docker ps --filter ancestor=nginx:alpine --format '{{.ID}}' | wc -l
# ⚠️ Los de k3s NO los ve el Docker de la maquina: corren dentro de SU propio containerd.
#    Contarlos ahi arriba daria 2 y parecerian los de todos. Se cuentan donde estan.
echo -n "   nginx dentro del containerd de k3s:                 "
docker exec k3s crictl ps --name servidor -q 2>/dev/null | wc -l

echo
echo "== 5 · MEMORIA DEL PLANO DE CONTROL =="
docker stats --no-stream --format '   {{.Name}}: {{.MemUsage}}' nomad k3s

echo
echo "== 6 · CUANTAS PIEZAS HAY QUE TENER VIVAS =="
echo -n "   procesos dentro del contenedor de Nomad: "
docker exec nomad ps -eo comm 2>/dev/null | tail -n +2 | sort -u | wc -l
echo -n "   procesos dentro del contenedor de k3s:   "
docker exec k3s ps -eo comm 2>/dev/null | tail -n +2 | sort -u | wc -l
echo "   piezas de k3s que se ven por nombre:"
docker exec k3s ps -eo comm 2>/dev/null | tail -n +2 | sort -u | head -12 | sed 's/^/     /'
echo -n "   pods del sistema que k3s levanta solo: "
docker exec k3s kubectl get pods -A --no-headers 2>/dev/null | wc -l

limpiar
echo
echo "== limpio =="
