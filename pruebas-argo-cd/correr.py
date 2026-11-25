# -*- coding: utf-8 -*-
"""Argo CD — banco de pruebas del vídeo 328 (cultura-devops, serie herramientas).

k3s + Gitea en Docker (ver ../lab-k8s/lab.py), Argo CD con el manifiesto oficial (stable).
Se mide: instalación, sincronización inicial, cuánto tarda en DETECTAR un cambio en Git sin
webhook, qué pasa al borrar un manifiesto con prune y sin él, y la autorreparación (selfHeal).
Capturas de la interfaz con Playwright (capturar.js) a motor/remotion/public/.

    python correr.py
"""
import base64
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "lab-k8s"))
import lab as L  # noqa: E402

PUB = Path(r"<proyecto>\motor\remotion\public\om-projects\cultura-devops\argo-cd")
INSTALL = "https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml"
salida = []
CLAVE_ADMIN = ""

APP = """apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: web
  namespace: argocd
spec:
  project: default
  source:
    repoURL: {repo}
    targetRevision: main
    path: .
  destination:
    server: https://kubernetes.default.svc
    namespace: default
{sync}"""
AUTO = "  syncPolicy:\n    automated: {}\n"
AUTO_PRUNE = "  syncPolicy:\n    automated:\n      prune: true\n"
AUTO_HEAL = "  syncPolicy:\n    automated:\n      prune: true\n      selfHeal: true\n"
NL = "{'\\n'}"   # salto de línea en jsonpath de kubectl


def anota(titulo, cmd_txt, texto):
    salida.extend(["", f"### {titulo}", "", f"`$ {cmd_txt}`", "", "```", texto.strip(), "```"])
    print(f"--- {titulo}\n{texto.strip()[:1200]}\n", flush=True)


def app(campo):
    return L.k("get", "application", "web", "-n", "argocd", "-o", f"jsonpath={campo}")


def estado():
    return (f"sync={app('{.status.sync.status}')}  health={app('{.status.health.status}')}  "
            f"revision={app('{.status.sync.revision}')[:7]}")


def recursos():
    return app("{range .status.resources[*]}{.kind}/{.name} {.status} requiresPruning={.requiresPruning}" + NL + "{end}")


def historial():
    return app("{range .status.history[*]}{.id} {.revision} {.deployedAt}" + NL + "{end}")


def replicas():
    return L.k("get", "deploy", "web", "-n", "default", "-o", "jsonpath={.spec.replicas}")


def espera(cond, max_s=600, paso=2):
    t = time.time()
    while time.time() - t < max_s:
        if cond():
            return time.time() - t
        time.sleep(paso)
    return None


def refresca():
    L.k("annotate", "application", "web", "-n", "argocd", "argocd.argoproj.io/refresh=normal", "--overwrite")


def politica(sync):
    L.k("apply", "-f", "-", entrada=APP.format(repo=L.REPO_URL, sync=sync))


def captura(nombre, ruta="/applications/argocd/web"):
    PUB.mkdir(parents=True, exist_ok=True)
    print(L.sh(["node", str(AQUI / "capturar.js"), str(PUB / f"{nombre}.png"), ruta, CLAVE_ADMIN]))


