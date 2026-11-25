# -*- coding: utf-8 -*-
"""Corre dentro del contenedor con el intérprete que se quiere medir (python3.14 o python3.14t).
Cada repetición es un proceso nuevo (`sys.executable banco.py ...`), así ninguna hereda calor ni memoria de la anterior.

    python3.14 medir.py version
    python3.14 medir.py comprobar --tam 20000 --tareas-io 20
    python3.14 medir.py tiempos cpu    --reps 5 --tareas 16 --tam 3000000 --trabajadores 4
    python3.14 medir.py tiempos espera --reps 5 --tareas 200 --ms 20 --trabajadores 50
    python3.14 medir.py tiempos red    --reps 5 --tareas 200 --ms 20 --trabajadores 50
    python3.14 medir.py coste   --n 10000 --reps 5
    python3.14 medir.py carrera --hilos 4 --vueltas 1000000 --reps 5

Las líneas que empiezan por «@@» son JSON para correr.py; el resto es la salida que se lee.
Si una corrida no da el mismo resultado que las demás, o si el GIL no está como debe, para con código 2.
"""
import argparse
import json
import os
import statistics
import subprocess
import sys

from banco import VARIANTES

AQUI = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
GIL = sys._is_gil_enabled()


def emitir(d):
    print("@@" + json.dumps(d), flush=True)


def correr(script, *args):
    r = subprocess.run([PY, os.path.join(AQUI, script), *map(str, args)], capture_output=True, text=True)
    if r.returncode:
        print(r.stdout + r.stderr)
        sys.exit(f"[FALLO] {script} {' '.join(map(str, args))} salió con {r.returncode}")
    if r.stderr.strip():
        print("  [stderr] " + r.stderr.strip().replace("\n", "\n  [stderr] "))
    d = json.loads(r.stdout.strip().splitlines()[-1])
    if d["gil"] != GIL:
        sys.exit(f"[PARO] el GIL cambió dentro de {script}: esperaba {GIL}, salió {d['gil']}")
    return d


class Servidor:
    """El servidor de la prueba de red: un proceso aparte, con el mismo intérprete, en 127.0.0.1."""

    def __init__(self, puerto, ms):
        self.p = subprocess.Popen([PY, os.path.join(AQUI, "tareas.py"), str(puerto), str(ms)], stdout=subprocess.PIPE, text=True)
        if self.p.stdout.readline().strip() != "escuchando":
            sys.exit("[FALLO] el servidor de red no arrancó")

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.p.kill()
        self.p.wait()


def args_tipo(tipo, a):
    if tipo == "cpu":
        return ["--tareas", a.tareas, "--tam", a.tam, "--trabajadores", a.trabajadores]
    if tipo == "espera":
        return ["--tareas", a.tareas, "--ms", a.ms, "--trabajadores", a.trabajadores]
    return ["--tareas", a.tareas, "--puerto", a.puerto, "--trabajadores", a.trabajadores]


def version(a):
    import multiprocessing as mp
    import sysconfig
    print(f"sys.version            {sys.version}")
    print(f"Py_GIL_DISABLED        {sysconfig.get_config_var('Py_GIL_DISABLED')}")
    print(f"sys._is_gil_enabled()  {GIL}")
    print(f"os.cpu_count()         {os.cpu_count()}")
    print(f"os.process_cpu_count() {os.process_cpu_count()}")
    try:
        cpumax = open("/sys/fs/cgroup/cpu.max").read().strip()
    except OSError:
        cpumax = "?"
    print(f"cgroup cpu.max         {cpumax}")
    print(f"multiprocessing        {mp.get_start_method()}")
    emitir({"que": "version", "version": sys.version.split()[0], "gil_build": sysconfig.get_config_var("Py_GIL_DISABLED"),
            "gil": GIL, "cpu_count": os.cpu_count(), "process_cpu_count": os.process_cpu_count(), "cpu_max": cpumax,
            "start_method": mp.get_start_method()})


