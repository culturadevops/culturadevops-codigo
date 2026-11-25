# -*- coding: utf-8 -*-
"""Demo de «Helm en 5 minutos» (cultura-devops). Kubernetes de un nodo (k3s v1.37.1) en Docker; helm v4.3.1 y kubectl
dentro de un contenedor Alpine en la misma red (en Windows, App Control bloquea binarios descargados).
  · helm create: qué trae un chart;
  · install, upgrade, una actualización que falla (imagen inexistente), history y rollback.
    python correr.py   -> SALIDA.md          (el clúster se borra al terminar; --dejar lo deja para la demo de Argo CD)
"""
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
K3S, HELM, KUBECTL = "rancher/k3s:v1.37.1-k3s1", "v4.3.1", "v1.37.1"
OUT = []


def run(args, entrada=None):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", input=entrada)
    return (p.stdout + p.stderr).strip(), p.returncode


def ex(cmd):
    return run(["docker", "exec", "herr5", "sh", "-c", cmd])


def bloque(titulo, mostrado, cmd, nota=None):
    s, rc = ex(cmd)
    OUT.append(f"### {titulo}\n\n`$ {mostrado}`\n\n```\n{s}\n```\n(código de salida {rc})\n" + (f"\n> {nota}\n" if nota else ""))
    print(f"[{rc}] {titulo}")
    return s, rc


def levantar_lab():
    """k3s5 + herr5 en la red lab5. Lo usan también la demo de Argo CD."""
    for c in ("k3s5", "herr5"):
        run(["docker", "rm", "-f", c])
    run(["docker", "network", "rm", "lab5"])
    run(["docker", "network", "create", "lab5"])
    run(["docker", "run", "-d", "--name", "k3s5", "--hostname", "k3s5", "--network", "lab5", "--privileged", K3S,
         "server", "--disable", "traefik", "--disable", "metrics-server", "--tls-san", "k3s5"])
    run(["docker", "run", "-d", "--name", "herr5", "--network", "lab5", "alpine:3.22", "sleep", "infinity"])
    ex("apk add -q curl git jq >/dev/null")
    ex(f"curl -sL https://get.helm.sh/helm-{HELM}-linux-amd64.tar.gz | tar xz -C /tmp && mv /tmp/linux-amd64/helm /usr/local/bin/helm")
    ex(f"curl -sLo /usr/local/bin/kubectl https://dl.k8s.io/release/{KUBECTL}/bin/linux/amd64/kubectl && chmod +x /usr/local/bin/kubectl")
    for _ in range(90):
        kc, rc = run(["docker", "exec", "k3s5", "cat", "/etc/rancher/k3s/k3s.yaml"])
        if rc == 0 and "server:" in kc:
            break
        time.sleep(2)
    run(["docker", "exec", "-i", "herr5", "sh", "-c", "mkdir -p /root/.kube && cat > /root/.kube/config"],
        entrada=kc.replace("127.0.0.1", "k3s5"))
    for _ in range(90):
        s, _ = ex("kubectl get serviceaccount default -o name 2>/dev/null")
        if "serviceaccount/default" in s:
            break
        time.sleep(2)


def main():
    levantar_lab()
    OUT.append(f"# SALIDA — Helm en 5 minutos (cultura-devops)\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con "
               f"`python correr.py`. k3s `{K3S}` en Docker; helm {HELM} y kubectl {KUBECTL} en un contenedor Alpine.\n")
    OUT.append("## 1 · Versiones\n")
    bloque("helm y el clúster", "helm version --short; kubectl get nodes", "helm version --short; kubectl get nodes")

    OUT.append("## 2 · Un chart\n")
    ex("cd /tmp && rm -rf tienda && helm create tienda >/dev/null")
    bloque("helm create tienda", "helm create tienda; find tienda -maxdepth 2 | sort", "cd /tmp && find tienda -maxdepth 2 | sort")
    bloque("lo que se puede cambiar (values.yaml)", "grep -E -A3 '^replicaCount|^image:' tienda/values.yaml",
           "cd /tmp && grep -E -A3 '^replicaCount|^image:' tienda/values.yaml | grep -v '^ *#'")
    bloque("y la versión de la app", "grep appVersion tienda/Chart.yaml", "cd /tmp && grep appVersion tienda/Chart.yaml")

    OUT.append("## 3 · Instalar, actualizar, romper y volver atrás\n")
    bloque("instalar", "helm install tienda ./tienda --set image.tag=1.31-alpine --wait",
           "cd /tmp && helm install tienda ./tienda --set image.tag=1.31-alpine --wait --timeout 180s 2>&1 | grep -E '^(NAME|STATUS|REVISION)'")
    bloque("lo que creó", "kubectl get deploy,svc -l app.kubernetes.io/instance=tienda",
           "kubectl get deploy,svc -l app.kubernetes.io/instance=tienda")
    bloque("actualizar: 3 réplicas", "helm upgrade tienda ./tienda --reuse-values --set replicaCount=3 --wait",
           "cd /tmp && helm upgrade tienda ./tienda --reuse-values --set replicaCount=3 --wait --timeout 180s 2>&1 | grep -E '^(STATUS|REVISION)'; "
           "kubectl get deploy tienda")
    t0 = time.time()
    bloque("una versión que no existe", "helm upgrade tienda ./tienda --reuse-values --set image.tag=no-existe --wait --timeout 40s",
           "cd /tmp && helm upgrade tienda ./tienda --reuse-values --set image.tag=no-existe --wait --timeout 40s 2>&1 | tail -2")
    print(f"   (fallo en {time.time() - t0:.1f} s)")
    bloque("¿y los pods?", "kubectl get pods -l app.kubernetes.io/instance=tienda",
           "kubectl get pods -l app.kubernetes.io/instance=tienda -o custom-columns=POD:.metadata.name,ESTADO:.status.containerStatuses[0].state.waiting.reason,LISTO:.status.containerStatuses[0].ready")
    bloque("el historial", "helm history tienda", "helm history tienda")
    bloque("volver a la revisión 2", "helm rollback tienda 2 --wait",
           "helm rollback tienda 2 --wait --timeout 180s; kubectl get deploy tienda; "
           "kubectl get deploy tienda -o jsonpath='imagen: {.spec.template.spec.containers[0].image}'")
    bloque("el historial después", "helm history tienda", "helm history tienda")
    bloque("y borrar todo", "helm uninstall tienda; kubectl get all -l app.kubernetes.io/instance=tienda",
           "helm uninstall tienda --wait; kubectl get all -l app.kubernetes.io/instance=tienda")

    (AQUI / "SALIDA.md").write_text("\n".join(OUT), encoding="utf-8")
    if "--dejar" not in sys.argv:
        for c in ("k3s5", "herr5"):
            run(["docker", "rm", "-f", c])
        run(["docker", "network", "rm", "lab5"])
    print("ok SALIDA.md")


if __name__ == "__main__":
    main()
