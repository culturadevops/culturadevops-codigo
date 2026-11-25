# Funciones comunes de las partes 1-4 (clúster k8s-a). Se cargan con «. ../comun/lib.sh».
# kubectl es el del propio nodo (v1.34.0, la misma versión que el clúster): el kubectl de la
# máquina es v1.36 y queda fuera del margen de versiones que Kubernetes soporta (±1).
export MSYS_NO_PATHCONV=1
NODO=k8s-a-control-plane
k() { docker exec -i -e KUBECONFIG=/etc/kubernetes/admin.conf "$NODO" kubectl "$@" 2>&1; }
# Igual que k, pero lee el manifiesto por la entrada estándar: kapply archivo.yaml
kapply() { docker exec -i -e KUBECONFIG=/etc/kubernetes/admin.conf "$NODO" kubectl apply -f - < "$1" 2>&1; }
# Lo que se enseña como comando: «$ kubectl …»
muestra() { echo "\$ $*"; }
titulo() { echo; echo "### $*"; }
# Milisegundos desde la época (date de Git Bash admite %N)
ms() { date +%s%3N; }
# Una consola dentro del nodo, para bucles de medición sin pagar un docker exec por muestra
nodo_sh() { docker exec -i -e KUBECONFIG=/etc/kubernetes/admin.conf "$NODO" sh -c "$1" 2>&1; }
# Espera a que no exista nada en el namespace (para empezar limpio)
ns_nuevo() { k delete namespace "$1" --ignore-not-found --wait=true >/dev/null; k create namespace "$1" >/dev/null; }
# Contenedores ajenos vivos (para la nota de la SALIDA)
ajenos() { docker ps --format '{{.Names}}' | grep -v '^k8s-a-' | tr '\n' ' '; }