def comprobar(a):
    """Cada variante, una vez, con datos pequeños: todas tienen que dar la misma suma."""
    ok = True
    for tipo in ("cpu", "espera", "red"):
        a2 = argparse.Namespace(tareas=a.tareas_io if tipo != "cpu" else 16, tam=a.tam, ms=a.ms, puerto=a.puerto, trabajadores=4)
        res = {}
        if tipo == "red":
            srv = Servidor(a.puerto, a.ms)
        try:
            for v in VARIANTES:
                res[v] = correr("banco.py", tipo, v, *args_tipo(tipo, a2))["resultado"]
        finally:
            if tipo == "red":
                srv.__exit__()
        iguales = len(set(res.values())) == 1
        ok &= iguales
        print(f"{tipo:6}  {'✓ las 6 variantes dan' if iguales else '✗ NO coinciden:'} {res[VARIANTES[0]] if iguales else res}")
        emitir({"que": "comprobar", "tipo": tipo, "res": res})
    if not ok:
        sys.exit(2)


def tiempos(a):
    srv = Servidor(a.puerto, a.ms) if a.tipo == "red" else None
    try:
        ref = None
        base = None
        for v in VARIANTES:
            ds = [correr("banco.py", a.tipo, v, *args_tipo(a.tipo, a)) for _ in range(a.reps)]
            rs = {d["resultado"] for d in ds}
            if ref is None:
                ref = ds[0]["resultado"]
            if rs != {ref}:
                sys.exit(f"[PARO] {v} no da el mismo resultado: {rs} (esperado {ref})")
            ss = [d["s"] for d in ds]
            med = statistics.median(ss)
            base = base or med
            print(f"{v:20} mediana {med:8.3f} s   ×{base / med:4.1f} vs secuencial   [{' '.join(f'{s:.3f}' for s in ss)}]")
            emitir({"que": "tiempos", "tipo": a.tipo, "variante": v, "mediana": med, "reps": ss, "resultado": ref})
        print(f"{'':20} misma suma en las 6: {ref}")
    finally:
        if srv:
            srv.__exit__()


def coste(a):
    for modo in ("hilos", "asyncio"):
        ds = sorted((correr("coste.py", modo, a.n) for _ in range(a.reps)), key=lambda d: d["s"])
        d = ds[len(ds) // 2]  # la corrida mediana (por tiempo), entera
        print(f"{modo:8} n={d['n']}  crear={d['s'] * 1000:.1f}ms  memoria=+{d['rss_mb']:.1f}MB ({d['kb_cada']:.2f} KB cada una)"
              f"  reservada=+{d['virtual_mb']:.0f}MB  hilos_del_SO={d['hilos_so']}")
        emitir({"que": "coste", **d, "todas_s": [x["s"] for x in ds]})


def carrera(a):
    for modo in ("sin", "lock"):
        ds = [correr("carrera.py", modo, a.hilos, a.vueltas) for _ in range(a.reps)]
        med = statistics.median(d["s"] for d in ds)
        totales = " ".join(str(d["total"]) for d in ds)
        print(f"{'sin lock' if modo == 'sin' else 'con lock'}  esperado={ds[0]['esperado']}  totales: {totales}  (mediana {med:.3f} s)")
        emitir({"que": "carrera", "modo": modo, "totales": [d["total"] for d in ds], "esperado": ds[0]["esperado"], "mediana": med})


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="que", required=True)
    sp.add_parser("version")
    c = sp.add_parser("comprobar")
    c.add_argument("--tam", type=int, default=20000)
    c.add_argument("--tareas-io", type=int, default=20)
    c.add_argument("--ms", type=float, default=5)
    c.add_argument("--puerto", type=int, default=9000)
    t = sp.add_parser("tiempos")
    t.add_argument("tipo", choices=["cpu", "espera", "red"])
    t.add_argument("--reps", type=int, default=5)
    t.add_argument("--tareas", type=int, default=16)
    t.add_argument("--tam", type=int, default=3_000_000)
    t.add_argument("--ms", type=float, default=20)
    t.add_argument("--puerto", type=int, default=9000)
    t.add_argument("--trabajadores", type=int, default=4)
    k = sp.add_parser("coste")
    k.add_argument("--n", type=int, default=10000)
    k.add_argument("--reps", type=int, default=5)
    r = sp.add_parser("carrera")
    r.add_argument("--hilos", type=int, default=4)
    r.add_argument("--vueltas", type=int, default=1_000_000)
    r.add_argument("--reps", type=int, default=5)
    a = ap.parse_args()
    {"version": version, "comprobar": comprobar, "tiempos": tiempos, "coste": coste, "carrera": carrera}[a.que](a)


if __name__ == "__main__":
    main()
