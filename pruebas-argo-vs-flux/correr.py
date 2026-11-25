# -*- coding: utf-8 -*-
"""Argo CD vs Flux — banco de pruebas del vídeo 335 (cultura-devops, serie versus).

El MISMO clúster (k3s en Docker), el MISMO repositorio (Gitea) y la MISMA prueba para los dos.
Cada uno despliega el repo en su espacio de nombres: argo-app y flux-app.
Configuración: la de la guía oficial de cada uno.
  · Argo CD: Application con syncPolicy.automated (sin prune ni selfHeal, que son opcionales).
  · Flux:    GitRepository interval 1m + Kustomization interval 30m, prune true (flux get-started).
Se mide: instalación (tiempo, pods, memoria), cuánto tarda cada uno en aplicar un push, qué hace
cada uno al borrar un manifiesto, y qué hace cada uno con un cambio a mano en el clúster.

    python correr.py
"""
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "lab-k8s"))
import lab as L  # noqa: E402

ARGO = "https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml"
FLUX = "ghcr.io/fluxcd/flux-cli:v2.9.6"
salida = []

APP = f"""apiVersion: argoproj.io/v1alpha1
kind: Application
metadata: {{name: web, namespace: argocd}}
spec:
  project: default
  source: {{repoURL: {L.REPO_URL}, targetRevision: main, path: .}}
  destination: {{server: https://kubernetes.default.svc, namespace: argo-app}}
  syncPolicy:
    automated: {{}}
    syncOptions: [CreateNamespace=true]
"""
FLUXCFG = f"""apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata: {{name: app, namespace: flux-system}}
spec:
  interval: 1m
  url: {L.REPO_URL}
  ref: {{branch: main}}
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata: {{name: web, namespace: flux-system}}
spec:
  interval: 30m
  prune: true
  sourceRef: {{kind: GitRepository, name: app}}
  path: ./
  targetNamespace: flux-app
"""


def anota(titulo, cmd_txt, texto):
    salida.extend(["", f"### {titulo}", "", f"`$ {cmd_txt}`", "", "```", texto.strip(), "```"])
    print(f"--- {titulo}\n{texto.strip()[:1500]}\n", flush=True)


def flux(*a, timeout=900):
    return L.sh(["docker", "run", "--rm", "--network", L.RED, "-v", f"{AQUI / '_kubeconfig'}:/kc:ro",
                 "-e", "KUBECONFIG=/kc", FLUX, *a], timeout=timeout)


def mem(ns):
    filas = [l.split() for l in L.k("top", "pods", "-n", ns, "--no-headers").splitlines() if l.strip()]
    return sum(int(f[2].rstrip("Mi")) for f in filas if len(f) >= 3 and f[2].endswith("Mi")), len(filas)


def replicas(ns):
    return L.k("get", "deploy", "web", "-n", ns, "-o", "jsonpath={.spec.replicas}")


def existe_cm(ns):
    return "NotFound" not in L.k("get", "cm", "web-config", "-n", ns)


