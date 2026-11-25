# -*- coding: utf-8 -*-
"""¿Python o Node en Lambda? Arranque en frío medido con la IMAGEN OFICIAL de Lambda y su emulador (RIE), en local.

⚠️ NO es la nube real: el RIE no levanta una microVM Firecracker, no descarga tu código, no tiene la red de AWS ni
reparte CPU según la memoria. Los números sirven para comparar Python con Node en la misma máquina, no como cifra de AWS.

    python correr.py funcional   # sin cronómetro: misma respuesta, logs del RIE, tamaño de imagen
    python correr.py medir       # cronometrado: SOLO con el candado <proyecto>/_logs/banco.lock tomado

Imágenes: public.ecr.aws/lambda/python:3.14 y public.ecr.aws/lambda/nodejs:24 (cd-lambda-py:1 / cd-lambda-node:1).
Cada contenedor: --cpus 1 --memory 1g --rm.
"""
import json
import re
import statistics as st
import subprocess as sp
import sys
import time
import urllib.request

AQUI = __file__.rsplit("\\", 1)[0] if "\\" in __file__ else "."
IMG = {"python": "cd-lambda-py:1", "node": "cd-lambda-node:1"}
FNS = ["simple", "sdk"]
PUERTO = 19796
URL = f"http://127.0.0.1:{PUERTO}/2015-03-31/functions/function/invocations"
FRIOS = 15      # contenedores nuevos por variante
CALIENTES = 30  # invocaciones seguidas en el mismo contenedor


def sh(*a, check=True):
    return sp.run(list(a), capture_output=True, text=True, encoding="utf-8", check=check).stdout.strip()


def construir():
    sh("docker", "build", "-q", "-f", "Dockerfile.python", "-t", IMG["python"], ".")
    sh("docker", "build", "-q", "-f", "Dockerfile.node", "-t", IMG["node"], ".")


