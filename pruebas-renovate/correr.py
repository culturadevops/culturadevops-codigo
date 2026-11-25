# -*- coding: utf-8 -*-
"""Renovate — banco de pruebas del vídeo 329 (cultura-devops, serie herramientas).

Gitea local (../lab-k8s/lab.py) + Renovate CLI en Docker (renovate/renovate), plataforma gitea.
El mismo contenido (dependencias de 2021 en npm, pip y Dockerfile) en cuatro repos, uno por
pasada, para que ninguna herede el estado de otra:
  app            1) sin configuración → PR de onboarding;  2) config:recommended → límite por hora
  app-todo       3) prHourlyLimit 0 → todas las PR;  y 5) cerrar una PR: ¿la vuelve a abrir?
  app-agrupado   4) packageRules → cuántas PR quedan
Capturas de Gitea con Playwright.

    python correr.py
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "lab-k8s"))
import lab as L  # noqa: E402

PUB = Path(r"<proyecto>\motor\remotion\public\om-projects\cultura-devops\renovate")
IMG = "renovate/renovate:latest"
salida = []

PACKAGE = """{
  "name": "app",
  "version": "1.0.0",
  "dependencies": {
    "express": "4.17.1",
    "lodash": "4.17.15",
    "axios": "0.21.1"
  },
  "devDependencies": {
    "jest": "26.6.3",
    "eslint": "7.32.0"
  }
}
"""
REQS = "requests==2.25.1\nflask==1.1.2\nurllib3==1.26.4\n"
DOCKERFILE = "FROM python:3.9-slim\nCOPY . /app\nCMD [\"python\", \"/app/main.py\"]\n"
ESQUEMA = "https://docs.renovatebot.com/renovate-schema.json"
CONF_BASICA = {"$schema": ESQUEMA, "extends": ["config:recommended"]}
CONF_TODO = {"$schema": ESQUEMA, "extends": ["config:recommended"],
             "prHourlyLimit": 0, "prConcurrentLimit": 0}
CONF_AGRUPADA = {"$schema": ESQUEMA, "extends": ["config:recommended"],
                 "prHourlyLimit": 0, "prConcurrentLimit": 0,
                 "packageRules": [
                     {"matchUpdateTypes": ["minor", "patch"], "groupName": "menores y parches"},
                     {"matchUpdateTypes": ["major"], "dependencyDashboardApproval": True}]}


def anota(titulo, cmd_txt, texto):
    salida.extend(["", f"### {titulo}", "", f"`$ {cmd_txt}`", "", "```", texto.strip(), "```"])
    print(f"--- {titulo}\n{texto.strip()[:1500]}\n", flush=True)


def renovate(token, repo):
    t = time.time()
    r = L.sh(["docker", "run", "--rm", "--network", L.RED,
              "-e", "RENOVATE_PLATFORM=gitea",
              "-e", f"RENOVATE_ENDPOINT=http://{L.GITEA_IP}:3000/api/v1/",
              "-e", f"RENOVATE_TOKEN={token}",
              "-e", f"RENOVATE_REPOSITORIES=dev/{repo}",
              "-e", "RENOVATE_GIT_AUTHOR=Renovate Bot <bot@ejemplo.test>",
              "-e", "LOG_LEVEL=info", IMG], timeout=1800)
    return r, time.time() - t


def prs(repo, estado="open"):
    lista = L.gitea_api(f"/repos/dev/{repo}/pulls?state={estado}&limit=50") or []
    return sorted(lista, key=lambda p: p["number"])


def lista_prs(repo, estado="open"):
    p = prs(repo, estado)
    return "\n".join(f"#{x['number']:<3} {x['title']}" for x in p) + f"\n({len(p)} PR)"


def resumen_log(r):
    claves = ("Repository started", "Dependency extraction complete", "Repository finished",
              "PR created", "Onboarding PR", "rate limit", "Rate limit", "ignored", "Ignore")
    return "\n".join(l.strip()[:170] for l in r.splitlines() if any(c in l for c in claves))


def dashboard(repo):
    issues = [i for i in (L.gitea_api(f"/repos/dev/{repo}/issues?state=open&type=issues") or [])
              if "Dashboard" in i["title"]]
    return issues[0] if issues else None


def captura(nombre, ruta):
    PUB.mkdir(parents=True, exist_ok=True)
    print(L.sh(["node", str(AQUI / "capturar.js"), str(PUB / f"{nombre}.png"), ruta]))


def nuevo_repo(nombre, conf=None):
    repo = L.Repo(nombre)
    repo.escribe("package.json", PACKAGE)
    repo.escribe("requirements.txt", REQS)
    repo.escribe("Dockerfile", DOCKERFILE)
    if conf:
        repo.escribe("renovate.json", json.dumps(conf, indent=2, ensure_ascii=False) + "\n")
    repo.commit("app con dependencias de 2021")
    return repo


def main():
    print(L.sh(["docker", "pull", "-q", IMG], timeout=1800))
    L.levantar_gitea()
    token = L.token_gitea()
    anota("versión de Renovate", f"docker run {IMG} renovate --version",
          L.sh(["docker", "run", "--rm", IMG, "renovate", "--version"]))

    salida.append("\n## 1 · El repositorio: dependencias de 2021 en tres ecosistemas")
    repo = nuevo_repo("app")
    anota("package.json", "cat package.json", PACKAGE)
    anota("requirements.txt", "cat requirements.txt", REQS)
    anota("Dockerfile", "cat Dockerfile", DOCKERFILE)

    salida.append("\n## 2 · Primera pasada, sin configuración: onboarding")
    r, s = renovate(token, "app")
    anota("renovate (1.ª pasada)", "docker run renovate/renovate (platform=gitea)",
          resumen_log(r) + f"\n(tardó {s:.0f} s)")
    anota("PR abiertas", "GET /repos/dev/app/pulls", lista_prs("app"))
    p = prs("app")
    if p:
        anota("la PR de onboarding (recorte)", "cuerpo de la PR", (p[0].get("body") or "")[:2500])
        captura("01-onboarding", f"/dev/app/pulls/{p[0]['number']}")
        anota("fusionar la PR de onboarding", "merge #1",
              L.sh(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-X", "POST",
                    "-u", f"{L.USUARIO}:{L.CLAVE}", "-H", "Content-Type: application/json",
                    "-d", json.dumps({"Do": "merge"}),
                    f"http://localhost:3000/api/v1/repos/dev/app/pulls/{p[0]['number']}/merge"]))

    salida.append("\n## 3 · Segunda pasada, con config:recommended: el límite por hora")
    anota("renovate.json que trae la PR", "cat renovate.json",
          L.sh(["curl", "-s", "http://localhost:3000/dev/app/raw/branch/main/renovate.json"]))
    r, s = renovate(token, "app")
    anota("renovate (2.ª pasada)", "docker run renovate/renovate", resumen_log(r) + f"\n(tardó {s:.0f} s)")
    anota("PR abiertas", "GET /repos/dev/app/pulls", lista_prs("app"))
    d = dashboard("app")
    if d:
        anota("el panel de dependencias (Dependency Dashboard)", f"issue #{d['number']}",
              (d.get("body") or "")[:3500])
        captura("02-dashboard", f"/dev/app/issues/{d['number']}")
    captura("03-dos-prs", "/dev/app/pulls")

    salida.append("\n## 4 · Sin límite: todas las PR")
    nuevo_repo("app-todo", CONF_TODO)
    anota("renovate.json", "cat renovate.json", json.dumps(CONF_TODO, indent=2))
    r, s = renovate(token, "app-todo")
    anota("renovate (sin límite)", "docker run renovate/renovate", resumen_log(r) + f"\n(tardó {s:.0f} s)")
    anota("PR abiertas", "GET /repos/dev/app-todo/pulls", lista_prs("app-todo"))
    captura("04-todas", "/dev/app-todo/pulls")
    p = prs("app-todo")
    exp = [x for x in p if "express" in x["title"] and "v4" in x["title"]]
    if exp:
        anota(f"diff de la PR #{exp[0]['number']}", f"GET .../pulls/{exp[0]['number']}.diff",
              L.sh(["curl", "-s", "-u", f"{L.USUARIO}:{L.CLAVE}",
                    f"http://localhost:3000/dev/app-todo/pulls/{exp[0]['number']}.diff"])[:2500])
        captura("05-diff", f"/dev/app-todo/pulls/{exp[0]['number']}/files")

    salida.append("\n## 5 · Cerrar una PR sin fusionarla: ¿la vuelve a abrir?")
    may = [x for x in p if "eslint" in x["title"]]
    if may:
        n = may[0]["number"]
        L.sh(["curl", "-s", "-X", "PATCH", "-u", f"{L.USUARIO}:{L.CLAVE}", "-H", "Content-Type: application/json",
              "-d", json.dumps({"state": "closed"}), f"http://localhost:3000/api/v1/repos/dev/app-todo/pulls/{n}"])
        anota("cerrar sin fusionar", f"PATCH .../pulls/{n} state=closed", f"#{n} {may[0]['title']} → cerrada")
        r, s = renovate(token, "app-todo")
        anota("renovate otra vez", "docker run renovate/renovate", resumen_log(r) + f"\n(tardó {s:.0f} s)")
        anota("PR abiertas", "GET /repos/dev/app-todo/pulls", lista_prs("app-todo"))
        comentarios = L.gitea_api(f"/repos/dev/app-todo/issues/{n}/comments") or []
        anota(f"comentarios en la #{n}", f"GET .../issues/{n}/comments",
              "\n---\n".join((c.get("body") or "")[:800] for c in comentarios) or "(ninguno)")

    salida.append("\n## 6 · Agrupando: menores y parches juntos, mayores bajo aprobación")
    nuevo_repo("app-agrupado", CONF_AGRUPADA)
    anota("renovate.json", "cat renovate.json", json.dumps(CONF_AGRUPADA, indent=2, ensure_ascii=False))
    r, s = renovate(token, "app-agrupado")
    anota("renovate (agrupado)", "docker run renovate/renovate", resumen_log(r) + f"\n(tardó {s:.0f} s)")
    anota("PR abiertas", "GET /repos/dev/app-agrupado/pulls", lista_prs("app-agrupado"))
    captura("06-agrupadas", "/dev/app-agrupado/pulls")
    p = [x for x in prs("app-agrupado") if "menores" in x["title"]]
    if p:
        anota("la PR agrupada (recorte del cuerpo)", "cuerpo de la PR", (p[0].get("body") or "")[:2500])
        captura("07-pr-agrupada", f"/dev/app-agrupado/pulls/{p[0]['number']}")
    d = dashboard("app-agrupado")
    if d:
        anota("el panel: mayores esperando aprobación", f"issue #{d['number']}", (d.get("body") or "")[:2500])
        captura("08-aprobacion", f"/dev/app-agrupado/issues/{d['number']}")

    L.limpiar()
    cab = ["# SALIDA — Renovate (vídeo 329)", "",
           f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. "
           f"Gitea (gitea/gitea:latest) + {IMG} en Docker."]
    (AQUI / "SALIDA.md").write_text("\n".join(cab + salida) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
