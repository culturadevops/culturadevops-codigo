# -*- coding: utf-8 -*-
"""k9s — banco de pruebas del vídeo 332 (cultura-devops, serie herramientas).

k3s en Docker (../lab-k8s/lab.py) + un contenedor con k9s v0.51.0, kubectl y ttyd (terminal web).
Playwright abre la terminal y teclea los atajos de k9s; cada paso, una captura a
motor/remotion/public/om-projects/cultura-devops/k9s/. Lo que se comprueba por kubectl va a SALIDA.md.

    python correr.py
"""
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "lab-k8s"))
import lab as L  # noqa: E402

PUB = Path(r"<proyecto>\motor\remotion\public\om-projects\cultura-devops\k9s")
K9S = "v0.51.0"
KUBECTL = "v1.37.1"
salida = []

DOCKERFILE = f"""FROM debian:bookworm-slim
RUN apt-get update -qq && apt-get install -y -qq curl ca-certificates >/dev/null \\
 && curl -sL https://github.com/derailed/k9s/releases/download/{K9S}/k9s_Linux_amd64.tar.gz | tar xz -C /usr/local/bin k9s \\
 && curl -sLo /usr/local/bin/kubectl https://dl.k8s.io/release/{KUBECTL}/bin/linux/amd64/kubectl && chmod +x /usr/local/bin/kubectl \\
 && curl -sLo /usr/local/bin/ttyd https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.x86_64 && chmod +x /usr/local/bin/ttyd
ENV TERM=xterm-256color
"""

CARGAS = """apiVersion: apps/v1
kind: Deployment
metadata: {name: web, namespace: tienda}
spec:
  replicas: 3
  selector: {matchLabels: {app: web}}
  template:
    metadata: {labels: {app: web}}
    spec:
      containers:
        - name: nginx
          image: nginx:1.29-alpine
---
apiVersion: apps/v1
kind: Deployment
metadata: {name: pagos, namespace: tienda}
spec:
  replicas: 1
  selector: {matchLabels: {app: pagos}}
  template:
    metadata: {labels: {app: pagos}}
    spec:
      containers:
        - name: api
          image: busybox:1.37
          command: ["sh", "-c", "echo 'conectando a la base de datos...'; sleep 3; echo 'ERROR: no encuentro DB_PASSWORD' >&2; exit 1"]
---
apiVersion: v1
kind: Service
metadata: {name: web, namespace: tienda}
spec:
  selector: {app: web}
  ports: [{port: 80}]
"""


def sh(cmd, timeout=900, entrada=None):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout, input=entrada)
    return (r.stdout + r.stderr).strip()


def anota(titulo, cmd_txt, texto):
    salida.extend(["", f"### {titulo}", "", f"`$ {cmd_txt}`", "", "```", texto.strip(), "```"])
    print(f"--- {titulo}\n{texto.strip()[:1500]}\n", flush=True)


def main():
    print(sh(["docker", "build", "-q", "-t", "lab-k9s", "-"], entrada=DOCKERFILE, timeout=1800))
    L.levantar()
    sh(["docker", "rm", "-f", "k9s"])
    L.k("create", "namespace", "tienda")
    L.k("apply", "-f", "-", entrada=CARGAS)
    time.sleep(40)
    anota("las cargas", "kubectl get pods -n tienda", L.k("get", "pods", "-n", "tienda"))

    salida.append("\n## 1 · k9s en una terminal web")
    kube = L.k("config", "view", "--raw").replace("127.0.0.1", L.K3S_IP)
    Path(AQUI / "_kubeconfig").write_text(kube, encoding="utf-8")
    sh(["docker", "run", "-d", "--name", "k9s", "--network", L.RED, "-p", "7681:7681",
        "-v", f"{AQUI / '_kubeconfig'}:/root/.kube/config:ro", "lab-k9s",
        "ttyd", "-W", "-t", "fontSize=17", "-t", "rendererType=dom", "bash"])
    time.sleep(3)
    anota("versiones", "k9s version -s; kubectl version --client",
          sh(["docker", "exec", "k9s", "sh", "-c", "k9s version -s; kubectl version --client | head -1"]))
    PUB.mkdir(parents=True, exist_ok=True)
    r = sh(["node", str(AQUI / "teclear.js"), str(PUB)], timeout=900)
    anota("capturas", "node teclear.js", r)

    salida.append("\n## 2 · Lo que se hizo desde k9s, comprobado con kubectl")
    anota("pods después de borrar uno con ctrl-d", "kubectl get pods -n tienda -l app=web",
          L.k("get", "pods", "-n", "tienda", "-l", "app=web"))
    anota("réplicas después de escalar desde k9s", "kubectl get deploy -n tienda",
          L.k("get", "deploy", "-n", "tienda"))
    anota("logs del que falla", "kubectl logs -n tienda deploy/pagos --previous",
          L.k("logs", "-n", "tienda", "deploy/pagos", "--previous"))
    anota("eventos", "kubectl get events -n tienda --field-selector reason=Killing",
          L.k("get", "events", "-n", "tienda", "--field-selector", "reason=Killing"))
    anota("modo solo lectura", "k9s --readonly (¿deja borrar?)", "ver captura 09-readonly")

    sh(["docker", "rm", "-f", "k9s"])
    (AQUI / "_kubeconfig").unlink(missing_ok=True)
    L.limpiar()
    cab = ["# SALIDA — k9s (vídeo 332)", "",
           f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. "
           f"k3s en Docker, k9s {K9S}, kubectl {KUBECTL}, ttyd 1.7.7."]
    (AQUI / "SALIDA.md").write_text("\n".join(cab + salida) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
