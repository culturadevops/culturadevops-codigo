# SALIDA — «Concurrencia en Python medida» (cultura-devops, 772)

> Generado por `correr.py`. **No se escribe a mano.**

- fecha: `2026-11-04 23:15:19Z`
- imagen `cd-concurrencia-py:3.14.10` (Dockerfile): CPython 3.14.10 y 3.14.10 free-threaded de python-build-standalone, vía uv 0.13.7.
- cada contenedor con `--cpus 4 --memory 4g`; una sola máquina, los tiempos son de esta.
- cada repetición es un proceso nuevo; «mediana» = mediana de las repeticiones; el reloj incluye crear hilos/pool.

```
== 0 · Versiones y lo que ve Python del contenedor ==
$ python3.14 medir.py version
  sys.version            3.14.10 (main, Oct 26 2026, 14:09:22) [Clang 23.1.3 ]
  Py_GIL_DISABLED        0
  sys._is_gil_enabled()  True
  os.cpu_count()         24
  os.process_cpu_count() 24
  cgroup cpu.max         400000 100000
  multiprocessing        forkserver

$ python3.14t medir.py version
  sys.version            3.14.10 free-threading build (main, Oct 26 2026, 14:06:35) [Clang 23.1.3 ]
  Py_GIL_DISABLED        1
  sys._is_gil_enabled()  False
  os.cpu_count()         24
  os.process_cpu_count() 24
  cgroup cpu.max         400000 100000
  multiprocessing        forkserver

== 1 · Antes de medir: ¿todas las variantes calculan lo mismo? ==
$ python3.14 medir.py comprobar
  cpu     ✓ las 6 variantes dan 9439192
  espera  ✓ las 6 variantes dan 2470
  red     ✓ las 6 variantes dan 2470
$ python3.14t medir.py comprobar
  cpu     ✓ las 6 variantes dan 9439192
  espera  ✓ las 6 variantes dan 2470
  red     ✓ las 6 variantes dan 2470
  → misma suma en las 6 variantes y en los dos intérpretes

== 2 · Tarea de CPU (cálculo puro en Python) ==
$ python3.14 medir.py tiempos cpu --reps 5 --tareas 16 --tam 3000000 --trabajadores 4
  secuencial           mediana    0.913 s   × 1.0 vs secuencial   [0.918 0.910 0.912 0.913 0.915]
  threading            mediana    0.929 s   × 1.0 vs secuencial   [0.929 0.932 0.936 0.929 0.928]
  asyncio              mediana    0.917 s   × 1.0 vs secuencial   [0.912 0.913 0.962 0.917 0.930]
  multiprocessing      mediana    0.281 s   × 3.3 vs secuencial   [0.302 0.279 0.281 0.282 0.279]
  ThreadPoolExecutor   mediana    0.929 s   × 1.0 vs secuencial   [0.924 0.929 0.927 0.933 0.931]
  ProcessPoolExecutor  mediana    0.282 s   × 3.2 vs secuencial   [0.283 0.280 0.282 0.286 0.281]
                       misma suma en las 6: 8614191

$ python3.14t medir.py tiempos cpu --reps 5 --tareas 16 --tam 3000000 --trabajadores 4
  secuencial           mediana    1.042 s   × 1.0 vs secuencial   [1.042 1.038 1.038 1.042 1.045]
  threading            mediana    0.255 s   × 4.1 vs secuencial   [0.237 0.256 0.255 0.253 0.330]
  asyncio              mediana    1.042 s   × 1.0 vs secuencial   [1.040 1.042 1.042 1.042 1.041]
  multiprocessing      mediana    0.318 s   × 3.3 vs secuencial   [0.346 0.318 0.323 0.315 0.318]
  ThreadPoolExecutor   mediana    0.271 s   × 3.8 vs secuencial   [0.273 0.271 0.271 0.270 0.275]
  ProcessPoolExecutor  mediana    0.319 s   × 3.3 vs secuencial   [0.322 0.319 0.319 0.320 0.319]
                       misma suma en las 6: 8614191

== 3 · Tarea de E/S simulada (time.sleep / asyncio.sleep) ==
$ python3.14 medir.py tiempos espera --reps 5 --tareas 200 --ms 20 --trabajadores 50
  secuencial           mediana    4.028 s   × 1.0 vs secuencial   [4.027 4.028 4.027 4.028 4.028]
  threading            mediana    0.038 s   ×104.8 vs secuencial   [0.039 0.038 0.039 0.037 0.036]
  asyncio              mediana    0.021 s   ×187.7 vs secuencial   [0.022 0.021 0.021 0.022 0.021]
  multiprocessing      mediana    0.176 s   ×22.9 vs secuencial   [0.204 0.174 0.176 0.174 0.177]
  ThreadPoolExecutor   mediana    0.089 s   ×45.3 vs secuencial   [0.092 0.090 0.089 0.088 0.088]
  ProcessPoolExecutor  mediana    0.190 s   ×21.2 vs secuencial   [0.196 0.184 0.195 0.190 0.186]
                       misma suma en las 6: 2646700

$ python3.14t medir.py tiempos espera --reps 5 --tareas 200 --ms 20 --trabajadores 50
  secuencial           mediana    4.028 s   × 1.0 vs secuencial   [4.027 4.028 4.028 4.028 4.027]
  threading            mediana    0.050 s   ×80.6 vs secuencial   [0.053 0.049 0.050 0.050 0.050]
  asyncio              mediana    0.022 s   ×187.2 vs secuencial   [0.022 0.021 0.022 0.022 0.022]
  multiprocessing      mediana    0.187 s   ×21.5 vs secuencial   [0.209 0.187 0.187 0.185 0.189]
  ThreadPoolExecutor   mediana    0.093 s   ×43.4 vs secuencial   [0.094 0.092 0.093 0.093 0.093]
  ProcessPoolExecutor  mediana    0.193 s   ×20.8 vs secuencial   [0.205 0.193 0.199 0.190 0.186]
                       misma suma en las 6: 2646700

== 4 · Tarea de E/S de red (socket TCP a un servidor local que tarda) ==
$ python3.14 medir.py tiempos red --reps 5 --tareas 200 --ms 20 --trabajadores 50
  secuencial           mediana    4.138 s   × 1.0 vs secuencial   [4.144 4.138 4.138 4.138 4.136]
  threading            mediana    0.082 s   ×50.2 vs secuencial   [0.087 0.070 0.082 0.080 0.090]
  asyncio              mediana    0.032 s   ×129.3 vs secuencial   [0.032 0.032 0.032 0.032 0.032]
  multiprocessing      mediana    0.198 s   ×21.0 vs secuencial   [0.206 0.198 0.187 0.210 0.186]
  ThreadPoolExecutor   mediana    0.097 s   ×42.7 vs secuencial   [0.097 0.097 0.097 0.096 0.096]
  ProcessPoolExecutor  mediana    0.206 s   ×20.1 vs secuencial   [0.211 0.213 0.191 0.206 0.193]
                       misma suma en las 6: 2646700

$ python3.14t medir.py tiempos red --reps 5 --tareas 200 --ms 20 --trabajadores 50
  secuencial           mediana    4.139 s   × 1.0 vs secuencial   [4.145 4.140 4.136 4.138 4.139]
  threading            mediana    0.101 s   ×41.0 vs secuencial   [0.105 0.097 0.095 0.107 0.101]
  asyncio              mediana    0.032 s   ×130.7 vs secuencial   [0.031 0.032 0.032 0.033 0.032]
  multiprocessing      mediana    0.237 s   ×17.5 vs secuencial   [0.269 0.237 0.235 0.235 0.239]
  ThreadPoolExecutor   mediana    0.096 s   ×43.1 vs secuencial   [0.100 0.098 0.095 0.096 0.096]
  ProcessPoolExecutor  mediana    0.210 s   ×19.7 vs secuencial   [0.210 0.199 0.219 0.218 0.206]
                       misma suma en las 6: 2646700

== 5 · Coste: 10000 hilos contra 10000 tareas de asyncio ==
$ python3.14 medir.py coste --n 10000 --reps 5
  hilos    n=10000  crear=829.6ms  memoria=+207.0MB (21.20 KB cada una)  reservada=+92460MB  hilos_del_SO=10001
  asyncio  n=10000  crear=14.3ms  memoria=+10.5MB (1.08 KB cada una)  reservada=+10MB  hilos_del_SO=1

$ python3.14t medir.py coste --n 10000 --reps 5
  hilos    n=10000  crear=1781.0ms  memoria=+2273.4MB (232.80 KB cada una)  reservada=+443841MB  hilos_del_SO=10001
  asyncio  n=10000  crear=20.0ms  memoria=+11.4MB (1.17 KB cada una)  reservada=+0MB  hilos_del_SO=1

== 6 · La trampa: un contador sin lock, 4 hilos ==
$ python3.14 medir.py carrera --hilos 4 --vueltas 1000000 --reps 5
  sin lock  esperado=4000000  totales: 4000000 4000000 4000000 4000000 4000000  (mediana 0.056 s)
  con lock  esperado=4000000  totales: 4000000 4000000 4000000 4000000 4000000  (mediana 0.208 s)

$ python3.14t medir.py carrera --hilos 4 --vueltas 1000000 --reps 5
  sin lock  esperado=4000000  totales: 1258097 1217860 1179013 1138797 1177703  (mediana 0.137 s)
  con lock  esperado=4000000  totales: 4000000 4000000 4000000 4000000 4000000  (mediana 0.521 s)

== 7 · Tabla: mediana en segundos, 3.14 (con GIL) · 3.14t (sin GIL) ==
  cpu
    secuencial              0.913 ·    1.042
    threading               0.929 ·    0.255
    asyncio                 0.917 ·    1.042
    multiprocessing         0.281 ·    0.318
    ThreadPoolExecutor      0.929 ·    0.271
    ProcessPoolExecutor     0.282 ·    0.319
  espera
    secuencial              4.028 ·    4.028
    threading               0.038 ·    0.050
    asyncio                 0.021 ·    0.022
    multiprocessing         0.176 ·    0.187
    ThreadPoolExecutor      0.089 ·    0.093
    ProcessPoolExecutor     0.190 ·    0.193
  red
    secuencial              4.138 ·    4.139
    threading               0.082 ·    0.101
    asyncio                 0.032 ·    0.032
    multiprocessing         0.198 ·    0.237
    ThreadPoolExecutor      0.097 ·    0.096
    ProcessPoolExecutor     0.206 ·    0.210
```