def invocar(timeout=10):
    req = urllib.request.Request(URL, data=b"{}", method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode()


def arrancar(lang, fn):
    nombre = f"cd796-{lang}-{fn}-{time.time_ns() % 10**8}"
    t0 = time.perf_counter()
    sh("docker", "run", "-d", "--rm", "--cpus", "1", "--memory", "1g", "--name", nombre,
       "-p", f"127.0.0.1:{PUERTO}:8080", IMG[lang], f"{fn}.handler")
    while True:  # el puerto acepta en cuanto el RIE escucha; la 1.ª invocación espera al INIT
        try:
            cuerpo = invocar()
            break
        except Exception:
            if time.perf_counter() - t0 > 30:
                sh("docker", "stop", "-t", "1", nombre, check=False)
                raise SystemExit(f"[X] {lang}/{fn} no respondió en 30 s")
            time.sleep(0.005)
    total_ms = (time.perf_counter() - t0) * 1000
    return nombre, cuerpo, total_ms


def reports(nombre):
    logs = sp.run(["docker", "logs", nombre], capture_output=True, text=True, encoding="utf-8").stdout
    logs += sp.run(["docker", "logs", nombre], capture_output=True, text=True, encoding="utf-8").stderr
    durs = [float(m) for m in re.findall(r"REPORT RequestId: \S+\s+(?:Init Duration: [\d.]+ ms\s+)?Duration: ([\d.]+) ms", logs)]
    init = [float(m) for m in re.findall(r"INIT REPORT\(durationMs: ([\d.]+)\)", logs)]
    return durs, logs, init


def memoria(nombre):
    s = sh("docker", "stats", "--no-stream", "--format", "{{.MemUsage}}", nombre)
    v, u = re.match(r"([\d.]+)\s*(\w+)", s).groups()
    return float(v) * {"MiB": 1, "GiB": 1024, "KiB": 1 / 1024}[u]


def parar(nombre):
    sh("docker", "stop", "-t", "1", nombre, check=False)


def funcional():
    construir()
    print("## Funcional (sin cronómetro)\n")
    print("```")
    for lang in IMG:
        print(f"$ docker image inspect {IMG[lang]} (base {'python:3.14' if lang == 'python' else 'nodejs:24'})")
        print(f"  contenido (comprimido): {int(sh('docker', 'image', 'inspect', '-f', '{{.Size}}', IMG[lang])) / 2**20:.1f} MiB")
        print(f"  en disco (docker images): {sh('docker', 'images', '--format', '{{.Size}}', IMG[lang])}")
    print("```\n")
    print("### ¿Llegan las dos al mismo estado? (misma respuesta, sin el campo lang)\n")
    resp = {}
    for fn in FNS:
        for lang in IMG:
            nombre, cuerpo, _ = arrancar(lang, fn)
            segunda = invocar()
            _, logs, _ = reports(nombre)
            parar(nombre)
            d = json.loads(cuerpo)
            resp[(lang, fn)] = {k: v for k, v in d.items() if k != "lang"}
            print(f"```\n$ curl -XPOST .../invocations -d '{{}}'   # {lang} · {fn} · 1.ª\n{cuerpo}\n"
                  f"$ (2.ª en el mismo contenedor)\n{segunda}\n```")
            if (lang, fn) == ("python", "simple"):
                print("\nLog del RIE de esa corrida (las líneas REPORT):\n```")
                for ln in logs.splitlines():
                    if "REPORT" in ln or "Version:" in ln:
                        print(ln.replace("\t", "  ").rstrip())
                print("```")
        if resp[("python", fn)] != resp[("node", fn)]:
            print(f"[X] {fn}: Python y Node NO devuelven lo mismo -> paro")
            sys.exit(1)
        print(f"\n✅ {fn}: Python y Node devuelven lo mismo: {resp[('python', fn)]}\n")


def medir():
    construir()
    print(f"## Medición ({time.strftime('%Y-%m-%d %H:%M')}) · {FRIOS} arranques en frío y {CALIENTES} en caliente por variante\n")
    print("Columnas: total = `docker run` → 1.ª respuesta (incluye Docker) · 1.ª Duration = lo que el RIE pone en el REPORT")
    print("de la 1.ª invocación (ahí dentro va el INIT, porque el RIE inicia en la 1.ª llamada) · caliente = invocaciones 2..N.\n")
    filas = []
    orden = [(l, f) for f in FNS for l in IMG]
    datos = {k: {"total": [], "init": [], "dur1": [], "cal_wall": [], "cal_dur": [], "mem": []} for k in orden}
    for ronda in range(FRIOS):  # intercalado: python, node, python, node... para que el ruido toque a los dos
        for lang, fn in orden:
            nombre, cuerpo, total = arrancar(lang, fn)
            assert json.loads(cuerpo)["invocacion"] == 1, cuerpo
            wall = []
            for _ in range(CALIENTES):
                t = time.perf_counter()
                invocar()
                wall.append((time.perf_counter() - t) * 1000)
            time.sleep(0.3)  # que el RIE escriba el último REPORT
            durs, _, init = reports(nombre)
            assert len(init) == 1, (lang, fn, init)
            datos[(lang, fn)]["mem"].append(memoria(nombre))
            parar(nombre)
            assert len(durs) == CALIENTES + 1, (lang, fn, len(durs))
            d = datos[(lang, fn)]
            d["total"].append(total)
            d["dur1"].append(durs[0])
            d["init"].append(init[0])
            d["cal_wall"].extend(wall)
            d["cal_dur"].extend(durs[1:])
        print(f"  ronda {ronda + 1}/{FRIOS} hecha", file=sys.stderr)
    print("| variante | total frío p50 (min-max) ms | INIT REPORT p50 ms | 1.ª Duration p50 ms | caliente Duration p50 ms | caliente ida y vuelta p50 ms | memoria contenedor MiB |")
    print("|---|---|---|---|---|---|---|")
    for lang, fn in orden:
        d = datos[(lang, fn)]
        filas.append((lang, fn, st.median(d["total"]), st.median(d["dur1"]), st.median(d["cal_dur"])))
        print(f"| {lang} · {fn} | {st.median(d['total']):.0f} ({min(d['total']):.0f}-{max(d['total']):.0f}) | "
              f"{st.median(d['init']):.1f} | {st.median(d['dur1']):.1f} | {st.median(d['cal_dur']):.2f} | {st.median(d['cal_wall']):.2f} | "
              f"{st.median(d['mem']):.1f} |")
    print("\nCrudos (total frío ms, en orden de ronda):")
    for k in orden:
        print(f"  {k[0]}·{k[1]}: " + " ".join(f"{x:.0f}" for x in datos[k]["total"]))
    print("Crudos (INIT REPORT ms):")
    for k in orden:
        print(f"  {k[0]}·{k[1]}: " + " ".join(f"{x:.1f}" for x in datos[k]["init"]))
    print("Crudos (1.ª Duration ms):")
    for k in orden:
        print(f"  {k[0]}·{k[1]}: " + " ".join(f"{x:.1f}" for x in datos[k]["dur1"]))


if __name__ == "__main__":
    import os
    os.chdir(AQUI)
    {"funcional": funcional, "medir": medir}[sys.argv[1]]()
