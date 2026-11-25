# -*- coding: utf-8 -*-
"""pruebas_uv_pip.py — uv contra pip con un requirements de verdad. Vídeo 157.

La revancha sembrada por el 153. Requirements de proyecto de datos (15 paquetes directos,
con sus transitivos). Todo en Docker, reloj del contenedor. Salida literal en
`recursos/pruebas-uv-pip/SALIDA.md`.

Mediciones:
    1. instalación FRÍA (caché vacía, red de por medio) — pip vs uv, mediana de 3
    2. instalación con la CACHÉ del gestor caliente (mismo contenedor, venv nuevo)
    3. cuántos paquetes reales quedan instalados y cuánto pesa el venv

    python canales/cultura-devops/investigacion/pruebas_uv_pip.py
"""
import io
import json
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = Path(__file__).resolve().parent.parent / "recursos" / "pruebas-uv-pip"
REPES = 3

R = {}


def sh(args, timeout=1800):
    return subprocess.run(args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def correr_en_docker(imagen, script):
    return sh(["docker", "run", "--rm",
               "-v", f"{BASE}:/lab", "-w", "/lab", imagen, "sh", "-c", script])


# ── 1 · frío ─────────────────────────────────────────────────────────────
print("1 · instalación fría (caché vacía, mediana de", REPES, ")")
FRIO = {
    "pip": ("python:3.13-slim",
            "t0=$(date +%s%N); python -m venv /v && /v/bin/pip install -q "
            "--no-cache-dir -r requirements-datos.txt; t1=$(date +%s%N); "
            "echo MS $(( (t1 - t0) / 1000000 ))"),
    "uv": ("ghcr.io/astral-sh/uv:python3.13-bookworm-slim",
           "t0=$(date +%s%N); uv venv /v -q && uv pip install -q --no-cache "
           "--python /v/bin/python -r requirements-datos.txt; t1=$(date +%s%N); "
           "echo MS $(( (t1 - t0) / 1000000 ))"),
}
for gestor, (imagen, script) in FRIO.items():
    tiempos = []
    for _ in range(REPES):
        r = correr_en_docker(imagen, script)
        m = re.search(r"^MS (\d+)", r.stdout, re.M)
        if not m:
            raise SystemExit(f"[!] {gestor} falló:\n{r.stdout[-300:]}\n{r.stderr[-500:]}")
        tiempos.append(int(m.group(1)))
        print(f"    · {gestor:4s} {tiempos[-1]/1000:.1f} s")
    R[f"{gestor}_frio_ms"] = tiempos

# ── 2 · caché caliente (venv nuevo, caché del gestor viva) ──────────────
print("2 · con la caché del gestor caliente (venv nuevo)")
CALIENTE = {
    "pip": ("python:3.13-slim",
            "python -m venv /v1 && /v1/bin/pip install -q -r requirements-datos.txt; "
            "t0=$(date +%s%N); python -m venv /v2 && /v2/bin/pip install -q "
            "-r requirements-datos.txt; t1=$(date +%s%N); echo MS $(( (t1 - t0) / 1000000 ))"),
    "uv": ("ghcr.io/astral-sh/uv:python3.13-bookworm-slim",
           "uv venv /v1 -q && uv pip install -q --python /v1/bin/python -r requirements-datos.txt; "
           "t0=$(date +%s%N); uv venv /v2 -q && uv pip install -q --python /v2/bin/python "
           "-r requirements-datos.txt; t1=$(date +%s%N); echo MS $(( (t1 - t0) / 1000000 ))"),
}
for gestor, (imagen, script) in CALIENTE.items():
    r = correr_en_docker(imagen, script)
    m = re.search(r"^MS (\d+)", r.stdout, re.M)
    if not m:
        raise SystemExit(f"[!] {gestor} caliente falló:\n{r.stdout[-300:]}\n{r.stderr[-500:]}")
    R[f"{gestor}_caliente_ms"] = int(m.group(1))
    print(f"    · {gestor:4s} {int(m.group(1))/1000:.1f} s")

# ── 3 · qué queda instalado ──────────────────────────────────────────────
print("3 · lo que queda instalado")
r = correr_en_docker("python:3.13-slim",
                     "python -m venv /v >/dev/null && /v/bin/pip install -q --no-cache-dir "
                     "-r requirements-datos.txt && /v/bin/pip list --format=freeze | wc -l "
                     "&& du -sm /v | cut -f1")
lineas = [x for x in r.stdout.split() if x.strip().isdigit()]
R["paquetes"], R["venv_mb"] = int(lineas[-2]), int(lineas[-1])
print(f"    · {R['paquetes']} paquetes · venv {R['venv_mb']} MB")

# ── salida ───────────────────────────────────────────────────────────────
pf = statistics.median(R["pip_frio_ms"]) / 1000
uf = statistics.median(R["uv_frio_ms"]) / 1000
li = [
    "# SALIDA — uv contra pip con un requirements de verdad, medidos en esta máquina", "",
    f"> Corrida del {time.strftime('%Y-%m-%d %H:%M')}. Regenerable con",
    "> `python investigacion/pruebas_uv_pip.py`. ⛔ Ninguna cifra de blog.",
    "> `requirements-datos.txt`: 15 paquetes directos de un proyecto de datos típico",
    f"> (pandas, numpy, scikit-learn, matplotlib, boto3…) → **{R['paquetes']} paquetes reales**",
    f"> instalados, venv de **{R['venv_mb']} MB**. Docker, reloj del contenedor.", "",
    "| medición | pip | uv | ratio |",
    "|---|---|---|---|",
    f"| instalación fría (mediana de {REPES}) | **{pf:.1f} s** | **{uf:.1f} s** | {pf/uf:.1f}x |",
    f"| con la caché del gestor caliente | {R['pip_caliente_ms']/1000:.1f} s "
    f"| {R['uv_caliente_ms']/1000:.1f} s "
    f"| {R['pip_caliente_ms']/max(R['uv_caliente_ms'],1):.1f}x |", "",
    f"Corridas frías completas: pip {[round(x/1000,1) for x in R['pip_frio_ms']]} s · "
    f"uv {[round(x/1000,1) for x in R['uv_frio_ms']]} s", "",
    "Contexto del 153 (ya medido): con DOS dependencias puras, uv no cambia nada",
    "(frío 7,1 s contra 3,1 por bajar su builder). Esta es la otra mitad de esa historia.",
]
(BASE / "SALIDA.md").write_text("\n".join(li), encoding="utf-8")
(BASE / "_salida_cruda.json").write_text(json.dumps(R, indent=1), encoding="utf-8")
print("\n[ok] escrito", BASE / "SALIDA.md")
