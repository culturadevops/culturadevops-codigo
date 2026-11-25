# -*- coding: utf-8 -*-
"""Segunda parte del banco del 408 (Argo CD), sobre el laboratorio que deja correr.py (k3s, herr, gitea, app «web»):
  · un commit + refresh inmediato (lo que haría un webhook): cuánto tarda entonces;
  · un commit con una imagen que no existe: cómo lo ve Argo CD, y git revert para volver.
    python correr_extra.py   -> SALIDA-extra.md
"""
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
OUT = []
DEPLOY = """apiVersion: apps/v1
kind: Deployment
metadata: {name: web}
spec:
  replicas: REPL
  selector: {matchLabels: {app: web}}
  template:
    metadata: {labels: {app: web}}
    spec:
      containers: [{name: web, image: IMAGEN}]
"""


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


def esperar(cmd, esperado, tope=300):
    t0 = time.time()
    while time.time() - t0 < tope:
        s, _ = ex(cmd)
        if s.strip() == esperado:
            return round(time.time() - t0, 1)
        time.sleep(1)
    return None


def commit(msg, repl, imagen):
    ex(f"cd /repo && cat > web/deploy.yaml <<'EOF'\n{DEPLOY.replace('REPL', str(repl)).replace('IMAGEN', imagen)}EOF\n"
       f"git add -A && git commit -qm '{msg}' && git push -q origin main")


REFRESH = "kubectl annotate application web -n argocd argocd.argoproj.io/refresh=normal --overwrite >/dev/null"
SALUD = "kubectl get application web -n argocd -o jsonpath=\"{.status.sync.status}/{.status.health.status}\""


def main():
    OUT.append(f"# SALIDA (2.ª parte) — Argo CD (vídeo 408)\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr_extra.py`, "
               "sobre el laboratorio de correr.py.\n")
    OUT.append("## 7 · Un commit con aviso inmediato (lo que hace un webhook)\n")
    commit("web con 4 réplicas", 4, "nginx:1.29-alpine")
    bloque("el commit", "git log --oneline | head -1", "cd /repo && git log --oneline | head -1")
    t0 = time.time()
    ex(REFRESH)
    t = esperar("kubectl get deploy web -n tienda -o jsonpath=\"{.spec.replicas}\"", "4")
    OUT.append(f"### pedir a Argo CD que mire ya\n\n`$ kubectl annotate application web -n argocd argocd.argoproj.io/refresh=normal`\n\n"
               f"> Con el aviso, el clúster pasó a 4 réplicas a los {t} s (sin aviso, en la 1.ª parte: 358 s).\n")

    OUT.append("## 8 · Un commit roto\n")
    commit("imagen que no existe", 4, "nginx:9.99-no-existe")
    bloque("el commit", "git log --oneline | head -1", "cd /repo && git log --oneline | head -1")
    ex(REFRESH)
    t = None
    t0 = time.time()
    while time.time() - t0 < 240:
        s, _ = ex(SALUD)
        if s.strip().startswith("Synced/") and not s.strip().endswith("Healthy"):
            t = round(time.time() - t0, 1)
            break
        time.sleep(2)
    OUT.append(f"> A los {t} s Argo CD ya marcaba la aplicación como no sana.\n")
    time.sleep(20)
    bloque("el estado de la aplicación", "kubectl get application web -n argocd", "kubectl get application web -n argocd")
    bloque("y los pods", "kubectl get pods -n tienda", "kubectl get pods -n tienda --no-headers | awk '{print $1, $3}'")

    OUT.append("## 9 · Volver atrás: git revert\n")
    bloque("revertir el commit", "git revert --no-edit HEAD && git push",
           "cd /repo && git revert --no-edit HEAD >/dev/null && git push -q origin main && git log --oneline | head -2")
    ex(REFRESH)
    t = esperar(SALUD, "Synced/Healthy", 300)
    OUT.append(f"> Synced y Healthy otra vez a los {t} s del revert (con aviso).\n")
    bloque("el estado", "kubectl get application web -n argocd", "kubectl get application web -n argocd")

    (AQUI / "SALIDA-extra.md").write_text("\n".join(OUT), encoding="utf-8")
    print("ok SALIDA-extra.md")


if __name__ == "__main__":
    main()
