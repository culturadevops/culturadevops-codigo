#!/bin/sh
# ⚠️ La regla de cgroups v2: un grupo NO puede tener procesos y delegar controladores a la vez.
#    Dentro de un contenedor, el proceso 1 está en la raíz, así que Nomad no puede escribir en
#    `cgroup.subtree_control` y muere con «device or resource busy». La cura es mover el proceso
#    a un subgrupo y dejar la raíz libre para que delegue.
set -e
mkdir -p /sys/fs/cgroup/init
for p in $(cat /sys/fs/cgroup/cgroup.procs 2>/dev/null); do
  echo "$p" > /sys/fs/cgroup/init/cgroup.procs 2>/dev/null || true
done
echo "+cpuset +cpu +io +memory +pids" > /sys/fs/cgroup/cgroup.subtree_control 2>/dev/null || true
exec nomad agent -dev -bind 0.0.0.0
