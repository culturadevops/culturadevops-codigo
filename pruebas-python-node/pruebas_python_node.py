# -*- coding: utf-8 -*-
"""pruebas_python_node.py — mide Python contra Node y guarda la salida LITERAL en
`recursos/pruebas-python-node/SALIDA.md`. Vídeo 152 · python-vs-node-lo-medi.

Adaptado del corredor de go-vs-java (golandia/investigacion/pruebas_go_java.py): mismos
ejes, contendientes nuevos, sin fase de compilación (los dos son interpretados/JIT).

⛔ Cero cifras de blogs. El MISMO servidor HTTP en los dos, librería estándar contra
librería estándar (http.server con hilos contra node:http), cero frameworks, imágenes
oficiales slim.

Las cinco mediciones:
    1. lo que despliegas   → imagen (descarga y disco)
    2. arranque            → contenedor nuevo → primera respuesta, mediana de 8
                             + el «listo» que declara el propio proceso (LISTO_EN_MS)
    3. memoria en reposo   → docker stats con el servidor recién levantado
    4. templado y el JIT   → 2.000 peticiones de CPU: p50/p99, y frío contra templado
                             con el reloj DEL PROPIO PROCESO (campo ns del JSON)
    5. concurrencia        → 300 peticiones a la vez esperando 100 ms + memoria bajo carga

    python canales/cultura-devops/investigacion/pruebas_python_node.py
"""
import concurrent.futures
import io
import json
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = Path(__file__).resolve().parent.parent / "recursos" / "pruebas-python-node"

N_CPU = 200_000
REPES_FRIO = 8
INVOCACIONES = 2_000
CONCURRENTES = 300
IO_MS = 100

LENGUAJES = [
    ("python", "cdo-pyvsnode-python:1", 9501),
    ("node", "cdo-pyvsnode-node:1", 9502),
]

SALIDA = {}


