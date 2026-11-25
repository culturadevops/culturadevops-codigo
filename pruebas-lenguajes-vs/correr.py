# -*- coding: utf-8 -*-
"""correr.py — «¿Python o X?» y «¿Node o X?» para cultura-devops (pedido del dueño 2026-11-04: «vídeos similares a Go con Kotlin
pero para culturadevops, Python vs otros y Node vs otros»).

Mismo banco que la serie «¿Go o X?» de golandia (pruebas_go_java_revancha.py + pruebas_go_vs_x.py), con los MISMOS servidores
(se leen de canales/golandia/recursos/pruebas-go-*; no se copian): el mismo contrato /suma (CPU), /trabajo (objetos, mapa, orden y
JSON armado a mano). Servidores limitados a 2 CPU y 1 GiB, `hey -c 16` desde otro contenedor, y antes de medir se comprueba que
todos devuelven exactamente lo mismo. La diferencia: el lenguaje de referencia es Python o Node, no Go.

    python correr.py python java|rust|php        → SALIDA-python-<x>.md
    python correr.py node bun|deno|php           → SALIDA-node-<x>.md
⛔ Ninguna cifra de blog: lo que diga el vídeo sale de la SALIDA de aquí.
"""

import json
import statistics
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
G = Path(r"<proyecto>\canales\golandia")
sys.path.insert(0, str(G / "investigacion"))
import pruebas_go_java_revancha as R  # noqa: E402
import pruebas_go_vs_x as X  # noqa: E402

GR = G / "recursos"
R.RED = "cdvs"

L = {
    "python": dict(nombre="Python", ctx=GR / "pruebas-go-vs-python", df="Dockerfile.python", etapa=None, img="cd-vs-python:1",
                   base="python:3.13.17-slim + FastAPI 0.162 + uvicorn 0.54", que="pip install de FastAPI + uvicorn",
                   variantes=[("python (1 proceso)", {"WORKERS": "1"}), ("python (2 procesos)", {"WORKERS": "2"})],
                   version=["docker", "run", "--rm", "--entrypoint", "python", "cd-vs-python:1", "--version"]),
    "node": dict(nombre="Node", ctx=GR / "pruebas-go-bun-node", df="Dockerfile.node", etapa=None, img="cd-vs-node:1",
                 base="node:24-slim (node:http, sin dependencias)", que="copiar servidor.js (no instala nada)",
                 variantes=[("node (1 proceso)", {"WORKERS": "1"}), ("node (2 procesos)", {"WORKERS": "2"})],
                 version=["docker", "run", "--rm", "--entrypoint", "node", "cd-vs-node:1", "--version"]),
    "bun": dict(nombre="Bun", ctx=GR / "pruebas-go-bun-node", df="Dockerfile.bun", etapa=None, img="cd-vs-bun:1",
                base="oven/bun:1.4.3-slim (el mismo servidor.js)", que="copiar servidor.js (no instala nada)",
                variantes=[("bun (1 proceso)", {"WORKERS": "1"}), ("bun (2 procesos)", {"WORKERS": "2"})],
                version=["docker", "run", "--rm", "--entrypoint", "bun", "cd-vs-bun:1", "--version"]),
    "deno": dict(nombre="Deno", ctx=GR / "pruebas-go-vs-deno", df="Dockerfile.deno", etapa=None, img="cd-vs-deno:1",
                 base="denoland/deno:2.9.8 (Deno.serve)", que="copiar + deno check (comprobar tipos)",
                 variantes=[("deno (1 hilo)", {"MODO": "run"}), ("deno serve --parallel", {"MODO": "paralelo"})],
                 version=["docker", "run", "--rm", "--entrypoint", "deno", "cd-vs-deno:1", "--version"]),
    "php": dict(nombre="PHP", ctx=GR / "pruebas-go-vs-php", df="Dockerfile.php", etapa=None, img="cd-vs-php:1",
                base="dunglas/frankenphp:1.13.3-php8.5", que="copiar el código (PHP no compila)",
                variantes=[("php clásico (FrankenPHP)", {}),
                           ("php worker (FrankenPHP)", {"MODO": "worker", "FRANKENPHP_CONFIG": "worker /app/public/index.php"}),
                           ("php worker + JIT", {"MODO": "worker", "FRANKENPHP_CONFIG": "worker /app/public/index.php",
                                                 "PHP_INI_SCAN_DIR": ":/app/jit"})],
                version=["docker", "run", "--rm", "--entrypoint", "frankenphp", "cd-vs-php:1", "version"]),
    "rust": dict(nombre="Rust", ctx=GR / "pruebas-go-vs-rust", df="Dockerfile.rust", etapa="build", img="cd-vs-rust:1",
                 base="debian:trixie-slim + binario (Rust 1.99.1, axum + tokio)", que="cargo build --release (descarga de crates incluida)",
                 variantes=[("rust (axum)", {})],
                 version=["docker", "run", "--rm", "rust:1.99.1-trixie", "rustc", "--version"]),
    "java": dict(nombre="Java", ctx=GR / "pruebas-go-java-revancha" / "java", df=str(AQUI / "Dockerfile.java"), etapa="build",
                 img="cd-vs-java:1", base="eclipse-temurin:25-jre + jar (com.sun.net.httpserver)", que="javac + jar",
                 variantes=[("java (hilos virtuales)", {"EJECUTOR": "virtual"}), ("java (hilos de plataforma)", {"EJECUTOR": "plataforma"})],
                 version=["docker", "run", "--rm", "eclipse-temurin:25-jdk", "java", "-version"]),
}
(AQUI / "Dockerfile.java").write_text(
    "FROM eclipse-temurin:25-jdk AS build\nWORKDIR /src\nCOPY Servidor.java /src/\n"
    "RUN javac -d /tmp/c Servidor.java && jar --create --file /servidor.jar --main-class Servidor -C /tmp/c .\n"
    "FROM eclipse-temurin:25-jre\nCOPY --from=build /servidor.jar /app/servidor.jar\nEXPOSE 8080\n"
    "ENTRYPOINT [\"java\", \"-jar\", \"/app/servidor.jar\"]\n", encoding="utf-8")


