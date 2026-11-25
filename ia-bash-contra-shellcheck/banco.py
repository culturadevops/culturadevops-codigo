# -*- coding: utf-8 -*-
"""Piezas comunes del banco del 704: shellcheck, shfmt y ejecución en contenedor desechable."""
import json
import os
import subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
SHELLCHECK = "koalaman/shellcheck:v0.11.0"
SHFMT = "mvdan/shfmt:v3.12.0"
RUNNER = "v704-runner"  # debian:bookworm-20251020-slim + procps (Dockerfile.runner)


def docker(args, **kw):
    return subprocess.run(["docker"] + args, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def shellcheck(ruta):
    """Devuelve la lista de avisos (json1) de un script."""
    d, f = os.path.split(os.path.abspath(ruta))
    r = docker(["run", "--rm", "--network", "none", "-v", f"{d}:/mnt:ro", "-w", "/mnt", SHELLCHECK, "-f", "json1", f])
    try:
        return json.loads(r.stdout)["comments"]
    except Exception:
        return [{"code": -1, "level": "error", "line": 0, "message": "shellcheck no pudo leerlo: " + r.stderr[:200]}]


def gcc(avisos, nombre="script.sh"):
    return "\n".join(f"{nombre}:{a['line']}:{a.get('column', 1)}: {a['level']}: {a['message']} [SC{a['code']}]" for a in avisos)


def shfmt(ruta):
    """('ok'|'formato'|'sintaxis', detalle). -d: diferencia con el formato de shfmt."""
    d, f = os.path.split(os.path.abspath(ruta))
    r = docker(["run", "--rm", "--network", "none", "-v", f"{d}:/mnt:ro", "-w", "/mnt", SHFMT, "-d", f])
    if r.returncode == 0:
        return "ok", ""
    if r.stdout.startswith("---") or "@@" in r.stdout:
        return "formato", ""
    return "sintaxis", (r.stderr or r.stdout)[:200]


def tareas_sh():
    from tareas import tareas_sh as gen
    p = os.path.join(AQUI, "_h", "tareas.sh")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(gen())
    with open(os.path.join(AQUI, "runner.sh"), encoding="utf-8") as src, \
            open(os.path.join(AQUI, "_h", "runner.sh"), "w", encoding="utf-8", newline="\n") as dst:
        dst.write(src.read().replace("\r\n", "\n"))


def ejecutar(casos):
    """casos: [(etiqueta, id, ruta_local)]. Corre todo en UN contenedor desechable, sin red.
    Devuelve {(etiqueta, id): {'control': (rc, ok, err), 'espacios': (...)}}."""
    tareas_sh()
    h = os.path.join(AQUI, "_h")
    lista, mounts = [], {}
    for etq, n, ruta in casos:
        rel = os.path.relpath(os.path.abspath(ruta), AQUI).replace("\\", "/")
        lista.append(f"{etq} {n} /s/{rel}")
    with open(os.path.join(h, "lista.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lista) + "\n")
    r = docker(["run", "--rm", "--network", "none", "--cpus", "2", "--name", "v704-banco",
                "-v", f"{h}:/h:ro", "-v", f"{AQUI}:/s:ro", RUNNER, "bash", "/h/runner.sh"], timeout=3600)
    res = {}
    for linea in r.stdout.splitlines():
        p = linea.split("\t")
        if len(p) < 5:
            continue
        res.setdefault((p[0], int(p[1])), {})[p[2]] = (int(p[3]), p[4] == "1", p[5] if len(p) > 5 else "")
    if not res:
        raise RuntimeError("el banco no devolvió nada: " + r.stderr[-500:])
    return res