def sh(args, **kw):
    return subprocess.run(args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", **kw)


def mib(n):
    return f"{n/1048576:.2f} MiB"


def p(v, q):
    v = sorted(v)
    return v[max(0, min(len(v) - 1, round(q * (len(v) - 1))))]


def parar(nombre):
    sh(["docker", "rm", "-f", nombre])


def esperar_ok(puerto, timeout=60):
    fin = time.perf_counter() + timeout
    while time.perf_counter() < fin:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{puerto}/suma?n=1", timeout=2) as r:
                if r.status == 200:
                    r.read()
                    return time.perf_counter()
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(0.002)
    raise SystemExit(f"[!] el puerto {puerto} nunca contestó")


def listo_interno(nombre):
    for _ in range(50):
        r = sh(["docker", "logs", nombre])
        for linea in (r.stderr or "").splitlines() + (r.stdout or "").splitlines():
            if linea.startswith("LISTO_EN_MS"):
                return float(linea.split()[1])
        time.sleep(0.05)
    return None


def memoria_mib(nombre):
    r = sh(["docker", "stats", "--no-stream", "--format", "{{.MemUsage}}", nombre])
    bruto = (r.stdout or "").strip().split("/")[0].strip()
    if bruto.endswith("GiB"):
        return float(bruto[:-3]) * 1024
    if bruto.endswith("MiB"):
        return float(bruto[:-3])
    if bruto.endswith("KiB"):
        return float(bruto[:-3]) / 1024
    return None


def construir():
    print("0 · construir las dos imágenes")
    for lang, imagen, _ in LENGUAJES:
        r = sh(["docker", "build", "-t", imagen, str(BASE / lang)])
        if r.returncode != 0:
            raise SystemExit(f"[!] docker build {lang}:\n{r.stderr[-500:]}")


def medir_imagenes():
    print("1 · imágenes")
    en_disco = {}
    r = sh(["docker", "images", "--format", "{{.Repository}}:{{.Tag}}\t{{.Size}}"])
    for linea in (r.stdout or "").splitlines():
        if "\t" in linea:
            ref, tam = linea.split("\t", 1)
            en_disco[ref] = tam.strip()
    filas = {}
    for ref in ["cdo-pyvsnode-python:1", "cdo-pyvsnode-node:1",
                "python:3.13-slim", "node:22-slim"]:
        rr = sh(["docker", "image", "inspect", ref, "--format", "{{.Size}}"])
        if rr.returncode == 0:
            filas[ref] = {"descarga": int(rr.stdout.strip()), "disco": en_disco.get(ref, "?")}
            print(f"    · {ref:26s} descarga {mib(filas[ref]['descarga']):>11s} "
                  f"disco {filas[ref]['disco']}")
    SALIDA["imagenes"] = filas


def medir_arranque():
    print("2 · arranque")
    filas = {}
    for lang, imagen, puerto in LENGUAJES:
        externos, internos = [], []
        for i in range(REPES_FRIO):
            nombre = f"pyvsnode-{lang}-frio-{i}"
            parar(nombre)
            t0 = time.perf_counter()
            r = sh(["docker", "run", "-d", "--name", nombre, "-p", f"{puerto}:8080", imagen])
            if r.returncode != 0:
                raise SystemExit(f"[!] docker run {lang}: {r.stderr}")
            t1 = esperar_ok(puerto)
            externos.append((t1 - t0) * 1000)
            li = listo_interno(nombre)
            if li is not None:
                internos.append(li)
            parar(nombre)
        filas[lang] = {"externo_ms": externos, "interno_ms": internos}
        print(f"    · {lang:7s} 1ª respuesta mediana {statistics.median(externos):.0f} ms · "
              f"proceso listo {statistics.median(internos):.1f} ms")
    SALIDA["arranque"] = filas


def medir_caliente():
    print("3-5 · memoria, templado y concurrencia")
    filas = {}
    for lang, imagen, puerto in LENGUAJES:
        nombre = f"pyvsnode-{lang}-caliente"
        parar(nombre)
        sh(["docker", "run", "-d", "--name", nombre, "-p", f"{puerto}:8080", imagen])
        esperar_ok(puerto)
        time.sleep(2)
        mem_reposo = memoria_mib(nombre)
        print(f"    · {lang:7s} memoria en reposo {mem_reposo:.1f} MiB")

        externos, internos = [], []
        for _ in range(INVOCACIONES):
            t0 = time.perf_counter()
            with urllib.request.urlopen(
                    f"http://127.0.0.1:{puerto}/suma?n={N_CPU}", timeout=30) as r2:
                cuerpo = json.loads(r2.read())
            externos.append((time.perf_counter() - t0) * 1000)
            internos.append(cuerpo["ns"] / 1e6)
        print(f"      templado ext p50 {p(externos, .5):.2f} ms · p99 {p(externos, .99):.2f} ms")
        print(f"      cómputo interno: primeras 20 → {statistics.median(internos[:20]):.3f} ms · "
              f"últimas 500 → {statistics.median(internos[-500:]):.3f} ms")
        mem_tras_cpu = memoria_mib(nombre)

        t0 = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENTES) as ex:
            futs = [ex.submit(
                lambda: urllib.request.urlopen(
                    f"http://127.0.0.1:{puerto}/espera?ms={IO_MS}", timeout=30).read())
                for _ in range(CONCURRENTES)]
            mem_bajo_carga = memoria_mib(nombre)
            for f in futs:
                f.result()
        total_conc = (time.perf_counter() - t0) * 1000
        mem_tras_conc = memoria_mib(nombre)
        print(f"      {CONCURRENTES} a la vez × {IO_MS} ms → total {total_conc:.0f} ms · "
              f"memoria bajo carga {mem_bajo_carga:.1f} MiB")
        parar(nombre)

        filas[lang] = {"mem_reposo_mib": mem_reposo, "mem_tras_cpu_mib": mem_tras_cpu,
                       "ext_ms": externos, "int_ms": internos,
                       "conc_total_ms": total_conc, "mem_bajo_carga_mib": mem_bajo_carga,
                       "mem_tras_conc_mib": mem_tras_conc}
    SALIDA["caliente"] = filas


