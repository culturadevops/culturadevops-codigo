# -*- coding: utf-8 -*-
"""Cuánto cuesta tener N cosas esperando a la vez: N hilos de threading contra N tareas de asyncio.

    python3.14 coste.py hilos 10000
    python3.14 coste.py asyncio 10000

Mide desde que empieza a crearlas hasta que TODAS están vivas y esperando (los hilos en un Event, las tareas en un
asyncio.Event). La memoria sale de /proc/self/status: VmRSS (lo que ocupa de verdad) y VmSize (lo que reserva),
antes y después. Threads = hilos que ve el sistema operativo en el proceso.
"""
import asyncio
import json
import sys
import threading
import time


def estado():
    d = {}
    with open("/proc/self/status") as f:
        for l in f:
            k, _, v = l.partition(":")
            if k in ("VmRSS", "VmSize", "Threads"):
                d[k] = int(v.split()[0])
    return d


def con_hilos(n):
    listo = threading.Event()
    antes = estado()
    t0 = time.perf_counter()
    ts = [threading.Thread(target=listo.wait) for _ in range(n)]
    for t in ts:
        t.start()  # start() vuelve cuando el hilo ya arrancó
    s = time.perf_counter() - t0
    despues = estado()
    listo.set()
    for t in ts:
        t.join()
    return s, antes, despues


def con_asyncio(n):
    async def main():
        listo = asyncio.Event()
        vivas = 0

        async def una():
            nonlocal vivas
            vivas += 1
            await listo.wait()

        antes = estado()
        t0 = time.perf_counter()
        ts = [asyncio.create_task(una()) for _ in range(n)]
        while vivas < n:
            await asyncio.sleep(0)  # deja que todas lleguen a esperar
        s = time.perf_counter() - t0
        despues = estado()
        listo.set()
        await asyncio.gather(*ts)
        return s, antes, despues
    return asyncio.run(main())


def main():
    modo, n = sys.argv[1], int(sys.argv[2])
    s, a, d = (con_hilos if modo == "hilos" else con_asyncio)(n)
    rss = (d["VmRSS"] - a["VmRSS"]) / 1024
    vm = (d["VmSize"] - a["VmSize"]) / 1024
    print(json.dumps({"modo": modo, "n": n, "s": s, "rss_mb": rss, "kb_cada": rss * 1024 / n, "virtual_mb": vm,
                      "hilos_so": d["Threads"], "gil": sys._is_gil_enabled()}))


if __name__ == "__main__":
    main()