def main():
    global CLAVE_ADMIN
    salida.append("\n## 1 · Laboratorio: k3s + Gitea en Docker")
    t0 = time.time()
    L.levantar(puertos_k3s=("8443:8080",))
    anota("nodo", "kubectl get nodes", L.k("get", "nodes") + f"\n(clúster listo en {time.time() - t0:.0f} s)")

    salida.append("\n## 2 · Instalar Argo CD")
    L.k("create", "namespace", "argocd")
    t0 = time.time()
    r = L.k("apply", "-n", "argocd", "--server-side", "--force-conflicts", "-f", INSTALL, timeout=900)
    anota("kubectl apply install.yaml", f"kubectl apply -n argocd --server-side -f {INSTALL}",
          f"{len([x for x in r.splitlines() if 'serverside-applied' in x])} objetos aplicados\n"
          + "\n".join(x for x in r.splitlines() if "customresourcedefinition" in x or "deployment" in x
                      or "statefulset" in x))
    for d in ("argocd-server", "argocd-repo-server", "argocd-redis", "argocd-applicationset-controller",
              "argocd-dex-server", "argocd-notifications-controller"):
        L.k("rollout", "status", f"deploy/{d}", "-n", "argocd", "--timeout=600s", timeout=700)
    L.k("rollout", "status", "statefulset/argocd-application-controller", "-n", "argocd",
        "--timeout=600s", timeout=700)
    anota("pods de Argo CD", "kubectl get pods -n argocd",
          L.k("get", "pods", "-n", "argocd") + f"\n(todo listo en {time.time() - t0:.0f} s)")
    anota("versión", "argocd version --client --short",
          L.k("exec", "-n", "argocd", "deploy/argocd-server", "--", "argocd", "version", "--client", "--short"))
    time.sleep(20)
    anota("memoria de Argo CD", "kubectl top pods -n argocd", L.k("top", "pods", "-n", "argocd"))
    CLAVE_ADMIN = base64.b64decode(L.k("get", "secret", "argocd-initial-admin-secret", "-n", "argocd",
                                       "-o", "jsonpath={.data.password}")).decode()
    anota("la contraseña inicial", "kubectl get secret argocd-initial-admin-secret ...",
          f"(una cadena de {len(CLAVE_ADMIN)} caracteres)")
    L.sh(["docker", "exec", "-d", "k3s", "kubectl", "port-forward", "--address", "0.0.0.0",
          "-n", "argocd", "svc/argocd-server", "8080:443"])

    salida.append("\n## 3 · El repositorio y la Application (sincronización manual)")
    repo = L.Repo()
    repo.escribe("deployment.yaml", L.DEPLOY.format(replicas=1))
    repo.escribe("service.yaml", L.SERVICE)
    repo.escribe("configmap.yaml", L.CONFIG)
    repo.commit("web: nginx con 1 réplica")
    anota("el repo", "git log --oneline; ls",
          repo.log() + "\n" + "\n".join(sorted(p.name for p in repo.dir.glob("*.yaml"))))
    politica("")
    espera(lambda: app("{.status.sync.status}") in ("OutOfSync", "Synced"))
    anota("recién creada, sin syncPolicy", "kubectl get application web -n argocd", estado())
    anota("y en el clúster", "kubectl get deploy,svc,cm -n default", L.k("get", "deploy,svc,cm", "-n", "default"))
    captura("01-outofsync")
    L.k("patch", "application", "web", "-n", "argocd", "--type", "merge",
        "-p", '{"operation":{"sync":{"revision":"main"}}}')
    s = espera(lambda: app("{.status.sync.status}") == "Synced" and app("{.status.health.status}") == "Healthy")
    anota("después de sincronizar a mano", "argocd app sync web  (aquí: operation.sync)",
          estado() + f"\n(Synced y Healthy en {s:.0f} s)\n" + L.k("get", "deploy", "web", "-n", "default"))
    captura("02-synced")

    salida.append("\n## 4 · Sincronización automática y cuánto tarda en ver un cambio")
    politica(AUTO)
    repo.escribe("deployment.yaml", L.DEPLOY.format(replicas=3))
    c2 = repo.commit("web: 3 réplicas")
    anota("el cambio", "git commit -m 'web: 3 réplicas' && git push",
          f"commit {c2[:7]} subido a las {datetime.now(timezone.utc):%H:%M:%S} UTC")
    s = espera(lambda: app("{.status.sync.revision}").startswith(c2), max_s=400, paso=3)
    anota("¿cuándo lo vio Argo?", "kubectl get application web (cada 3 s)",
          estado() + (f"\n(Argo aplicó {c2[:7]} {s:.0f} s después del push)" if s else "\n(no lo vio en 400 s)"))
    anota("réplicas", "kubectl get deploy web", L.k("get", "deploy", "web", "-n", "default"))

    salida.append("\n## 5 · Borrar un manifiesto en Git: sin prune y con prune")
    repo.borra("configmap.yaml")
    c3 = repo.commit("quitar web-config")
    refresca()
    espera(lambda: app("{.status.sync.revision}").startswith(c3), max_s=120)
    time.sleep(8)
    anota("sin prune", "kubectl get application web; kubectl get cm web-config",
          estado() + "\n" + L.k("get", "cm", "web-config", "-n", "default") + "\n" + recursos())
    anota("historial", "status.history", historial())
    captura("03-requiere-prune")
    politica(AUTO_PRUNE)
    s = espera(lambda: "NotFound" in L.k("get", "cm", "web-config", "-n", "default"), max_s=240, paso=5)
    anota("activar prune después del commit", "syncPolicy.automated.prune: true (y esperar 240 s)",
          (f"web-config borrado a los {s:.0f} s" if s is not None else "web-config sigue ahí 240 s después")
          + "\n" + estado() + "\n" + historial())
    if s is None:
        repo.escribe("LEEME.md", "app de prueba\n")
        repo.commit("un commit cualquiera")
        refresca()
        s = espera(lambda: "NotFound" in L.k("get", "cm", "web-config", "-n", "default"), max_s=120, paso=2)
        anota("con un commit nuevo", "git commit && git push; refresh",
              (f"web-config borrado {s:.0f} s después" if s is not None else "sigue ahí") + "\n"
              + estado() + "\n" + historial())

    salida.append("\n## 6 · Alguien cambia el clúster a mano (selfHeal)")
    linea = []
    L.k("scale", "deploy/web", "-n", "default", "--replicas=1")
    t = time.time()
    while time.time() - t < 60:
        linea.append(f"t={time.time() - t:3.0f}s  spec.replicas={replicas()}  {estado()}")
        time.sleep(10)
    anota("sin selfHeal: escalar a 1 y mirar 60 s", "kubectl scale deploy/web --replicas=1", "\n".join(linea))
    politica(AUTO_HEAL)
    s = espera(lambda: replicas() == "3", max_s=120)
    anota("activar selfHeal: true", "kubectl get deploy web",
          L.k("get", "deploy", "web", "-n", "default")
          + (f"\n(volvió a 3 réplicas {s:.0f} s después de activar selfHeal)" if s is not None else "\n(no volvió)"))
    time.sleep(5)
    L.k("scale", "deploy/web", "-n", "default", "--replicas=1")
    s = espera(lambda: replicas() == "3", max_s=120, paso=1)
    anota("otro cambio a mano, ya con selfHeal", "kubectl scale deploy/web --replicas=1",
          (f"revertido a 3 réplicas en {s:.0f} s" if s is not None else "no se revirtió en 120 s"))
    anota("historial", "status.history", historial())
    captura("04-arbol")

    L.limpiar()
    cab = ["# SALIDA — Argo CD (vídeo 328)", "",
           f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. "
           f"k3s (rancher/k3s:latest) + Gitea en Docker; Argo CD de {INSTALL}."]
    (AQUI / "SALIDA.md").write_text("\n".join(cab + salida) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
