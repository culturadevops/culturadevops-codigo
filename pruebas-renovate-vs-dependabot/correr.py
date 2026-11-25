# -*- coding: utf-8 -*-
"""Renovate vs Dependabot — banco de pruebas del vídeo 343 (cultura-devops, serie versus).

El MISMO repositorio (el del vídeo 329: dependencias de 2021 en npm, pip y un Dockerfile) con los dos, en local:
  · Dependabot: dependabot-cli oficial de GitHub (github.com/dependabot/cli), `update <ecosistema> --local`. Es el
    mismo motor que corre en GitHub; lo que devuelve son las PR que abriría («create_pull_request»).
  · Renovate: imagen oficial, plataforma `local` (no crea ramas: extrae y calcula; se leen del registro en JSON
    las actualizaciones y la rama de cada una), con config:recommended, que es lo que propone su PR de bienvenida.
Pruebas: 1) por defecto: cuántas PR y a qué versión; 2) agrupando; 3) tiempo e imágenes.

    python correr.py          (dependabot.exe en DEPENDABOT o en el PATH)
"""
import collections
import json
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = AQUI / "repo"
DBOT = os.environ.get("DEPENDABOT") or shutil.which("dependabot") or "dependabot"
RENO = "renovate/renovate:latest"
salida = []


def sh(cmd, timeout=1200, env=None):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
                       env={**os.environ, "MSYS_NO_PATHCONV": "1", **(env or {})})
    return (r.stdout + r.stderr).strip()


def anota(titulo, cmd_txt, texto):
    salida.extend(["", f"### {titulo}", "", f"`$ {cmd_txt}`", "", "```", texto.strip(), "```"])
    print(f"--- {titulo}\n{texto.strip()[:1500]}\n", flush=True)


def seccion(t):
    salida.extend(["", f"## {t}"])
    print(f"\n===== {t}", flush=True)


def dependabot(eco, job=None):
    out = AQUI / f"_dbot-{eco}{'-grupo' if job else ''}.yaml"
    c = [DBOT, "update"] + (["-f", str(job)] if job else [eco, "lab/app"]) + ["--local", str(REPO), "-o", str(out)]
    t0 = time.time()
    log = sh(c)
    dt = time.time() - t0
    prs = [l.strip() for l in log.splitlines() if re.search(r"\| created \|", l)]
    prs = [re.sub(r"^updater \| \| created \| ", "", p).rstrip(" |") for p in prs]
    n = out.read_text(encoding="utf-8").count("create_pull_request") if out.exists() else 0
    return n, prs, dt, log


def renovate(config):
    t0 = time.time()
    log = sh(["docker", "run", "--rm", "-v", f"{REPO}:/usr/src/app", "-w", "/usr/src/app",
              "-e", "RENOVATE_PLATFORM=local", "-e", "RENOVATE_ONBOARDING=false", "-e", "RENOVATE_REQUIRE_CONFIG=optional",
              "-e", "RENOVATE_CONFIG=" + json.dumps(config), "-e", "LOG_LEVEL=debug", "-e", "LOG_FORMAT=json", RENO])
    dt = time.time() - t0
    ramas = collections.OrderedDict()
    for l in log.splitlines():
        try:
            j = json.loads(l)
        except Exception:
            continue
        if j.get("msg") == "packageFiles with updates":
            for mgr, files in j["config"].items():
                for f in files:
                    for d in f.get("deps", []):
                        for u in d.get("updates", []):
                            ramas.setdefault(u.get("branchName"), []).append(
                                f"{d.get('depName')} {d.get('currentValue')} → {u.get('newValue')} ({u.get('updateType')})")
    return ramas, dt


def main():
    seccion("1 · Versiones y el repositorio")
    anota("versiones", f"dependabot --version; docker run {RENO} renovate --version",
          sh([DBOT, "--version"]) + "\nrenovate " + sh(["docker", "run", "--rm", RENO, "renovate", "--version"]).splitlines()[-1])
    for f in ("package.json", "requirements.txt", "Dockerfile"):
        anota(f, f"cat {f}", (REPO / f).read_text(encoding="utf-8"))

    seccion("2 · Por defecto")
    total, filas, tiempo = 0, [], 0.0
    for eco in ("npm_and_yarn", "pip", "docker"):
        n, prs, dt, _ = dependabot(eco)
        total += n
        tiempo += dt
        filas.append(f"[{eco}] {n} PR en {dt:.0f} s")
        filas += [f"  {p}" for p in prs]
    anota("Dependabot: una pasada por ecosistema", "dependabot update <ecosistema> lab/app --local repo",
          "\n".join(filas) + f"\n\nTOTAL: {total} PR · {tiempo:.0f} s")
    ramas, dt = renovate({"extends": ["config:recommended"]})
    anota("Renovate con config:recommended", "renovate --platform=local  (config:recommended)",
          "\n".join(f"{r}\n    " + "\n    ".join(v) for r, v in ramas.items()) + f"\n\nTOTAL: {len(ramas)} ramas · {dt:.0f} s")

    seccion("3 · Agrupando")
    job = AQUI / "job-npm-grupo.yaml"
    n, prs, dt, _ = dependabot("npm_and_yarn", job)
    anota("Dependabot: un grupo con todo npm", "cat job-npm-grupo.yaml; dependabot update -f job-npm-grupo.yaml --local repo",
          job.read_text(encoding="utf-8") + f"\n→ {n} PR en {dt:.0f} s\n" + "\n".join(f"  {p}" for p in prs))
    cfg = {"extends": ["config:recommended"], "packageRules": [{"matchUpdateTypes": ["minor", "patch"], "groupName": "menores y parches"}]}
    ramas, dt = renovate(cfg)
    anota("Renovate: menores y parches juntos", "RENOVATE_CONFIG=" + json.dumps(cfg, ensure_ascii=False),
          "\n".join(f"{r}\n    " + "\n    ".join(v) for r, v in ramas.items()) + f"\n\nTOTAL: {len(ramas)} ramas · {dt:.0f} s")

    seccion("4 · Lo que descarga cada uno")
    imgs = [l for l in sh(["docker", "images", "--format", "{{.Repository}}:{{.Tag}} {{.Size}}"]).splitlines()
            if "dependabot" in l or l.startswith("renovate/renovate:latest")]
    anota("imágenes", "docker images | grep -E 'dependabot|renovate'", "\n".join(sorted(imgs)))

    cab = ["# SALIDA — Renovate vs Dependabot (vídeo 343)", "",
           f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. Dependabot con dependabot-cli en "
           f"local (el motor de GitHub); Renovate con la plataforma local. Ninguno crea PR de verdad: se lee lo que abrirían."]
    (AQUI / "SALIDA.md").write_text("\n".join(cab + salida) + "\n", encoding="utf-8")
    print("SALIDA.md escrita")


if __name__ == "__main__":
    main()
