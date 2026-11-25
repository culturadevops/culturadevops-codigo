# -*- coding: utf-8 -*-
"""Banco del vídeo 408 «¿Vale la pena Argo CD en 2027?». Argo CD v3.5.5 sobre k3s en Docker, con un Gitea propio como
repositorio (para poder hacer commits). Necesita los contenedores k3s y herr del banco de Helm (red lab-k8s).
    python correr.py   -> SALIDA.md
"""
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
OUT = []
ARGO = "v3.5.5"
REPO = "http://GITEA_IP:3000/lab/apps.git"   # IP: los pods de k3s no resuelven los nombres de la red de Docker


def run(args):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (p.stdout + p.stderr).strip(), p.returncode


def ex(cmd):
    return run(["docker", "exec", "herr", "sh", "-c", cmd])


def bloque(titulo, mostrado, cmd, nota=None):
    s, rc = ex(cmd)
    OUT.append(f"### {titulo}\n\n`$ {mostrado}`\n\n```\n{s}\n```\n(código de salida {rc})\n" + (f"\n> {nota}\n" if nota else ""))
    print(f"[{rc}] {titulo}")
    return s, rc


def esperar(cond_cmd, esperado, tope=400):
    t0 = time.time()
    while time.time() - t0 < tope:
        s, _ = ex(cond_cmd)
        if s.strip() == esperado:
            return round(time.time() - t0, 1)
        time.sleep(2)
    return None


DEPLOY = """apiVersion: apps/v1
kind: Deployment
metadata: {name: web}
spec:
  replicas: REPL
  selector: {matchLabels: {app: web}}
  template:
    metadata: {labels: {app: web}}
    spec:
      containers: [{name: web, image: nginx:1.29-alpine}]
"""
CM = """apiVersion: v1
kind: ConfigMap
metadata: {name: ajustes}
data: {modo: produccion}
"""
APP = f"""apiVersion: argoproj.io/v1alpha1
kind: Application
metadata: {{name: web, namespace: argocd}}
spec:
  project: default
  source: {{repoURL: {REPO}, targetRevision: main, path: web}}
  destination: {{server: https://kubernetes.default.svc, namespace: tienda}}
  syncPolicy:
    automated: {{prune: true, selfHeal: true}}
    syncOptions: [CreateNamespace=true]
"""


def git_commit(msg, repl, con_cm=True):
    ex(f"cd /repo && mkdir -p web && cat > web/deploy.yaml <<'EOF'\n{DEPLOY.replace('REPL', str(repl))}EOF\n"
       + (f"cat > web/ajustes.yaml <<'EOF'\n{CM}EOF\n" if con_cm else "rm -f web/ajustes.yaml\n")
       + f"git add -A && git commit -qm '{msg}' && git push -q origin main")


