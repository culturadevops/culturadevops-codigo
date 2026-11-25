# -*- coding: utf-8 -*-
"""carga.py — el cliente del banco del vídeo 396. Corre dentro de la red de Docker.

    python carga.py pedidos URL N                 crea N pedidos
    python carga.py subir URL N                   sube N ficheros de 4 KB (f0..fN-1)
    python carga.py bajar URL N VECES             pide cada fichero VECES veces: cuántos 404 y de qué réplica
    python carga.py golpe URL RUTA SEG CONC       carga sostenida: peticiones/s, mediana, p99 y errores
    python carga.py golpe-caida URL RUTA SEG CONC MATAR_A   igual, y a MATAR_A s escribe /lab/datos/matar
    python carga.py tiempos URL N                 N peticiones seguidas: el tiempo de cada una
"""
import os
import random
import statistics
import sys
import threading
import time
from collections import Counter

import requests


def golpe(url, ruta, seg, conc, matar_a=None):
    fin = time.time() + seg
    t0 = time.time()
    ts, err, por_seg, rep = [], Counter(), Counter(), {}
    lock = threading.Lock()

    def obrero():
        s = requests.Session()
        while time.time() < fin:
            a = time.perf_counter()
            try:
                r = s.get(url + ruta, timeout=10)
                ok = r.status_code == 200
                quien = r.headers.get("X-Replica")
                motivo = str(r.status_code)
            except Exception as e:  # noqa: BLE001
                ok, motivo = False, type(e).__name__
            ms = (time.perf_counter() - a) * 1000
            with lock:
                if ok:
                    ts.append(ms)
                    seg_ = int(time.time() - t0)
                    por_seg[seg_] += 1
                    rep.setdefault(quien, Counter())[seg_] += 1
                else:
                    err[motivo] += 1

    hilos = [threading.Thread(target=obrero) for _ in range(conc)]
    for h in hilos:
        h.start()
    if matar_a is not None:
        time.sleep(matar_a)
        open("/lab/datos/matar", "w").write("1")
    for h in hilos:
        h.join()
    ts.sort()
    print(f"  {len(ts)} respuestas en {seg} s → {len(ts) / seg:.0f} por segundo · mediana {statistics.median(ts):.1f} ms"
          f" · p99 {ts[int(len(ts) * 0.99)]:.1f} ms · errores {sum(err.values())}"
          + (f" ({dict(err)})" if err else ""))
    if matar_a is not None:
        print("  por segundo:      " + " ".join(f"{por_seg[i]:>4}" for i in range(seg)))
        for q in sorted(rep):
            print(f"  de ellas, {q}: " + " ".join(f"{rep[q][i]:>4}" for i in range(seg)))


def main():
    modo, url = sys.argv[1], sys.argv[2]
    s = requests.Session()
    if modo == "pedidos":
        for _ in range(int(sys.argv[3])):
            s.post(url + "/pedido").raise_for_status()
        print(f"  {sys.argv[3]} pedidos creados")
    elif modo == "subir":
        donde = Counter()
        for i in range(int(sys.argv[3])):
            r = s.post(f"{url}/subir/f{i}", data=os.urandom(4096))
            r.raise_for_status()
            donde[r.headers.get("X-Replica")] += 1
        print(f"  {sys.argv[3]} ficheros subidos · " + " · ".join(f"{k}: {v}" for k, v in sorted(donde.items())))
    elif modo == "bajar":
        n, veces = int(sys.argv[3]), int(sys.argv[4])
        c = Counter()
        rnd = random.Random(7)
        for _ in range(veces):
            orden = list(range(n))
            rnd.shuffle(orden)            # los usuarios no piden en el orden en que se subió
            for i in orden:
                r = s.get(f"{url}/archivo/f{i}")
                c[(r.status_code, r.headers.get("X-Replica"))] += 1
        total = n * veces
        malos = sum(v for (code, _), v in c.items() if code != 200)
        print(f"  {total} descargas · 200: {total - malos} · 404: {malos} ({100 * malos / total:.0f} %)")
        print("  " + " · ".join(f"{code} desde {rep}: {v}" for (code, rep), v in sorted(c.items())))
    elif modo == "golpe":
        golpe(url, sys.argv[3], int(sys.argv[4]), int(sys.argv[5]))
    elif modo == "golpe-caida":
        golpe(url, sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]))
    elif modo == "tiempos":
        out = []
        for i in range(int(sys.argv[3])):
            a = time.perf_counter()
            r = s.get(url)
            out.append(f"{(time.perf_counter() - a) * 1000:.0f} ms" + (" (HIT)" if r.headers.get("X-Cache") == "HIT"
                                                                           else " (MISS)" if r.headers.get("X-Cache") else ""))
        print("  " + " · ".join(out))


if __name__ == "__main__":
    main()
