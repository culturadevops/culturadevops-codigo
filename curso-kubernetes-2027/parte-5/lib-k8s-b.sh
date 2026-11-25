#!/usr/bin/env bash
# Funciones comunes del banco de las partes 5-8 (clúster k8s-b). Se carga con «source».
# kubectl corre DENTRO del control-plane (v1.34.0, la misma versión que el servidor):
# el kubectl de Windows es v1.36 y queda fuera del desfase de versiones soportado.
export MSYS_NO_PATHCONV=1
CP=k8s-b-control-plane

# NS = namespace de la parte (se pasa con -n; un -n posterior manda). Sin tocar el contexto compartido.
k() { docker exec -i "$CP" kubectl ${NS:+-n "$NS"} "$@" 2>&1; }
# muestra el comando como en la terminal y lo ejecuta
x() { echo "\$ kubectl $*"; k "$@"; }
# aplica un manifiesto del disco (se manda por stdin)
aplicar() { echo "\$ kubectl apply -f $1"; docker exec -i "$CP" kubectl ${NS:+-n "$NS"} apply -f - < "$1" 2>&1; }
# reloj del clúster en milisegundos (la VM de Docker: el mismo reloj que ven los pods)
ms() { docker exec "$CP" date +%s%3N; }
titulo() { echo; echo "### $*"; }
nota() { echo "# $*"; }

encabezado() {
  echo "# SALIDA de la parte $1 · Curso de Kubernetes 2027 (cultura-devops)"
  echo
  echo "Generado: $(date -u '+%Y-%m-%d %H:%M:%S UTC') · script: $2"
  echo "Clúster: kind $(kind version | awk '{print $2}') · $(k version -o json | grep -m1 gitVersion | sed 's/.*: "\(.*\)".*/servidor \1/') · nodos: $(k get nodes --no-headers | wc -l)"
  echo "Contenedores de Docker vivos al empezar (ajenos a k8s-b): $(docker ps --format '{{.Names}}' | grep -v '^k8s-b-' | tr '\n' ' ' | sed 's/ $//')"
  [ -z "$(docker ps --format '{{.Names}}' | grep -v '^k8s-b-')" ] && echo "(ninguno)"
  echo
  echo '```'
}

pie() { echo '```'; }

# candado de mediciones de la fábrica
candado_tomar() {
  local t0; t0=$(date +%s)
  until mkdir <proyecto>/_logs/banco.lock 2>/dev/null; do sleep 15; done
  echo "agente B (curso k8s partes 5-8) $(date)" > <proyecto>/_logs/banco.lock/quien.txt
  trap 'rm -f <proyecto>/_logs/banco.lock/quien.txt; rmdir <proyecto>/_logs/banco.lock 2>/dev/null' EXIT
  echo "# candado banco.lock tomado $(date -u '+%H:%M:%S UTC') tras esperar $(( $(date +%s) - t0 )) s · contenedores ajenos vivos: $(docker ps --format '{{.Names}}' | grep -v '^k8s-b-' | tr '
' ' ')"
}
candado_soltar() { rm -f <proyecto>/_logs/banco.lock/quien.txt; rmdir <proyecto>/_logs/banco.lock 2>/dev/null; trap - EXIT; echo "# candado banco.lock soltado $(date -u '+%H:%M:%S UTC')"; }