def main():
    run(["docker", "rm", "-f", "gitea"])
    run(["docker", "run", "-d", "--name", "gitea", "--network", "lab-k8s", "-e", "GITEA__security__INSTALL_LOCK=true",
         "-e", "GITEA__server__ROOT_URL=http://gitea:3000/", "gitea/gitea:latest"])
    time.sleep(12)
    global REPO, APP
    ip, _ = run(["docker", "inspect", "-f", "{{(index .NetworkSettings.Networks \"lab-k8s\").IPAddress}}", "gitea"])
    REPO = REPO.replace("GITEA_IP", ip.strip())
    APP = APP.replace("http://GITEA_IP:3000/lab/apps.git", REPO)
    run(["docker", "exec", "-u", "git", "gitea", "gitea", "admin", "user", "create", "--username", "lab", "--password",
         "lab12345", "--email", "lab@lab.local", "--admin", "--must-change-password=false"])
    ex("apk add -q git curl >/dev/null; curl -s -u lab:lab12345 -H 'Content-Type: application/json' "
       "-d '{\"name\":\"apps\",\"default_branch\":\"main\"}' http://gitea:3000/api/v1/user/repos >/dev/null; "
       "rm -rf /repo && git init -q -b main /repo && cd /repo && git config user.email lab@lab.local && git config user.name lab "
       "&& git remote add origin http://lab:lab12345@gitea:3000/lab/apps.git")
    git_commit("web con 2 réplicas", 2)

    OUT.append(f"# SALIDA — Argo CD (vídeo 408)\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. "
               f"k3s en Docker, Argo CD {ARGO} con su manifiesto oficial, Gitea propio como repositorio.\n")
    OUT.append("## 1 · Instalar Argo CD\n")
    ex("kubectl delete ns argocd tienda --ignore-not-found --wait=true >/dev/null 2>&1; kubectl create ns argocd")
    bloque("el manifiesto oficial", f"kubectl apply -n argocd --server-side -f …/argo-cd/{ARGO}/manifests/install.yaml | tail -3",
           f"kubectl apply -n argocd --server-side --force-conflicts -f https://raw.githubusercontent.com/argoproj/argo-cd/{ARGO}/manifests/install.yaml | tail -3")
    t0 = time.time()
    ex("kubectl wait -n argocd --for=condition=Available deploy --all --timeout=400s >/dev/null; "
       "kubectl wait -n argocd --for=condition=Ready pod -l app.kubernetes.io/name=argocd-application-controller --timeout=400s >/dev/null")
    OUT.append(f"> Todo listo a los {round(time.time() - t0)} s (incluye bajar las imágenes).\n")
    bloque("lo que instala", "kubectl get pods -n argocd", "kubectl get pods -n argocd")
    bloque("la versión", "kubectl get deploy argocd-server -n argocd -o jsonpath=…image",
           "kubectl get deploy argocd-server -n argocd -o jsonpath=\"{.spec.template.spec.containers[0].image}\"")

    OUT.append("## 2 · Una aplicación que vive en Git\n")
    bloque("lo que hay en el repositorio", "git log --oneline; ls web/", "cd /repo && git log --oneline && ls web/")
    ex(f"cat > /tmp/app.yaml <<'EOF'\n{APP}EOF")
    bloque("la Application (automatizada, con prune y selfHeal)", "kubectl apply -f app.yaml", "kubectl apply -f /tmp/app.yaml && cat /tmp/app.yaml")
    t = esperar("kubectl get application web -n argocd -o jsonpath=\"{.status.sync.status}/{.status.health.status}\"", "Synced/Healthy")
    OUT.append(f"> Synced y Healthy a los {t} s.\n")
    bloque("lo que creó en el clúster", "kubectl get deploy,cm -n tienda", "kubectl get deploy,configmap -n tienda")

    OUT.append("## 3 · Alguien lo cambia a mano\n")
    bloque("escalar a 5 con kubectl", "kubectl scale deploy web -n tienda --replicas=5", "kubectl scale deploy web -n tienda --replicas=5")
    t = esperar("kubectl get deploy web -n tienda -o jsonpath=\"{.spec.replicas}\"", "2", 300)
    OUT.append(f"> selfHeal: volvió a 2 réplicas a los {t} s.\n")
    bloque("el historial de la aplicación", "kubectl get application web -n argocd -o jsonpath=…status.operationState",
           "kubectl get application web -n argocd -o jsonpath=\"{.status.operationState.message} · {.status.operationState.syncResult.revision}\"")

    OUT.append("## 4 · Un commit en Git\n")
    git_commit("web con 3 réplicas", 3)
    bloque("el commit", "git log --oneline | head -1", "cd /repo && git log --oneline | head -1")
    t = esperar("kubectl get deploy web -n tienda -o jsonpath=\"{.spec.replicas}\"", "3", 400)
    OUT.append(f"> Con la configuración por defecto (sin webhook), el clúster pasó a 3 réplicas a los {t} s del push.\n")
    bloque("intervalo de sondeo configurado", "kubectl get cm argocd-cm -n argocd -o jsonpath=…timeout.reconciliation",
           "kubectl get cm argocd-cm -n argocd -o jsonpath=\"timeout.reconciliation={.data.timeout\\.reconciliation}\"",
           "Vacío = valor por defecto de Argo CD.")

    OUT.append("## 5 · Se borra algo del repositorio\n")
    git_commit("quito el ConfigMap", 3, con_cm=False)
    t = esperar("kubectl get configmap ajustes -n tienda -o name 2>/dev/null | wc -l", "0", 400)
    OUT.append(f"> prune: el ConfigMap desapareció del clúster a los {t} s del push.\n")
    bloque("lo que queda", "kubectl get deploy,cm -n tienda", "kubectl get deploy,configmap -n tienda")

    OUT.append("## 6 · Lo que pesa\n")
    bloque("contenedores de Argo CD", "kubectl get pods -n argocd --no-headers | wc -l", "kubectl get pods -n argocd --no-headers | wc -l")

    (AQUI / "SALIDA.md").write_text("\n".join(OUT), encoding="utf-8")
    print("ok SALIDA.md")


if __name__ == "__main__":
    main()
