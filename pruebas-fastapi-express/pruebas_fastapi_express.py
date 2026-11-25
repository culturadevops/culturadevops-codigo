# -*- coding: utf-8 -*-
"""pruebas_fastapi_express.py — la revancha con frameworks del vídeo 152. Vídeo 156.

Mismos ejes que investigacion/pruebas_python_node.py (mismo contrato /suma y /espera),
contendientes: FastAPI+uvicorn contra Express 5. Salida literal en
`recursos/pruebas-fastapi-express/SALIDA.md`.

    python canales/cultura-devops/investigacion/pruebas_fastapi_express.py
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
BASE = Path(__file__).resolve().parent.parent / "recursos" / "pruebas-fastapi-express"

N_CPU = 200_000
REPES_FRIO = 8
INVOCACIONES = 2_000
CONCURRENTES = 300
IO_MS = 100

LENGUAJES = [
    ("fastapi", "cdo-revancha-fastapi:1", 9601),
    ("express", "cdo-revancha-express:1", 9602),
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


def esperar_ok(puerto, timeout=90):
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
    for _ in range(80):
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
    print("0 · construir")
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
    for _, imagen, _ in LENGUAJES:
        rr = sh(["docker", "image", "inspect", imagen, "--format", "{{.Size}}"])
        filas[imagen] = {"descarga": int(rr.stdout.strip()), "disco": en_disco.get(imagen, "?")}
        print(f"    · {imagen:26s} descarga {mib(filas[imagen]['descarga']):>11s} "
              f"disco {filas[imagen]['disco']}")
    SALIDA["imagenes"] = filas


def medir_arranque():
    print("2 · arranque")
    filas = {}
    for lang, imagen, puerto in LENGUAJES:
        externos, internos = [], []
        for i in range(REPES_FRIO):
            nombre = f"revancha-{lang}-frio-{i}"
            parar(nombre)
            t0 = time.perf_counter()
            sh(["docker", "run", "-d", "--name", nombre, "-p", f"{puerto}:8080", imagen])
            t1 = esperar_ok(puerto)
            externos.append((t1 - t0) * 1000)
            li = listo_interno(nombre)
            if li is not None:
                internos.append(li)
            parar(nombre)
        filas[lang] = {"externo_ms": externos, "interno_ms": internos}
        print(f"    · {lang:8s} 1ª respuesta mediana {statistics.median(externos):.0f} ms · "
              f"proceso listo {statistics.median(internos):.1f} ms")
    SALIDA["arranque"] = filas


def medir_caliente():
    print("3-5 · memoria, templado y concurrencia")
    filas = {}
    for lang, imagen, puerto in LENGUAJES:
        nombre = f"revancha-{lang}-caliente"
        parar(nombre)
        sh(["docker", "run", "-d", "--name", nombre, "-p", f"{puerto}:8080", imagen])
        esperar_ok(puerto)
        time.sleep(2)
        mem_reposo = memoria_mib(nombre)
        print(f"    · {lang:8s} memoria en reposo {mem_reposo:.1f} MiB")

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
        print(f"      {CONCURRENTES} a la vez × {IO_MS} ms → total {total_conc:.0f} ms")
        parar(nombre)
        filas[lang] = {"mem_reposo_mib": mem_reposo, "mem_tras_cpu_mib": mem_tras_cpu,
                       "ext_ms": externos, "int_ms": internos,
                       "conc_total_ms": total_conc, "mem_bajo_carga_mib": mem_bajo_carga}
    SALIDA["caliente"] = filas


def escribir_salida():
    li = []
    w = li.append
    w("# SALIDA — FastAPI contra Express, medidos en esta máquina (la revancha del 152)")
    w("")
    w(f"> Corrida del {time.strftime('%Y-%m-%d %H:%M')}. Regenerable con")
    w("> `python investigacion/pruebas_fastapi_express.py`. ⛔ Ninguna cifra de blog.")
    w("> FastAPI 0.116.1 + uvicorn 0.35.0 sobre python:3.13-slim · Express 5.1.0 sobre")
    w("> node:22-slim. Referencias del 152 (stdlib): python p50 21,07 · node p50 2,12 ·")
    w("> bucle 8,40 / 1,18 ms · reposo 14,7 / 9,8 MiB.")
    w("")
    w("## 1 · Imágenes (con las dependencias del framework)")
    w("")
    w("| imagen | descarga | en disco |")
    w("|---|---|---|")
    for ref, d in SALIDA["imagenes"].items():
        w(f"| `{ref}` | {mib(d['descarga'])} | {d['disco']} |")
    w("")
    ar = SALIDA["arranque"]
    w(f"## 2 · Arranque (mediana de {REPES_FRIO})")
    w("")
    w("| framework | 1ª respuesta (docker incluido) | proceso «listo» |")
    w("|---|---|---|")
    for lang in ("fastapi", "express"):
        e = statistics.median(ar[lang]["externo_ms"])
        i = statistics.median(ar[lang]["interno_ms"])
        w(f"| {lang} | {e:.0f} ms | {i:.1f} ms |")
    w("")
    ca = SALIDA["caliente"]
    w("## 3 · Memoria (MiB)")
    w("")
    w("| framework | reposo | tras 2.000 de CPU | bajo 300 concurrentes |")
    w("|---|---|---|---|")
    for lang in ("fastapi", "express"):
        d = ca[lang]
        w(f"| {lang} | {d['mem_reposo_mib']:.1f} | {d['mem_tras_cpu_mib']:.1f} | "
          f"{d['mem_bajo_carga_mib']:.1f} |")
    w("")
    w(f"## 4 · Templado ({INVOCACIONES:,} peticiones, n={N_CPU:,})".replace(",", "."))
    w("")
    w("| framework | ext p50 | ext p99 | cómputo primeras 20 | cómputo últimas 500 |")
    w("|---|---|---|---|---|")
    for lang in ("fastapi", "express"):
        d = ca[lang]
        w(f"| {lang} | {p(d['ext_ms'], .5):.2f} ms | {p(d['ext_ms'], .99):.2f} ms | "
          f"{statistics.median(d['int_ms'][:20]):.3f} ms | "
          f"{statistics.median(d['int_ms'][-500:]):.3f} ms |")
    w("")
    w(f"## 5 · Concurrencia: {CONCURRENTES} × {IO_MS} ms de espera")
    w("")
    w("| framework | total |")
    w("|---|---|")
    for lang in ("fastapi", "express"):
        w(f"| {lang} | {ca[lang]['conc_total_ms']:.0f} ms |")
    w("")
    (BASE / "SALIDA.md").write_text("\n".join(li), encoding="utf-8")
    (BASE / "_salida_cruda.json").write_text(json.dumps(SALIDA, indent=1), encoding="utf-8")
    print("\n[ok] escrito", BASE / "SALIDA.md")


if __name__ == "__main__":
    construir()
    medir_imagenes()
    medir_arranque()
    medir_caliente()
    escribir_salida()
