# -*- coding: utf-8 -*-
"""Demo de «Argo CD en 5 minutos» (cultura-devops). Argo CD v3.5.6 (manifiesto oficial) sobre el k3s de la demo de Helm
(contenedores k3s5 y herr5, red lab5: `python ../demo-5min-helm/correr.py --dejar` antes), con un Gitea propio como
repositorio para poder hacer commits. Credenciales inventadas, todo local; se borra al terminar.
  · una Application automatizada (prune + selfHeal);
  · alguien escala a mano → vuelve sola;
  · un commit cambia las réplicas → llega al clúster;
  · git revert como «volver atrás»;
  · borrar un archivo del repo → desaparece del clúster.
    python correr.py   -> SALIDA.md
"""
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
ARGO = "v3.5.6"
GITEA = "gitea/gitea:1.25"
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
      containers: [{name: web, image: nginx:1.31-alpine}]
"""
CM = """apiVersion: v1
kind: ConfigMap
metadata: {name: ajustes}
data: {modo: produccion}
"""
APP = """apiVersion: argoproj.io/v1alpha1
kind: Application
metadata: {name: web, namespace: argocd}
spec:
  project: default
  source: {repoURL: REPO, targetRevision: main, path: web}
  destination: {server: https://kubernetes.default.svc, namespace: tienda}
  syncPolicy:
    automated: {prune: true, selfHeal: true}
    syncOptions: [CreateNamespace=true]
"""


def run(args):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (p.stdout + p.stderr).strip(), p.returncode


def ex(cmd):
    return run(["docker", "exec", "herr5", "sh", "-c", cmd])


def bloque(titulo, mostrado, cmd, nota=None):
    s, rc = ex(cmd)
    OUT.append(f"### {titulo}\n\n`$ {mostrado}`\n\n```\n{s}\n```\n(código de salida {rc})\n" + (f"\n> {nota}\n" if nota else ""))
    print(f"[{rc}] {titulo}")
    return s, rc


def esperar(cond_cmd, esperado, tope=420):
    t0 = time.time()
    while time.time() - t0 < tope:
        s, _ = ex(cond_cmd)
        if s.strip() == esperado:
            return round(time.time() - t0, 1)
        time.sleep(2)
    return None


def git_commit(msg, repl, con_cm=True):
    ex(f"cd /repo && mkdir -p web && cat > web/deploy.yaml <<'EOF'\n{DEPLOY.replace('REPL', str(repl))}EOF\n"
       + (f"cat > web/ajustes.yaml <<'EOF'\n{CM}EOF\n" if con_cm else "rm -f web/ajustes.yaml\n")
       + f"git add -A && git commit -qm '{msg}' && git push -q origin main")


REPL = "kubectl get deploy web -n tienda -o jsonpath=\"{.spec.replicas}\""


def main():
    s, rc = run(["docker", "exec", "herr5", "kubectl", "get", "nodes"])
    if rc:   # sin laboratorio: se levanta con la misma función de la demo de Helm
        import importlib.util
        spec = importlib.util.spec_from_file_location("helm5", AQUI.parent / "demo-5min-helm" / "correr.py")
        helm5 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helm5)
        helm5.levantar_lab()
    run(["docker", "rm", "-f", "gitea5"])
    run(["docker", "run", "-d", "--name", "gitea5", "--network", "lab5", "-e", "GITEA__security__INSTALL_LOCK=true",
         "-e", "GITEA__server__ROOT_URL=http://gitea5:3000/", GITEA])
    for _ in range(60):
        s, _ = ex("curl -s -o /dev/null -w '%{http_code}' http://gitea5:3000/api/healthz")
        if s.strip() == "200":
            break
        time.sleep(2)
    ip, _ = run(["docker", "inspect", "-f", "{{(index .NetworkSettings.Networks \"lab5\").IPAddress}}", "gitea5"])
    repo = f"http://{ip.strip()}:3000/lab/apps.git"   # IP: los pods de k3s no resuelven los nombres de la red de Docker
    run(["docker", "exec", "-u", "git", "gitea5", "gitea", "admin", "user", "create", "--username", "lab", "--password",
         "lab12345", "--email", "lab@lab.local", "--admin", "--must-change-password=false"])
    ex("curl -s -u lab:lab12345 -H 'Content-Type: application/json' -d '{\"name\":\"apps\",\"default_branch\":\"main\"}' "
       "http://gitea5:3000/api/v1/user/repos >/dev/null; "
       "rm -rf /repo && git init -q -b main /repo && cd /repo && git config user.email lab@lab.local && git config user.name lab "
       "&& git remote add origin http://lab:lab12345@gitea5:3000/lab/apps.git")
    git_commit("web con 2 réplicas", 2)

    OUT.append(f"# SALIDA — Argo CD en 5 minutos (cultura-devops)\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con "
               f"`python correr.py`. k3s en Docker, Argo CD {ARGO} con su manifiesto oficial, Gitea ({GITEA}) como repositorio.\n")
    OUT.append("## 1 · Instalar Argo CD\n")
    ex("kubectl create ns argocd")
    t0 = time.time()
    bloque("el manifiesto oficial", f"kubectl apply -n argocd --server-side -f …/argo-cd/{ARGO}/manifests/install.yaml | tail -2",
           f"kubectl apply -n argocd --server-side --force-conflicts -f https://raw.githubusercontent.com/argoproj/argo-cd/{ARGO}/manifests/install.yaml | tail -2")
    ex("kubectl wait -n argocd --for=condition=Available deploy --all --timeout=400s >/dev/null; "
       "kubectl wait -n argocd --for=condition=Ready pod -l app.kubernetes.io/name=argocd-application-controller --timeout=400s >/dev/null")
    OUT.append(f"> Todo listo a los {round(time.time() - t0)} s (incluye bajar las imágenes).\n")
    bloque("lo que instala", "kubectl get pods -n argocd", "kubectl get pods -n argocd -o custom-columns=POD:.metadata.name,ESTADO:.status.phase")
    bloque("la versión", "kubectl get deploy argocd-server -n argocd -o jsonpath=…image",
           "kubectl get deploy argocd-server -n argocd -o jsonpath=\"{.spec.template.spec.containers[0].image}\"")

    OUT.append("## 2 · Una aplicación que vive en Git\n")
    bloque("lo que hay en el repositorio", "git log --oneline; ls web/", "cd /repo && git log --oneline && ls web/")
    ex(f"cat > /tmp/app.yaml <<'EOF'\n{APP.replace('REPO', repo)}EOF")
    bloque("la Application", "kubectl apply -f app.yaml", "kubectl apply -f /tmp/app.yaml && cat /tmp/app.yaml")
    t = esperar("kubectl get application web -n argocd -o jsonpath=\"{.status.sync.status}/{.status.health.status}\"", "Synced/Healthy")
    OUT.append(f"> Synced y Healthy a los {t} s.\n")
    bloque("lo que creó en el clúster", "kubectl get deploy,cm -n tienda", "kubectl get deploy web -n tienda && kubectl get configmap ajustes -n tienda")

    OUT.append("## 3 · Alguien lo cambia a mano\n")
    bloque("escalar a 5 con kubectl", "kubectl scale deploy web -n tienda --replicas=5", "kubectl scale deploy web -n tienda --replicas=5")
    t = esperar(REPL, "2", 300)
    OUT.append(f"> selfHeal: volvió a 2 réplicas a los {t} s.\n")

    OUT.append("## 4 · Un commit en Git\n")
    git_commit("web con 4 réplicas", 4)
    bloque("el commit", "git log --oneline | head -1", "cd /repo && git log --oneline | head -1")
    t = esperar(REPL, "4", 420)
    OUT.append(f"> Sin webhook (sondeo por defecto), el clúster pasó a 4 réplicas a los {t} s del push.\n")

    OUT.append("## 5 · Volver atrás es un git revert\n")
    bloque("git revert", "git revert --no-edit HEAD && git push", "cd /repo && git revert --no-edit HEAD >/dev/null && git push -q origin main && git log --oneline | head -3")
    t = esperar(REPL, "2", 420)
    OUT.append(f"> El clúster volvió a 2 réplicas a los {t} s del push.\n")

    OUT.append("## 6 · Se borra algo del repositorio\n")
    git_commit("quito el ConfigMap", 2, con_cm=False)
    t = esperar("kubectl get configmap ajustes -n tienda -o name 2>/dev/null | wc -l", "0", 420)
    OUT.append(f"> prune: el ConfigMap desapareció del clúster a los {t} s del push.\n")
    bloque("lo que queda", "kubectl get deploy,cm -n tienda", "kubectl get deploy,configmap -n tienda 2>&1 | grep -v kube-root-ca")

    (AQUI / "SALIDA.md").write_text("\n".join(OUT), encoding="utf-8")
    for c in ("k3s5", "herr5", "gitea5"):
        run(["docker", "rm", "-f", c])
    run(["docker", "network", "rm", "lab5"])
    print("ok SALIDA.md")


if __name__ == "__main__":
    main()