def escribir_salida():
    v = {}
    for cmd_, clave in [(["docker", "--version"], "docker"),
                        (["docker", "run", "--rm", "python:3.13-slim", "python", "--version"],
                         "python"),
                        (["docker", "run", "--rm", "node:22-slim", "node", "--version"], "node")]:
        r = sh(cmd_)
        v[clave] = ((r.stdout or "").strip().splitlines() or ["?"])[0]

    li = []
    w = li.append
    w("# SALIDA — Python contra Node, medidos en esta máquina")
    w("")
    w(f"> Corrida del {time.strftime('%Y-%m-%d %H:%M')}. Regenerable con")
    w("> `python investigacion/pruebas_python_node.py`. ⛔ Ninguna cifra de blog.")
    w("")
    w(f"- `{v['docker']}` · `{v['python']}` (python:3.13-slim) · `{v['node']}` (node:22-slim)")
    w("- Mismo servidor HTTP, librería estándar en ambos (http.server con hilos / node:http).")
    w(f"- Trabajo de CPU por petición: {N_CPU:,} vueltas de multiplicar y módulo.".replace(",", "."))
    w("")
    w("## 1 · Imágenes")
    w("")
    w("| imagen | descarga | en disco |")
    w("|---|---|---|")
    for ref, d in SALIDA["imagenes"].items():
        w(f"| `{ref}` | {mib(d['descarga'])} | {d['disco']} |")
    w("")
    ar = SALIDA["arranque"]
    w(f"## 2 · Arranque (mediana de {REPES_FRIO})")
    w("")
    w("| lenguaje | 1ª respuesta (docker incluido) | proceso «listo» (su reloj) |")
    w("|---|---|---|")
    for lang in ("python", "node"):
        e = statistics.median(ar[lang]["externo_ms"])
        i = statistics.median(ar[lang]["interno_ms"])
        w(f"| {lang} | {e:.0f} ms | {i:.1f} ms |")
    w("")
    ca = SALIDA["caliente"]
    w("## 3 · Memoria (docker stats, MiB)")
    w("")
    w("| lenguaje | reposo | tras 2.000 de CPU | bajo 300 concurrentes | tras la carga |")
    w("|---|---|---|---|---|")
    for lang in ("python", "node"):
        d = ca[lang]
        w(f"| {lang} | {d['mem_reposo_mib']:.1f} | {d['mem_tras_cpu_mib']:.1f} | "
          f"{d['mem_bajo_carga_mib']:.1f} | {d['mem_tras_conc_mib']:.1f} |")
    w("")
    w(f"## 4 · Templado y el JIT ({INVOCACIONES:,} peticiones, n={N_CPU:,})".replace(",", "."))
    w("")
    w("| lenguaje | ext p50 | ext p99 | cómputo primeras 20 | cómputo últimas 500 |")
    w("|---|---|---|---|---|")
    for lang in ("python", "node"):
        d = ca[lang]
        w(f"| {lang} | {p(d['ext_ms'], .5):.2f} ms | {p(d['ext_ms'], .99):.2f} ms | "
          f"{statistics.median(d['int_ms'][:20]):.3f} ms | "
          f"{statistics.median(d['int_ms'][-500:]):.3f} ms |")
    w("")
    w(f"## 5 · Concurrencia: {CONCURRENTES} × {IO_MS} ms de espera")
    w("")
    w("| lenguaje | total | secuencial teórico |")
    w("|---|---|---|")
    for lang in ("python", "node"):
        w(f"| {lang} | {ca[lang]['conc_total_ms']:.0f} ms | "
          f"{CONCURRENTES * IO_MS:,} ms |".replace(",", "."))
    w("")
    destino = BASE / "SALIDA.md"
    destino.write_text("\n".join(li), encoding="utf-8")
    print("\n[ok] escrito", destino)
    (BASE / "_salida_cruda.json").write_text(json.dumps(SALIDA, indent=1), encoding="utf-8")


if __name__ == "__main__":
    construir()
    medir_imagenes()
    medir_arranque()
    medir_caliente()
    escribir_salida()
