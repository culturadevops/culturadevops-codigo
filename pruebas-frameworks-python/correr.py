# -*- coding: utf-8 -*-
"""correr.py — banco de la «Tier list de frameworks web de Python 2026» (cultura-devops, vídeo 770).

El MISMO banco que «¿Python o X?» (recursos/pruebas-lenguajes-vs/correr.py) y que la serie «¿Go o X?» de golandia
(investigacion/pruebas_go_java_revancha.py = R, pruebas_go_vs_x.py = X), pero lo que cambia ahora es el framework, no el lenguaje:
  · la MISMA lógica (app/logica.py, copiada del servidor FastAPI de canales/golandia/recursos/pruebas-go-vs-python), y cada framework
    solo lee `n` y devuelve ese texto: /suma (CPU), /trabajo (objetos, dict, orden y JSON armado a mano);
  · cada uno con su servidor de producción habitual (app/arrancar.sh): Django, Flask y Falcon con gunicorn (workers síncronos);
    FastAPI, Starlette y Litestar con uvicorn (uvloop + httptools); Sanic con su propio servidor. 2 procesos (uno por CPU);
  · versiones fijadas en req/<fw>.txt; servidores con 2 CPU y 1 GiB; `hey -c 16` con 4 CPU desde otro contenedor;
  · antes de medir, se comprueba que todos devuelven el MISMO cuerpo byte a byte (quitando "ns", el reloj del cálculo).
Añadido respecto al banco de lenguajes: /suma?n=1, donde el cálculo es casi cero y lo que se mide es el coste del framework.

    python correr.py                  → SALIDA.md (todo; ~30 min, la máquina sin otras cargas)
    python correr.py --comprobar      → solo construir + sección 0 (¿devuelven lo mismo?), sin carga
    python correr.py --solo django,flask
⛔ Ninguna cifra de blog: lo que diga el vídeo sale de la SALIDA de aquí.
"""
import json
import re
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

R.RED = "fwpy"
HEY_IMG = "golandia-revancha-hey:1"

# clave → (nombre en pantalla, servidor)
FW = {
    "django": ("Django", "gunicorn 26.2 (workers síncronos)"),
    "flask": ("Flask", "gunicorn 26.2 (workers síncronos)"),
    "falcon": ("Falcon", "gunicorn 26.2 (workers síncronos)"),
    "fastapi": ("FastAPI", "uvicorn 0.54 + uvloop + httptools"),
    "starlette": ("Starlette", "uvicorn 0.54 + uvloop + httptools"),
    "litestar": ("Litestar", "uvicorn 0.54 + uvloop + httptools"),
    "sanic": ("Sanic", "su propio servidor (uvloop)"),
}
VARIANTES = [  # (nombre, framework, entorno extra)
    ("django", "django", {}),
    ("flask", "flask", {}),
    ("falcon", "falcon", {}),
    ("fastapi (def)", "fastapi", {}),
    ("fastapi (async def)", "fastapi", {"MODO": "async"}),
    ("starlette", "starlette", {}),
    ("litestar", "litestar", {}),
    ("sanic", "sanic", {}),
]
REF = "fastapi (def)"


def img(fw):
    return f"cd-fwpy-{fw}:1"


def construir(fw):
    """`docker build --no-cache` cronometrado (pip install incluido; la imagen base ya descargada no cuenta)."""
    base = ["docker", "build", "-q", "--build-arg", f"FW={fw}", "-f", str(AQUI / "Dockerfile"), "-t", img(fw)]
    r = R.sh(base + [str(AQUI)])  # primero sin cronometrar: deja la imagen base descargada
    assert r.returncode == 0, r.stderr[-2000:]
    t0 = time.perf_counter()
    r = R.sh(base[:3] + ["--no-cache"] + base[3:] + [str(AQUI)])
    seg = time.perf_counter() - t0
    assert r.returncode == 0, r.stderr[-2000:]
    return seg


def directas(fw):
    return ", ".join(x.strip() for x in (AQUI / "req" / f"{fw}.in").read_text(encoding="utf-8").splitlines() if x.strip())


