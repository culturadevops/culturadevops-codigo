# -*- coding: utf-8 -*-
"""Banco del vídeo 407 «¿Vale la pena Helm en 2027?». Helm 3.22.0 contra Helm 4.3.0 sobre un k3s en Docker.

Necesita el contenedor k3s (red lab-k8s). Las herramientas se bajan DENTRO de un contenedor Linux (herr): en Windows,
App Control bloquea binarios descargados.
    python correr.py   -> SALIDA.md
"""
import subprocess
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
OUT = []
H3, H4 = "v3.22.0", "v4.3.0"


def sh(cmd):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (p.stdout + p.stderr).strip(), p.returncode


def ex(cmd):
    p = subprocess.run(["docker", "exec", "herr", "sh", "-c", cmd], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return (p.stdout + p.stderr).strip(), p.returncode


def bloque(titulo, mostrado, cmd):
    s, rc = ex(cmd)
    OUT.append(f"### {titulo}\n\n`$ {mostrado}`\n\n```\n{s}\n```\n(código de salida {rc})\n")
    print(f"[{rc}] {titulo}")
    return s, rc


def preparar():
    sh("docker rm -f herr")
    sh("docker run -d --name herr --network lab-k8s alpine:3.22 sleep infinity")
    ex("apk add -q curl jq >/dev/null")
    for v, n in ((H3, "helm3"), (H4, "helm4")):
        ex(f"curl -sL https://get.helm.sh/helm-{v}-linux-amd64.tar.gz | tar xz -C /tmp && mv /tmp/linux-amd64/helm /usr/local/bin/{n}")
    ex("curl -sLo /usr/local/bin/kubectl https://dl.k8s.io/release/v1.34.1/bin/linux/amd64/kubectl && chmod +x /usr/local/bin/kubectl")
    kc, _ = sh("docker exec k3s cat /etc/rancher/k3s/k3s.yaml")
    (AQUI / "_kubeconfig").write_text(kc.replace("127.0.0.1", "k3s"), encoding="utf-8")
    sh(f'docker exec herr mkdir -p /root/.kube && docker cp "{AQUI / "_kubeconfig"}" herr:/root/.kube/config')


def main():
    preparar()
    OUT.append(f"# SALIDA — Helm 3 contra Helm 4 (vídeo 407)\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. "
               "Clúster k3s en Docker; Helm y kubectl dentro de un contenedor Alpine.\n")
    OUT.append("## 1 · Versiones\n")
    bloque("las dos versiones", "helm3 version; helm4 version", "helm3 version --short; helm4 version --short")
    bloque("el clúster", "kubectl get nodes", "kubectl get nodes")

    OUT.append("## 2 · Empaquetar el mismo chart dos veces\n")
    ex("cd /tmp && rm -rf demo && helm4 create demo >/dev/null")
    bloque("Helm 3: dos paquetes, ¿mismo hash?", "helm3 package demo (dos veces); sha256sum",
           "cd /tmp && helm3 package demo -d p3a >/dev/null && sleep 2 && helm3 package demo -d p3b >/dev/null && sha256sum p3a/*.tgz p3b/*.tgz")
    bloque("Helm 4: lo mismo", "helm4 package demo (dos veces); sha256sum",
           "cd /tmp && helm4 package demo -d p4a >/dev/null && sleep 2 && helm4 package demo -d p4b >/dev/null && sha256sum p4a/*.tgz p4b/*.tgz")

    OUT.append("## 3 · Instalar el mismo chart\n")
    bloque("Helm 3", "helm3 install web3 ./demo -n h3 --create-namespace --wait",
           "cd /tmp && helm3 install web3 ./demo -n h3 --create-namespace --wait 2>&1 | grep STATUS")
    bloque("Helm 4", "helm4 install web4 ./demo -n h4 --create-namespace --wait",
           "cd /tmp && helm4 install web4 ./demo -n h4 --create-namespace --wait 2>&1 | grep STATUS")
    bloque("quién gestiona los campos (Helm 3)", "kubectl get deploy -n h3 -o jsonpath=…managedFields",
           "kubectl get deploy web3-demo -n h3 --show-managed-fields -o jsonpath=\"{range .metadata.managedFields[*]}{.manager} {.operation}{\\\"\\n\\\"}{end}\"")
    bloque("quién gestiona los campos (Helm 4)", "kubectl get deploy -n h4 -o jsonpath=…managedFields",
           "kubectl get deploy web4-demo -n h4 --show-managed-fields -o jsonpath=\"{range .metadata.managedFields[*]}{.manager} {.operation}{\\\"\\n\\\"}{end}\"")

    OUT.append("## 4 · Alguien toca el clúster a mano\n")
    bloque("escalar a 3 réplicas con kubectl", "kubectl scale deploy --replicas=3 (en h3 y h4)",
           "kubectl scale deploy web3-demo -n h3 --replicas=3 && kubectl scale deploy web4-demo -n h4 --replicas=3")
    bloque("Helm 3: upgrade sin cambiar nada", "helm3 upgrade web3 ./demo -n h3; réplicas",
           "cd /tmp && helm3 upgrade web3 ./demo -n h3 --wait >/dev/null; echo \"código $?\"; kubectl get deploy web3-demo -n h3 -o jsonpath=\"réplicas={.spec.replicas}\"")
    bloque("Helm 4: upgrade sin cambiar nada", "helm4 upgrade web4 ./demo -n h4; réplicas",
           "cd /tmp && helm4 upgrade web4 ./demo -n h4 --wait > /tmp/o 2>&1; echo \"código $?\"; grep ^Error /tmp/o; kubectl get deploy web4-demo -n h4 -o jsonpath=\"réplicas={.spec.replicas}\"")
    bloque("Helm 4: upgrade con --force-conflicts", "helm4 upgrade web4 ./demo -n h4 --force-conflicts; réplicas",
           "cd /tmp && helm4 upgrade web4 ./demo -n h4 --wait --force-conflicts > /tmp/o 2>&1; echo \"código $?\"; kubectl get deploy web4-demo -n h4 -o jsonpath=\"réplicas={.spec.replicas}\"")

    OUT.append("## 5 · Lo que guarda Helm del despliegue\n")
    bloque("historial", "helm4 history web4 -n h4", "helm4 history web4 -n h4")
    bloque("dónde lo guarda", "kubectl get secrets -n h4 -l owner=helm", "kubectl get secrets -n h4 -l owner=helm")
    bloque("volver atrás", "helm4 rollback web4 1 -n h4", "helm4 rollback web4 1 -n h4 --wait && helm4 history web4 -n h4 | tail -2")

    OUT.append("## 6 · La alternativa que ya viene en kubectl\n")
    bloque("kustomize dentro de kubectl", "kubectl version --client; kubectl kustomize --help | head -3",
           "kubectl version --client | head -2; kubectl kustomize --help | head -3")

    (AQUI / "SALIDA.md").write_text("\n".join(OUT), encoding="utf-8")
    ex("helm3 uninstall web3 -n h3; helm4 uninstall web4 -n h4")
    print("ok SALIDA.md")


if __name__ == "__main__":
    main()