def main():
    salida.append("\n## 1 · Laboratorio y repositorio")
    L.levantar(puertos_k3s=("8443:8080",))
    (AQUI / "_kubeconfig").write_text(L.k("config", "view", "--raw").replace("127.0.0.1", L.K3S_IP), encoding="utf-8")
    repo = L.Repo()
    repo.escribe("deployment.yaml", L.DEPLOY.format(replicas=1))
    repo.escribe("service.yaml", L.SERVICE)
    repo.escribe("configmap.yaml", L.CONFIG)
    repo.commit("web: nginx con 1 réplica")
    anota("el repo", "git log --oneline; ls", repo.log() + "\n" + "\n".join(sorted(p.name for p in repo.dir.glob("*.yaml"))))

    salida.append("\n## 2 · Instalar los dos")
    L.k("create", "namespace", "argocd")
    t0 = time.time()
    L.k("apply", "-n", "argocd", "--server-side", "--force-conflicts", "-f", ARGO, timeout=900)
    for d in ("argocd-server", "argocd-repo-server", "argocd-redis", "argocd-applicationset-controller",
              "argocd-dex-server", "argocd-notifications-controller"):
        L.k("rollout", "status", f"deploy/{d}", "-n", "argocd", "--timeout=600s", timeout=700)
    L.k("rollout", "status", "statefulset/argocd-application-controller", "-n", "argocd", "--timeout=600s", timeout=700)
    t_argo = time.time() - t0
    anota("Argo CD", f"kubectl apply -n argocd --server-side -f {ARGO}",
          L.k("get", "pods", "-n", "argocd", "--no-headers", "-o", "custom-columns=NOMBRE:.metadata.name")
          + f"\n(listo en {t_argo:.0f} s) · versión " +
          L.k("exec", "-n", "argocd", "deploy/argocd-server", "--", "argocd", "version", "--client", "--short"))
    t0 = time.time()
    r = flux("install", "--timeout=10m", timeout=900)
    t_flux = time.time() - t0
    anota("Flux", "flux install", "\n".join(l for l in r.splitlines() if "✔" in l or "✚" in l or "installed" in l)
          + "\n" + L.k("get", "pods", "-n", "flux-system", "--no-headers", "-o", "custom-columns=NOMBRE:.metadata.name")
          + f"\n(listo en {t_flux:.0f} s)")
    anota("versión de Flux", "flux version", flux("version"))
    time.sleep(45)
    ma, pa = mem("argocd")
    mf, pf = mem("flux-system")
    anota("memoria en reposo", "kubectl top pods -n argocd / -n flux-system",
          L.k("top", "pods", "-n", "argocd") + "\n\n" + L.k("top", "pods", "-n", "flux-system")
          + f"\n\nArgo CD: {pa} pods, {ma} MiB · Flux: {pf} pods, {mf} MiB")
    anota("CRD que añade cada uno", "kubectl get crd | grep -c argoproj / toolkit.fluxcd",
          f"argoproj.io: {L.k('get', 'crd', '-o', 'name').count('argoproj.io')}\n"
          f"toolkit.fluxcd.io: {L.k('get', 'crd', '-o', 'name').count('toolkit.fluxcd.io')}")

    salida.append("\n## 3 · Conectar el repo (configuración de la guía oficial de cada uno)")
    anota("Argo CD: Application", "cat application.yaml", APP)
    anota("Flux: GitRepository + Kustomization", "cat flux.yaml", FLUXCFG)
    L.k("create", "namespace", "flux-app")
    t0 = time.time()
    L.k("apply", "-f", "-", entrada=APP)
    L.k("apply", "-f", "-", entrada=FLUXCFG)
    ta = tf = None
    while time.time() - t0 < 400 and (ta is None or tf is None):
        if ta is None and replicas("argo-app") == "1" and "1/1" in L.k("get", "deploy", "web", "-n", "argo-app"):
            ta = time.time() - t0
        if tf is None and replicas("flux-app") == "1" and "1/1" in L.k("get", "deploy", "web", "-n", "flux-app"):
            tf = time.time() - t0
        time.sleep(2)
    anota("primera sincronización", "kubectl get deploy web -n argo-app / -n flux-app",
          f"Argo CD: web listo a los {ta:.0f} s\nFlux:    web listo a los {tf:.0f} s")
    anota("estado según cada uno", "kubectl get application -n argocd; flux get kustomizations",
          L.k("get", "application", "-n", "argocd") + "\n\n" + flux("get", "kustomizations", "-A"))

    salida.append("\n## 4 · Un push: ¿cuánto tarda cada uno?")
    repo.escribe("deployment.yaml", L.DEPLOY.format(replicas=3))
    c2 = repo.commit("web: 3 réplicas")
    t0 = time.time()
    anota("el cambio", "git commit -m 'web: 3 réplicas' && git push", f"commit {c2[:7]} a las {datetime.now(timezone.utc):%H:%M:%S} UTC")
    ta = tf = None
    while time.time() - t0 < 420 and (ta is None or tf is None):
        if ta is None and replicas("argo-app") == "3":
            ta = time.time() - t0
        if tf is None and replicas("flux-app") == "3":
            tf = time.time() - t0
        time.sleep(2)
    anota("¿cuándo llegó a cada clúster?", "réplicas en argo-app / flux-app, cada 2 s",
          f"Argo CD: {f'{ta:.0f} s' if ta else 'no en 420 s'}\nFlux:    {f'{tf:.0f} s' if tf else 'no en 420 s'}")

    salida.append("\n## 5 · Borrar un manifiesto en Git")
    repo.borra("configmap.yaml")
    c3 = repo.commit("quitar web-config")
    t0 = time.time()
    da = df = None
    while time.time() - t0 < 300 and df is None:
        if df is None and not existe_cm("flux-app"):
            df = time.time() - t0
        time.sleep(3)
    time.sleep(max(0, 200 - (time.time() - t0)))
    da = existe_cm("argo-app")
    anota("¿sigue el ConfigMap?", "kubectl get cm web-config -n argo-app / -n flux-app",
          f"Argo CD (automated sin prune): {'sigue ahí' if da else 'borrado'} a los {time.time() - t0:.0f} s\n"
          f"  " + L.k("get", "application", "web", "-n", "argocd", "-o", "jsonpath={.status.sync.status}") + "\n"
          f"Flux (prune: true de la guía):  {f'borrado a los {df:.0f} s' if df else 'sigue ahí'}")

    salida.append("\n## 6 · Alguien cambia el clúster a mano")
    L.k("scale", "deploy/web", "-n", "argo-app", "--replicas=1")
    L.k("scale", "deploy/web", "-n", "flux-app", "--replicas=1")
    t0 = time.time()
    linea = []
    while time.time() - t0 < 180:
        linea.append(f"t={time.time() - t0:4.0f}s  argo-app={replicas('argo-app')}  flux-app={replicas('flux-app')}")
        time.sleep(30)
    anota("kubectl scale --replicas=1 en los dos y mirar 3 min", "réplicas cada 30 s", "\n".join(linea))
    t0 = time.time()
    anota("Flux: forzar la reconciliación", "flux reconcile kustomization web",
          flux("reconcile", "kustomization", "web", "-n", "flux-system") + f"\nflux-app={replicas('flux-app')} ({time.time() - t0:.0f} s)")
    L.k("patch", "application", "web", "-n", "argocd", "--type", "merge",
        "-p", '{"spec":{"syncPolicy":{"automated":{"selfHeal":true}}}}')
    s = None
    t0 = time.time()
    while time.time() - t0 < 120:
        if replicas("argo-app") == "3":
            s = time.time() - t0
            break
        time.sleep(1)
    anota("Argo CD: activar selfHeal", "syncPolicy.automated.selfHeal: true",
          f"argo-app={replicas('argo-app')} ({f'{s:.0f} s' if s is not None else 'no volvió'})")

    salida.append("\n## 7 · Ver el estado")
    anota("Flux desde la terminal", "flux get all -A", flux("get", "all", "-A"))
    anota("eventos de Flux", "flux events -A | tail", "\n".join(flux("events", "-A").splitlines()[-8:]))

    (AQUI / "_kubeconfig").unlink(missing_ok=True)
    L.limpiar()
    cab = ["# SALIDA — Argo CD vs Flux (vídeo 335)", "",
           f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. "
           f"k3s + Gitea en Docker; Argo CD (install.yaml de stable) y Flux ({FLUX})."]
    (AQUI / "SALIDA.md").write_text("\n".join(cab + salida) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