def pedir(ruta, n, puerto=9300):
    with urllib.request.urlopen(f"http://127.0.0.1:{puerto}/{ruta}?n={n}") as r:
        return r.read(), r.headers.get("Content-Type")


def sin_ns(b):
    return re.sub(rb',"ns":\d+}$', b"}", b)


def mismo_resultado():
    R.w("## 0 · ¿Hacen lo mismo? (antes de medir)\n")
    R.w(f"El cuerpo de /trabajo?n={R.N_TRABAJO}, /suma?n={R.N_SUMA} y /suma?n=1, comparado byte a byte con {REF} "
        "quitando solo el campo \"ns\" (el reloj del cálculo).\n")
    salidas = {}
    for nombre, imagen, env in R.VARIANTES:
        t0 = R.arrancar(nombre, imagen, env, puerto=9300)
        R.esperar_200(9300, t0)
        res = []
        for ruta, n in (("trabajo", R.N_TRABAJO), ("suma", R.N_SUMA), ("suma", 1)):
            cuerpo, ct = pedir(ruta, n)
            res.append((sin_ns(cuerpo), ct.split(";")[0].strip().lower()))
        salidas[nombre] = res
        R.sh(["docker", "rm", "-f", "srv"])
    ref = salidas[REF]
    for nombre, v in salidas.items():
        ok = v == ref
        j = json.loads(v[0][0])
        s = json.loads(v[1][0])
        R.w(f"- {nombre}: total {j['total']}, primeros ids {[x['id'] for x in j['primeros']][:5]}…, suma {s['suma']}, "
            f"{len(v[0][0])} + {len(v[1][0])} + {len(v[2][0])} bytes, {v[0][1]} → {'idéntico' if ok else '⛔ DISTINTO'}")
        if not ok:
            raise SystemExit("las variantes no devuelven lo mismo: no se compara")
    R.w()


def computo_una():
    """Lo que tarda UNA petición en calcular, con el reloj del propio cálculo (campo ns): debería ser igual en todos (es la misma
    lógica); si no lo es, algo del framework se mete en el cálculo (el threadpool, el bucle de eventos…)."""
    R.w("## A · Cómputo de UNA petición (mediana del campo ns, 30 de calentamiento + 200 medidas, de una en una)\n")
    R.w("| variante | /trabajo (20.000 objetos) | /suma (200.000 vueltas) |")
    R.w("|---|---|---|")
    for nombre, imagen, env in R.VARIANTES:
        t0 = R.arrancar(nombre, imagen, env, puerto=9300)
        R.esperar_200(9300, t0)
        res = []
        for ruta, n in (("trabajo", R.N_TRABAJO), ("suma", R.N_SUMA)):
            ns = []
            for i in range(230):
                j = json.loads(pedir(ruta, n)[0])
                if i >= 30:
                    ns.append(j["ns"])
            res.append(statistics.median(ns) / 1e6)
        R.sh(["docker", "rm", "-f", "srv"])
        R.w(f"| {nombre} | {res[0]:.2f} ms | {res[1]:.3f} ms |")
    R.w()


