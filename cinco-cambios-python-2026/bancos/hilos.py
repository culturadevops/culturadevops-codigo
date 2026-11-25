# -*- coding: utf-8 -*-
"""715 · Trabajo de CPU repartido en hilos. Se ejecuta DENTRO del contenedor.

  python hilos.py primos 4      # cuenta primos hasta N con 4 hilos (Python puro)
  python hilos.py json 4        # parsea 400.000 líneas de log JSON con 4 hilos

Imprime una línea JSON: build, GIL activo o no, hilos, segundos y el resultado (debe ser igual en todos los lados).
"""
import json
import sys
import sysconfig
import time
from concurrent.futures import ThreadPoolExecutor

N_PRIMOS = 3_000_000
N_LINEAS = 400_000


def es_primo(n):
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def contar(rango):
    a, b = rango
    return sum(1 for n in range(a, b) if es_primo(n))


def lineas():
    est = (200, 200, 200, 404, 500, 301)
    return [json.dumps({"ts": 1761800000 + i, "ruta": f"/api/v1/item/{i % 977}", "estado": est[i % 6],
                        "ms": (i * 37) % 900, "ip": f"10.0.{i % 255}.{i % 7}"}) for i in range(N_LINEAS)]


def contar_500(trozo):
    return sum(1 for l in trozo if json.loads(l)["estado"] == 500)


def trozos(total, k):
    paso = total // k
    return [(i * paso, total if i == k - 1 else (i + 1) * paso) for i in range(k)]


def main():
    modo, hilos = sys.argv[1], int(sys.argv[2])
    if modo == "primos":
        partes, fn = trozos(N_PRIMOS, hilos * 4), contar
    else:
        datos = lineas()
        partes = [datos[a:b] for a, b in trozos(len(datos), hilos * 4)]
        fn = contar_500
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=hilos) as ex:
        res = sum(ex.map(fn, partes))
    seg = time.perf_counter() - t0
    gil = sys._is_gil_enabled() if hasattr(sys, "_is_gil_enabled") else True
    print(json.dumps({"python": sys.version.split()[0], "free_threading_build": bool(sysconfig.get_config_var("Py_GIL_DISABLED")),
                      "gil": gil, "modo": modo, "hilos": hilos, "seg": round(seg, 3), "resultado": res}))


if __name__ == "__main__":
    main()
