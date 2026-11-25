# -*- coding: utf-8 -*-
"""Una corrida de una variante. Imprime una línea JSON: segundos, resultado (suma de todas las tareas) y si el GIL estaba activo.

    python3.14  banco.py cpu    threading            --tareas 16  --tam 2000000 --trabajadores 4
    python3.14t banco.py espera asyncio              --tareas 200 --ms 20
    python3.14  banco.py red    ProcessPoolExecutor  --tareas 200 --puerto 9000 --trabajadores 50

El reloj (time.perf_counter) incluye crear los hilos, el bucle o el pool: es lo que paga tu programa de verdad.
"""
import argparse
import asyncio
import concurrent.futures as cf
import json
import multiprocessing as mp
import sys
import threading
import time

import tareas

VARIANTES = ["secuencial", "threading", "asyncio", "multiprocessing", "ThreadPoolExecutor", "ProcessPoolExecutor"]


def secuencial(fn, afn, args, w):
    return [fn(*a) for a in args]


def hilos(fn, afn, args, w):
    # Un hilo por tarea, a mano, como se escribe con threading.
    res = [None] * len(args)

    def uno(k, a):
        res[k] = fn(*a)

    ts = [threading.Thread(target=uno, args=(k, a)) for k, a in enumerate(args)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    return res


def con_asyncio(fn, afn, args, w):
    async def main():
        return await asyncio.gather(*(afn(*a) for a in args))
    return asyncio.run(main())


def con_multiprocessing(fn, afn, args, w):
    with mp.Pool(w) as p:
        return p.starmap(fn, args)


def pool_hilos(fn, afn, args, w):
    with cf.ThreadPoolExecutor(max_workers=w) as ex:
        return list(ex.map(fn, *zip(*args)))


def pool_procesos(fn, afn, args, w):
    with cf.ProcessPoolExecutor(max_workers=w) as ex:
        return list(ex.map(fn, *zip(*args)))


CORRER = {"secuencial": secuencial, "threading": hilos, "asyncio": con_asyncio, "multiprocessing": con_multiprocessing,
          "ThreadPoolExecutor": pool_hilos, "ProcessPoolExecutor": pool_procesos}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tipo", choices=["cpu", "espera", "red"])
    ap.add_argument("variante", choices=VARIANTES)
    ap.add_argument("--tareas", type=int, default=16)
    ap.add_argument("--tam", type=int, default=2_000_000, help="vueltas por tarea de CPU")
    ap.add_argument("--ms", type=float, default=20, help="espera por tarea de E/S simulada")
    ap.add_argument("--puerto", type=int, default=9000)
    ap.add_argument("--trabajadores", type=int, default=4)
    a = ap.parse_args()

    if a.tipo == "cpu":
        fn, afn, args = tareas.cpu, tareas.cpu_async, [(k, a.tam) for k in range(a.tareas)]
    elif a.tipo == "espera":
        fn, afn, args = tareas.espera, tareas.espera_async, [(k, a.ms) for k in range(a.tareas)]
    else:
        fn, afn, args = tareas.red, tareas.red_async, [(k, a.puerto) for k in range(a.tareas)]

    t0 = time.perf_counter()
    res = CORRER[a.variante](fn, afn, args, a.trabajadores)
    s = time.perf_counter() - t0
    print(json.dumps({"tipo": a.tipo, "variante": a.variante, "s": s, "resultado": sum(res), "n": len(res),
                      "gil": sys._is_gil_enabled()}))


if __name__ == "__main__":
    main()
