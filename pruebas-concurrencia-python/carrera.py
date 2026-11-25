# -*- coding: utf-8 -*-
"""La trampa: un contador compartido sin lock.

    python3.14t carrera.py sin  4 1000000
    python3.14t carrera.py lock 4 1000000

H hilos suman V veces cada uno a la misma variable global. Debería dar H*V.
`contador += 1` son varias operaciones (leer, sumar, guardar); si otro hilo guarda entre medias, una suma se pierde.
Que con GIL salga bien NO es una garantía del lenguaje: es un detalle de cuándo CPython suelta el GIL.
"""
import json
import sys
import threading
import time

contador = 0
candado = threading.Lock()


def sin_lock(v):
    global contador
    for _ in range(v):
        contador += 1


def con_lock(v):
    global contador
    for _ in range(v):
        with candado:
            contador += 1


def main():
    modo, h, v = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    fn = sin_lock if modo == "sin" else con_lock
    ts = [threading.Thread(target=fn, args=(v,)) for _ in range(h)]
    t0 = time.perf_counter()
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    s = time.perf_counter() - t0
    print(json.dumps({"modo": modo, "total": contador, "esperado": h * v, "perdidas": h * v - contador, "s": s,
                      "gil": sys._is_gil_enabled()}))


if __name__ == "__main__":
    main()
