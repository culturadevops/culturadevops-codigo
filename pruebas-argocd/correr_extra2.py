# -*- coding: utf-8 -*-
"""Tercera parte del banco del 408: ApplicationSet con el generador de directorios de Git — una carpeta nueva en el
repositorio = una aplicación nueva, sin escribir otra Application. Sobre el laboratorio de correr.py.
    python correr_extra2.py   -> SALIDA-extra2.md
"""
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
OUT = []
CM = """apiVersion: v1
kind: ConfigMap
metadata: {name: hola}
data: {equipo: NOMBRE}
"""


def run(args):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (p.stdout + p.stderr).strip(), p.returncode


def ex(cmd):
    return run(["docker", "exec", "herr", "sh", "-c", cmd])


def bloque(titulo, mostrado, cmd):
    s, rc = ex(cmd)
    OUT.append(f"### {titulo}\n\n`$ {mostrado}`\n\n```\n{s}\n```\n(código de salida {rc})\n")
    print(f"[{rc}] {titulo}")
    return s, rc


def main():
    repo, _ = ex("kubectl get application web -n argocd -o jsonpath=\"{.spec.source.repoURL}\"")
    for eq in ("pagos", "envios"):
        ex(f"cd /repo && mkdir -p equipos/{eq} && cat > equipos/{eq}/cm.yaml <<'EOF'\n{CM.replace('NOMBRE', eq)}EOF\n")
    ex("cd /repo && git add -A && git commit -qm 'dos equipos' && git push -q origin main")
    APPSET = f"""apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata: {{name: equipos, namespace: argocd}}
spec:
  goTemplate: true
  generators:
  - git:
      repoURL: {repo}
      revision: main
      directories: [{{path: "equipos/*"}}]
  template:
    metadata: {{name: "eq-{{{{.path.basename}}}}"}}
    spec:
      project: default
      source: {{repoURL: {repo}, targetRevision: main, path: "{{{{.path.path}}}}"}}
      destination: {{server: https://kubernetes.default.svc, namespace: "{{{{.path.basename}}}}"}}
      syncPolicy:
        automated: {{prune: true, selfHeal: true}}
        syncOptions: [CreateNamespace=true]
"""
    ex(f"cat > /tmp/appset.yaml <<'EOF'\n{APPSET}EOF")
    OUT.append(f"# SALIDA (3.ª parte) — Argo CD, ApplicationSet (vídeo 408)\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr_extra2.py`.\n")
    OUT.append("## 10 · Una carpeta nueva = una aplicación nueva\n")
    bloque("las carpetas en Git", "ls equipos/", "cd /repo && ls equipos/")
    bloque("el ApplicationSet", "kubectl apply -f appset.yaml", "kubectl apply -f /tmp/appset.yaml && grep -A2 directories /tmp/appset.yaml")
    time.sleep(15)
    bloque("las aplicaciones que generó", "kubectl get applications -n argocd", "kubectl get applications -n argocd")
    ex("cd /repo && mkdir -p equipos/soporte && printf 'apiVersion: v1\\nkind: ConfigMap\\nmetadata: {name: hola}\\ndata: {equipo: soporte}\\n' > equipos/soporte/cm.yaml "
       "&& git add -A && git commit -qm 'equipo soporte' && git push -q origin main")
    bloque("añado una carpeta y hago push", "mkdir equipos/soporte … git push", "cd /repo && git log --oneline | head -1")
    ex("kubectl annotate applicationset equipos -n argocd argocd.argoproj.io/application-set-refresh=true --overwrite >/dev/null")
    t0 = time.time()
    t = None
    while time.time() - t0 < 300:
        s, _ = ex("kubectl get application eq-soporte -n argocd -o jsonpath=\"{.status.health.status}\" 2>/dev/null")
        if s.strip() == "Healthy":
            t = round(time.time() - t0, 1)
            break
        time.sleep(1)
    OUT.append(f"> La aplicación «eq-soporte» apareció, sincronizada y sana, a los {t} s (con aviso al ApplicationSet).\n")
    bloque("y queda así", "kubectl get applications -n argocd", "kubectl get applications -n argocd")
    (AQUI / "SALIDA-extra2.md").write_text("\n".join(OUT), encoding="utf-8")
    print("ok SALIDA-extra2.md")


if __name__ == "__main__":
    main()
