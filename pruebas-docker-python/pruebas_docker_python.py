# -*- coding: utf-8 -*-
"""pruebas_docker_python.py — mide los 4 Dockerfiles de Python y guarda la salida LITERAL
en `recursos/pruebas-docker-python/SALIDA.md`. Vídeo 153 · docker-con-python-4-dockerfiles.

Las mediciones:
    1. build FRÍO (sin caché de capas, --no-cache) por variante
    2. build TIBIO tras cambiar SOLO el código (¿sobrevive la caché de pip?)
    3. tamaño de imagen (descarga = inspect Size con containerd; disco = docker images)
    4. contexto que viaja al demonio, con y sin .dockerignore
    5. humo: cada imagen levanta y contesta /salud

    python canales/cultura-devops/investigacion/pruebas_docker_python.py
"""
import io
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = Path(__file__).resolve().parent.parent / "recursos" / "pruebas-docker-python"

VARIANTES = [
    ("1-ingenuo", "Dockerfile.1-ingenuo"),
    ("2-slim", "Dockerfile.2-slim"),
    ("3-multistage", "Dockerfile.3-multistage"),
    ("4-uv", "Dockerfile.4-uv"),
]


def sh(args, **kw):
    return subprocess.run(args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", **kw)


def mib(n):
    return f"{n/1048576:.1f} MiB"


R = {}

# ── 1 y 2 · builds ───────────────────────────────────────────────────────
app = BASE / "app" / "app.py"
original = app.read_text(encoding="utf-8")
for clave, df in VARIANTES:
    ref = f"cdo-dockerpy-{clave}:1"
    t0 = time.perf_counter()
    r = sh(["docker", "build", "--no-cache", "-f", str(BASE / df), "-t", ref, str(BASE)])
    frio = time.perf_counter() - t0
    if r.returncode != 0:
        raise SystemExit(f"[!] no construye {clave}:\n{r.stderr[-800:]}")
    # cambia SOLO el código y re-construye: la caché de dependencias ¿vive o muere?
    app.write_text(original + f"\n# cambio {clave}\n", encoding="utf-8")
    t0 = time.perf_counter()
    r = sh(["docker", "build", "-f", str(BASE / df), "-t", ref, str(BASE)])
    tibio = time.perf_counter() - t0
    app.write_text(original, encoding="utf-8")
    R[clave] = {"frio_s": round(frio, 1), "tibio_s": round(tibio, 1)}
    print(f"{clave:14s} frío {frio:6.1f} s · tras tocar el código {tibio:5.1f} s")

# ── 3 · tamaños ──────────────────────────────────────────────────────────
en_disco = {}
r = sh(["docker", "images", "--format", "{{.Repository}}:{{.Tag}}\t{{.Size}}"])
for linea in (r.stdout or "").splitlines():
    if "\t" in linea:
        ref, tam = linea.split("\t", 1)
        en_disco[ref] = tam.strip()
for clave, _ in VARIANTES:
    ref = f"cdo-dockerpy-{clave}:1"
    rr = sh(["docker", "image", "inspect", ref, "--format", "{{.Size}}"])
    R[clave]["descarga"] = int(rr.stdout.strip())
    R[clave]["disco"] = en_disco.get(ref, "?")
    print(f"{clave:14s} descarga {mib(R[clave]['descarga']):>10s} · disco {R[clave]['disco']}")

# ── 4 · el contexto ──────────────────────────────────────────────────────
basura = BASE / "_basura"
basura.mkdir(exist_ok=True)
(basura / "modelo.bin").write_bytes(b"\0" * (80 * 1024 * 1024))
ign = BASE / ".dockerignore"
guardado = ign.read_text(encoding="utf-8")


def contexto():
    r = sh(["docker", "build", "-f", str(BASE / "Dockerfile.2-slim"),
            "-t", "cdo-dockerpy-ctx:1", str(BASE)])
    for linea in (r.stdout + r.stderr).splitlines():
        if "transferring context" in linea and "B" in linea:
            return linea.strip()
    return "?"


ign.unlink()
R["contexto_sin"] = contexto()
ign.write_text(guardado, encoding="utf-8")
R["contexto_con"] = contexto()
print("contexto SIN .dockerignore:", R["contexto_sin"])
print("contexto CON .dockerignore:", R["contexto_con"])

# ── 5 · humo ─────────────────────────────────────────────────────────────
for i, (clave, _) in enumerate(VARIANTES):
    ref = f"cdo-dockerpy-{clave}:1"
    nombre = f"cdo-dockerpy-{clave}"
    sh(["docker", "rm", "-f", nombre])
    sh(["docker", "run", "-d", "--name", nombre, "-p", f"{9400+i}:8000", ref])
    ok = False
    for _ in range(60):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{9400+i}/salud", timeout=2) as h:
                ok = h.status == 200
                break
        except Exception:
            time.sleep(0.5)
    R[clave]["humo"] = ok
    print(f"{clave:14s} responde /salud: {ok}")
    sh(["docker", "rm", "-f", nombre])

(BASE / "_salida_cruda.json").write_text(json.dumps(R, indent=1), encoding="utf-8")

li = ["# SALIDA — Los 4 Dockerfiles de Python, medidos en esta máquina", "",
      f"> Corrida del {time.strftime('%Y-%m-%d %H:%M')}. Regenerable con",
      "> `python investigacion/pruebas_docker_python.py`. ⛔ Ninguna cifra de blog.",
      "> App: Flask 3.1.0 + gunicorn 23.0.0 (dos rutas). Docker 29.6.2.", "",
      "| variante | build frío | tras tocar SOLO el código | descarga | en disco | /salud |",
      "|---|---|---|---|---|---|"]
for clave, _ in VARIANTES:
    d = R[clave]
    li.append(f"| {clave} | {d['frio_s']} s | **{d['tibio_s']} s** | {mib(d['descarga'])} "
              f"| {d['disco']} | {'✅' if d['humo'] else '⛔'} |")
li += ["", "## El contexto que viaja al demonio (con 80 MB de basura en la carpeta)", "",
       f"- SIN `.dockerignore`: `{R['contexto_sin']}`",
       f"- CON `.dockerignore`: `{R['contexto_con']}`", ""]
(BASE / "SALIDA.md").write_text("\n".join(li), encoding="utf-8")
print("\n[ok] escrito", BASE / "SALIDA.md")