def main():
    solo = None
    if "--solo" in sys.argv:
        solo = set(sys.argv[sys.argv.index("--solo") + 1].split(","))
    comprobar = "--comprobar" in sys.argv
    variantes = [v for v in VARIANTES if solo is None or v[1] in solo]
    fws = list(dict.fromkeys(fw for _, fw, _ in variantes))
    global REF
    if REF not in [n for n, _, _ in variantes]:
        REF = variantes[0][0]

    R.OUT.clear()
    R.sh(["docker", "network", "create", R.RED])
    if R.sh(["docker", "image", "inspect", HEY_IMG]).returncode != 0:
        r = R.sh(["docker", "build", "-q", "-f", str(G / "recursos" / "pruebas-go-java-revancha" / "Dockerfile.hey"), "-t", HEY_IMG,
                  str(G / "recursos" / "pruebas-go-java-revancha")])
        assert r.returncode == 0, r.stderr[-1500:]

    R.w("# SALIDA — Tier list de frameworks web de Python 2026 (cultura-devops, vídeo 770)\n")
    R.w(f"> Corrida del {datetime.now():%Y-%m-%d %H:%M}. Regenerable con `python correr.py`. ⛔ Ninguna cifra de blog: todo salió "
        "de aquí. La misma lógica (app/logica.py) en todos; cambia solo el framework y su servidor.\n")
    segs = {fw: construir(fw) for fw in fws}
    v = R.sh(["docker", "run", "--rm", "--entrypoint", "python", img(fws[0]), "--version"])
    R.w(f"- `{(v.stdout or v.stderr).strip()}` (python:3.13.17-slim, la misma base que «¿Python o X?»). Docker "
        f"`{R.sh(['docker', 'version', '--format', '{{.Server.Version}}']).stdout.strip()}`.")
    R.w(f"- Servidores con {R.CPUS} CPU y {R.MEM}, 2 procesos cada uno (uno por CPU); `hey -c {R.C}` con 4 CPU desde otro contenedor.")
    R.w(f"- /trabajo?n={R.N_TRABAJO}: crea {R.N_TRABAJO} objetos, los mete en un dict, los ordena y arma un JSON a mano. "
        f"/suma?n={R.N_SUMA}: multiplicar y módulo en un bucle. /suma?n=1: el cálculo es casi cero, queda el coste del framework.")
    R.w("- Rutas: Django, Flask y Falcon síncronas (WSGI). FastAPI `def` y Starlette `def` → threadpool; Litestar `sync_to_thread=True` "
        "→ threadpool; FastAPI `async def` y Sanic `async def` → en el bucle de eventos.\n")
    R.w("| framework | servidor | dependencias directas (versiones fijadas en req/<fw>.txt) |")
    R.w("|---|---|---|")
    for fw in fws:
        R.w(f"| {FW[fw][0]} | {FW[fw][1]} | {directas(fw)} |")
    R.w()
    R.w("## 1 · Construir la imagen desde cero (`docker build --no-cache`: pip install incluido; la imagen base ya descargada no cuenta)\n")
    R.w("| framework | paquetes instalados | segundos |")
    R.w("|---|---|---|")
    for fw in fws:
        n = len([x for x in (AQUI / "req" / f"{fw}.txt").read_text(encoding="utf-8").splitlines() if x.strip()])
        R.w(f"| {FW[fw][0]} | {n} | {segs[fw]:.1f} |")
    R.w()
    R.w("## 2 · Lo que despliegas\n")
    R.w("| framework | tamaño en disco (python:3.13.17-slim + dependencias + código) |")
    R.w("|---|---|")
    for fw in fws:
        s = int(R.sh(["docker", "image", "inspect", "-f", "{{.Size}}", img(fw)]).stdout.strip())
        R.w(f"| {FW[fw][0]} | {s / 1048576:.1f} MiB |")
    R.w()

    R.VARIANTES[:] = [(n, img(fw), env) for n, fw, env in variantes]
    mismo_resultado()
    if comprobar:
        (AQUI / "SALIDA-comprobacion.md").write_text("\n".join(R.OUT) + "\n", encoding="utf-8")
        print(f"\n[ok] {AQUI / 'SALIDA-comprobacion.md'} (sin carga)")
        return
    X.arranque_y_memoria()
    computo_una()
    X.carga_max("trabajo", R.N_TRABAJO, "4 · Carga con memoria: /trabajo (objetos, dict, orden, JSON), a tope")
    X.carga_max("suma", R.N_SUMA, "5 · Carga de CPU pura: /suma, a tope")
    X.carga_max("suma", 1, "6 · El coste del framework: /suma?n=1 (casi sin cálculo), a tope")
    X.ritmo_fijo("trabajo", R.N_TRABAJO, 0, "7 · Latencia de una petición sola: /trabajo")
    X.ritmo_fijo("suma", 1, 0, "8 · Latencia de una petición sola: /suma?n=1 (el framework solo)")
    nombre = "SALIDA.md" if solo is None else f"SALIDA-{'-'.join(sorted(solo))}.md"
    (AQUI / nombre).write_text("\n".join(R.OUT) + "\n", encoding="utf-8")
    print(f"\n[ok] {AQUI / nombre}")


if __name__ == "__main__":
    main()