def df_de(cfg):
    d = Path(cfg["df"])
    return d if d.is_absolute() else cfg["ctx"] / d


def construir(k, cfg):
    args = ["docker", "build", "-q", "--no-cache", "-f", str(df_de(cfg))]
    args += (["--target", cfg["etapa"], "-t", cfg["img"] + "-etapa"] if cfg["etapa"] else ["-t", cfg["img"]])
    # Primero una construcción sin cronometrar: deja descargadas las imágenes base (si no, el tiempo incluiría la descarga).
    r = R.sh(["docker", "build", "-q", "-f", str(df_de(cfg)), "-t", cfg["img"], str(cfg["ctx"])])
    assert r.returncode == 0, r.stderr[-2000:]
    t0 = time.perf_counter()
    r = R.sh(args + [str(cfg["ctx"])])
    seg = time.perf_counter() - t0
    assert r.returncode == 0, r.stderr[-2000:]
    if cfg["etapa"]:
        r = R.sh(["docker", "build", "-q", "-f", str(df_de(cfg)), "-t", cfg["img"], str(cfg["ctx"])])
        assert r.returncode == 0, r.stderr[-2000:]
    return seg


def mismo_resultado(ref):
    R.w("## 0 · ¿Hacen lo mismo? (antes de medir)\n")
    salidas = {}
    for nombre, imagen, env in R.VARIANTES:
        t0 = R.arrancar(nombre, imagen, env, puerto=9300)
        R.esperar_200(9300, t0)
        j = json.loads(urllib.request.urlopen(f"http://127.0.0.1:9300/trabajo?n={R.N_TRABAJO}").read())
        s = json.loads(urllib.request.urlopen(f"http://127.0.0.1:9300/suma?n={R.N_SUMA}").read())
        salidas[nombre] = (j["total"], [x["id"] for x in j["primeros"]], s["suma"])
        R.sh(["docker", "rm", "-f", "srv"])
    base = salidas[ref]
    for nombre, v in salidas.items():
        ok = v == base
        R.w(f"- {nombre}: total {v[0]}, primeros ids {v[1][:5]}…, suma {v[2]} → {'igual' if ok else '⛔ DISTINTO'}")
        if not ok:
            raise SystemExit("las variantes no devuelven lo mismo: no se compara")
    R.w()


