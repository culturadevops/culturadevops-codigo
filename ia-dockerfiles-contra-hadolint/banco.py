# -*- coding: utf-8 -*-
"""Piezas comunes del banco del 711: hadolint, docker build, tamaño, usuario, `latest` y si arranca.
Todo lo de Docker lleva el prefijo v711-: builder propio (su caché se va con él), red, contenedores e imágenes."""
import json
import os
import re
import subprocess
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
HADOLINT = "hadolint/hadolint:v2.14.0"
CURL = "curlimages/curl:8.11.1"
BUILDER = "v711-builder"
RED = "v711-net"


def docker(args, timeout=900, **kw):
    try:
        return subprocess.run(["docker"] + args, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=timeout, **kw)
    except subprocess.TimeoutExpired as e:
        return subprocess.CompletedProcess(e.cmd, 124, "", "timeout")


def preparar():
    if docker(["buildx", "inspect", BUILDER]).returncode != 0:
        docker(["buildx", "create", "--name", BUILDER, "--driver", "docker-container"])
    docker(["buildx", "inspect", "--bootstrap", BUILDER])
    if docker(["network", "inspect", RED]).returncode != 0:
        docker(["network", "create", RED])


def hadolint(ruta):
    with open(ruta, encoding="utf-8") as f:
        txt = f.read()
    r = docker(["run", "--rm", "-i", "--network", "none", HADOLINT, "hadolint", "-f", "json", "-"], input=txt, timeout=60)
    try:
        return json.loads(r.stdout or "[]")
    except Exception:
        return [{"code": "PARSE", "level": "error", "line": 0, "message": (r.stdout + r.stderr)[:200]}]


def tty(avisos):
    return "\n".join(f"Dockerfile:{a['line']} {a['code']} {a['level']}: {a['message']}" for a in avisos)


def imagenes_base(ruta):
    """[(imagen, usa_latest)] de cada FROM que no sea otra etapa ni scratch."""
    with open(ruta, encoding="utf-8") as f:
        lineas = f.read().splitlines()
    etapas, res = set(), []
    for l in lineas:
        m = re.match(r"\s*FROM\s+(?:--platform=\S+\s+)?(\S+)(?:\s+AS\s+(\S+))?", l, re.I)
        if not m:
            continue
        img = m.group(1)
        if img.lower() not in etapas and img != "scratch":
            sin_digest = img.split("@")[0]
            ultimo = sin_digest.rsplit("/", 1)[-1]
            tag = ultimo.split(":", 1)[1] if ":" in ultimo else ""
            res.append((img, "@" not in img and tag in ("", "latest")))
        if m.group(2):
            etapas.add(m.group(2).lower())
    return res


def construir(app, dockerfile, tag):
    t0 = time.time()
    r = docker(["buildx", "build", "--builder", BUILDER, "--load", "--progress", "plain", "-t", tag, "-f",
                os.path.abspath(dockerfile), os.path.join(AQUI, "apps", app)], timeout=1200)
    seg = round(time.time() - t0, 1)
    if r.returncode != 0:
        errs = [l for l in r.stderr.splitlines() if "ERROR" in l or "error" in l.lower()]
        return False, seg, "\n".join(errs[-4:])[-600:]
    return True, seg, ""


def inspeccionar(tag):
    r = docker(["image", "inspect", tag])
    d = json.loads(r.stdout)[0]
    usuario = (d.get("Config") or {}).get("User") or ""
    root = usuario.split(":")[0] in ("", "root", "0")
    # «disco» = lo que ocupa descomprimida (columna DISK USAGE de `docker images`); «bytes» = contenido comprimido (inspect .Size)
    ls = json.loads(docker(["image", "ls", "--format", "json", tag]).stdout.splitlines()[0])
    m = re.match(r"([\d.]+)\s*([kMG]?B)", ls["Size"])
    mb = float(m.group(1)) * {"B": 1e-6, "kB": 1e-3, "MB": 1, "GB": 1000}[m.group(2)]
    return {"bytes": d["Size"], "disco_mb": round(mb, 1), "usuario": usuario, "root": root}


def arranca(tag, espera=40):
    nombre = "v711-run"
    docker(["rm", "-f", nombre])
    r = docker(["run", "-d", "--rm", "--name", nombre, "--network", RED, "--cpus", "1", "--memory", "1g", tag])
    if r.returncode != 0:
        return False, "no arrancó: " + r.stderr[-200:]
    ok, resp = False, ""
    t0 = time.time()
    while time.time() - t0 < espera:
        c = docker(["run", "--rm", "--network", RED, CURL, "-s", "-m", "3", f"http://{nombre}:8080/"], timeout=30)
        resp = c.stdout.strip()
        if c.returncode == 0 and resp.startswith("ok"):
            ok = True
            break
        vivo = docker(["inspect", "-f", "{{.State.Running}}", nombre]).stdout.strip()
        if vivo != "true":
            break
        time.sleep(2)
    logs = docker(["logs", "--tail", "5", nombre]).stdout + docker(["logs", "--tail", "5", nombre]).stderr
    docker(["rm", "-f", nombre])
    return ok, ("" if ok else logs[-300:])


def borrar_imagen(tag):
    docker(["rmi", "-f", tag])


def limpiar():
    docker(["rm", "-f", "v711-run"])
    for img in docker(["images", "--format", "{{.Repository}}:{{.Tag}}", "--filter", "reference=v711-*"]).stdout.split():
        docker(["rmi", "-f", img])
    docker(["network", "rm", RED])
    docker(["buildx", "rm", BUILDER])
