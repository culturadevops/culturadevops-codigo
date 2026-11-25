# -*- coding: utf-8 -*-
"""correr.py — banco del vídeo 772 «Concurrencia en Python medida: hilos, asyncio, procesos y el GIL» (cultura-devops).

Construye la imagen (Dockerfile: CPython 3.14.10 normal y free-threaded, los dos de python-build-standalone vía uv 0.13.7)
y corre todo en contenedores con CPU y memoria fijas. Deja la salida LITERAL en SALIDA.md y los datos en _salida_cruda.json.

    python correr.py            -> SALIDA.md            (5 repeticiones, tamaños del vídeo)
    python correr.py --humo     -> _humo.md             (1 repetición, datos mínimos: solo comprueba que todo funciona;
                                                          sus tiempos NO valen para el vídeo)

Paradas (no compara si los dos lados no están en el mismo estado):
  · los dos intérpretes tienen que ser la misma versión;
  · python3.14 con GIL (Py_GIL_DISABLED=0) y python3.14t sin GIL (Py_GIL_DISABLED=1, sys._is_gil_enabled() False);
  · las 6 variantes tienen que dar la misma suma, y la misma en los dos intérpretes;
  · cada corrida medida comprueba de nuevo resultado y GIL (medir.py para con código 2).
⚠️ No lo lances con otro banco corriendo en la máquina: los dos se contaminan.
"""
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ENV = dict(os.environ, MSYS_NO_PATHCONV="1")
IMG = "cd-concurrencia-py:3.14.10"
CPUS, MEM = "4", "4g"
PYS = ("python3.14", "python3.14t")
HUMO = "--humo" in sys.argv

salida, crudo = [], []


def p(t=""):
    print(t, flush=True)
    salida.append(t)


def docker(py, *args, mostrar=True):
    linea = f"{py} medir.py {' '.join(args)}"
    if mostrar:
        p(f"$ {linea}")
    r = subprocess.run(["docker", "run", "--rm", "--cpus", CPUS, "--memory", MEM, IMG, py, "medir.py", *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    datos = []
    for l in (r.stdout + r.stderr).splitlines():
        if l.startswith("@@"):
            d = json.loads(l[2:])
            d["py"] = py
            datos.append(d)
            crudo.append(d)
        elif l.strip():
            p("  " + l)
    if r.returncode:
        p(f"  [código de salida {r.returncode}]")
        fin()
        sys.exit(f"[PARO] {linea} falló; mira la salida")
    return datos


def fin():
    nombre = "_humo.md" if HUMO else "SALIDA.md"
    cab = [f"# {'HUMO (no vale para el vídeo)' if HUMO else 'SALIDA'} — «Concurrencia en Python medida» (cultura-devops, 772)", "",
           "> Generado por `correr.py`. **No se escribe a mano.**", "",
           f"- fecha: `{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%SZ}`",
           f"- imagen `{IMG}` (Dockerfile): CPython 3.14.10 y 3.14.10 free-threaded de python-build-standalone, vía uv 0.13.7.",
           f"- cada contenedor con `--cpus {CPUS} --memory {MEM}`; una sola máquina, los tiempos son de esta.",
           "- cada repetición es un proceso nuevo; «mediana» = mediana de las repeticiones; el reloj incluye crear hilos/pool."]
    (AQUI / nombre).write_bytes(("\n".join(cab) + "\n\n```\n" + "\n".join(salida) + "\n```\n").encode("utf-8"))
    if not HUMO:
        (AQUI / "_salida_cruda.json").write_text(json.dumps(crudo, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\n[ok] {nombre}")


def main():
    r = subprocess.run(["docker", "build", "-q", "-t", IMG, str(AQUI)], capture_output=True, text=True, env=ENV)
    if r.returncode:
        sys.exit(r.stdout + r.stderr)

    if HUMO:
        cpu = ["--tareas", "8", "--tam", "20000", "--trabajadores", "4"]
        io = ["--tareas", "20", "--ms", "5", "--trabajadores", "10"]
        reps, n_coste, vueltas = "1", "200", "20000"
    else:
        cpu = ["--tareas", "16", "--tam", "3000000", "--trabajadores", "4"]
        io = ["--tareas", "200", "--ms", "20", "--trabajadores", "50"]
        reps, n_coste, vueltas = "5", "10000", "1000000"

    p("== 0 · Versiones y lo que ve Python del contenedor ==")
    v = {}
    for py in PYS:
        v[py] = docker(py, "version")[0]
        p("")
    if v["python3.14"]["version"] != v["python3.14t"]["version"]:
        sys.exit("[PARO] los dos intérpretes no son la misma versión")
    if not (v["python3.14"]["gil"] and not v["python3.14"]["gil_build"]):
        sys.exit("[PARO] python3.14 debería tener el GIL")
    if v["python3.14t"]["gil"] or v["python3.14t"]["gil_build"] != 1:
        sys.exit("[PARO] python3.14t debería correr SIN GIL")

    p("== 1 · Antes de medir: ¿todas las variantes calculan lo mismo? ==")
    comp = {py: docker(py, "comprobar") for py in PYS}
    for a, b in zip(comp["python3.14"], comp["python3.14t"]):
        if a["res"] != b["res"]:
            sys.exit(f"[PARO] {a['tipo']}: 3.14 y 3.14t no dan lo mismo")
    p("  → misma suma en las 6 variantes y en los dos intérpretes")
    p("")

    for n, (tipo, titulo, args) in enumerate([("cpu", "Tarea de CPU (cálculo puro en Python)", cpu),
                                              ("espera", "Tarea de E/S simulada (time.sleep / asyncio.sleep)", io),
                                              ("red", "Tarea de E/S de red (socket TCP a un servidor local que tarda)", io)], 2):
        p(f"== {n} · {titulo} ==")
        for py in PYS:
            docker(py, "tiempos", tipo, "--reps", reps, *args)
            p("")

    p(f"== 5 · Coste: {n_coste} hilos contra {n_coste} tareas de asyncio ==")
    for py in PYS:
        docker(py, "coste", "--n", n_coste, "--reps", reps)
        p("")

    p("== 6 · La trampa: un contador sin lock, 4 hilos ==")
    for py in PYS:
        docker(py, "carrera", "--hilos", "4", "--vueltas", vueltas, "--reps", reps)
        p("")

    p("== 7 · Tabla: mediana en segundos, 3.14 (con GIL) · 3.14t (sin GIL) ==")
    t = {(d["py"], d["tipo"], d["variante"]): d["mediana"] for d in crudo if d["que"] == "tiempos"}
    for tipo in ("cpu", "espera", "red"):
        p(f"  {tipo}")
        for var in ("secuencial", "threading", "asyncio", "multiprocessing", "ThreadPoolExecutor", "ProcessPoolExecutor"):
            a, b = t[("python3.14", tipo, var)], t[("python3.14t", tipo, var)]
            p(f"    {var:20} {a:8.3f} · {b:8.3f}")
    fin()


if __name__ == "__main__":
    main()