def computo_una():
    """Lo que tarda UNA petición en calcular, con el reloj del propio servidor (campo ns): sin red ni cola."""
    R.w("## A · Cómputo de UNA petición (mediana del reloj del propio servidor, 30 de calentamiento + 200 medidas, de una en una)\n")
    R.w("| variante | /trabajo (20.000 objetos) | /suma (200.000 vueltas) |")
    R.w("|---|---|---|")
    for nombre, imagen, env in R.VARIANTES:
        t0 = R.arrancar(nombre, imagen, env, puerto=9300)
        R.esperar_200(9300, t0)
        res = []
        for ruta, n in (("trabajo", R.N_TRABAJO), ("suma", R.N_SUMA)):
            ns = []
            for i in range(230):
                j = json.loads(urllib.request.urlopen(f"http://127.0.0.1:9300/{ruta}?n={n}").read())
                if i >= 30:
                    ns.append(j["ns"])
            res.append(statistics.median(ns) / 1e6)
        R.sh(["docker", "rm", "-f", "srv"])
        R.w(f"| {nombre} | {res[0]:.2f} ms | {res[1]:.3f} ms |")
    R.w()


def main():
    a, x = sys.argv[1], sys.argv[2]
    ca, cx = L[a], L[x]
    salida = AQUI / f"SALIDA-{a}-{x}.md"
    R.OUT.clear()
    R.sh(["docker", "network", "create", R.RED])
    if not R.sh(["docker", "image", "inspect", "golandia-revancha-hey:1"]).returncode == 0:
        r = R.sh(["docker", "build", "-q", "-f", str(GR / "pruebas-go-java-revancha" / "Dockerfile.hey"), "-t", "golandia-revancha-hey:1",
                  str(GR / "pruebas-go-java-revancha")])
        assert r.returncode == 0, r.stderr[-1500:]
    R.w(f"# SALIDA — ¿{ca['nombre']} o {cx['nombre']}? (cultura-devops)\n")
    R.w(f"> Corrida del {datetime.now():%Y-%m-%d %H:%M}. Regenerable con `python correr.py {a} {x}`. "
        "⛔ Ninguna cifra de blog: todo salió de aquí. Servidores de canales/golandia/recursos/pruebas-go-* (mismo contrato).\n")
    segs = {k: construir(k, c) for k, c in ((a, ca), (x, cx))}
    for k, c in ((a, ca), (x, cx)):
        v = R.sh(c["version"])
        R.w(f"- {k}: `{(v.stdout or v.stderr).strip().splitlines()[0]}` — {c['base']}")
    R.w(f"- Docker `{R.sh(['docker', 'version', '--format', '{{.Server.Version}}']).stdout.strip()}`. Servidores con {R.CPUS} CPU y "
        f"{R.MEM}; `hey -c {R.C}` con 4 CPU desde otro contenedor.")
    R.w(f"- /trabajo?n={R.N_TRABAJO}: crea {R.N_TRABAJO} objetos, los mete en un mapa, los ordena y arma un JSON a mano. "
        f"/suma?n={R.N_SUMA}: multiplicar y módulo en un bucle.\n")
    R.w("## 1 · Construir la imagen desde cero (`docker build --no-cache`, dependencias incluidas; la imagen base ya descargada no cuenta)\n")
    R.w("| lenguaje | qué se cronometra | segundos |")
    R.w("|---|---|---|")
    for k, c in ((a, ca), (x, cx)):
        R.w(f"| {k} | {c['que']} | {segs[k]:.1f} |")
    R.w()
    R.w("## 2 · Lo que despliegas\n")
    R.w("| imagen | base | tamaño en disco |")
    R.w("|---|---|---|")
    for k, c in ((a, ca), (x, cx)):
        s = int(R.sh(["docker", "image", "inspect", "-f", "{{.Size}}", c["img"]]).stdout.strip())
        R.w(f"| {k} | {c['base']} | {s / 1048576:.1f} MiB |")
    R.w()
    R.VARIANTES[:] = [(n, ca["img"], e) for n, e in ca["variantes"]] + [(n, cx["img"], e) for n, e in cx["variantes"]]
    mismo_resultado(ca["variantes"][0][0])
    X.arranque_y_memoria()
    computo_una()
    X.carga_max("trabajo", R.N_TRABAJO, "4 · Carga con memoria: /trabajo (objetos, mapa, orden, JSON), a tope")
    X.carga_max("suma", R.N_SUMA, "5 · Carga de CPU pura: /suma, a tope")
    X.ritmo_fijo("trabajo", R.N_TRABAJO, 0, "6 · Latencia de una petición sola: /trabajo")
    X.ritmo_fijo("suma", R.N_SUMA, 0, "7 · Latencia de una petición sola: /suma")
    salida.write_text("\n".join(R.OUT) + "\n", encoding="utf-8")
    print(f"\n[ok] {salida}")


if __name__ == "__main__":
    main()
