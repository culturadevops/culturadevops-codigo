# HUMO (no vale para el vídeo) — «Concurrencia en Python medida» (cultura-devops, 772)

> Generado por `correr.py`. **No se escribe a mano.**

- fecha: `2026-11-04 21:51:12Z`
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
$ python3.14 medir.py tiempos cpu --reps 1 --tareas 8 --tam 20000 --trabajadores 4
  secuencial           mediana    0.003 s   × 1.0 vs secuencial   [0.003]
  threading            mediana    0.004 s   × 0.8 vs secuencial   [0.004]
  asyncio              mediana    0.003 s   × 1.0 vs secuencial   [0.003]
  multiprocessing      mediana    0.076 s   × 0.0 vs secuencial   [0.076]
  ThreadPoolExecutor   mediana    0.005 s   × 0.6 vs secuencial   [0.005]
  ProcessPoolExecutor  mediana    0.060 s   × 0.1 vs secuencial   [0.060]
                       misma suma en las 6: 5383693

$ python3.14t medir.py tiempos cpu --reps 1 --tareas 8 --tam 20000 --trabajadores 4
  secuencial           mediana    0.004 s   × 1.0 vs secuencial   [0.004]
  threading            mediana    0.002 s   × 1.5 vs secuencial   [0.002]
  asyncio              mediana    0.004 s   × 1.0 vs secuencial   [0.004]
  multiprocessing      mediana    0.092 s   × 0.0 vs secuencial   [0.092]
  ThreadPoolExecutor   mediana    0.004 s   × 0.9 vs secuencial   [0.004]
  ProcessPoolExecutor  mediana    0.069 s   × 0.1 vs secuencial   [0.069]
                       misma suma en las 6: 5383693

== 3 · Tarea de E/S simulada (time.sleep / asyncio.sleep) ==
$ python3.14 medir.py tiempos espera --reps 1 --tareas 20 --ms 5 --trabajadores 10
  secuencial           mediana    0.102 s   × 1.0 vs secuencial   [0.102]
  threading            mediana    0.007 s   ×14.1 vs secuencial   [0.007]
  asyncio              mediana    0.006 s   ×18.5 vs secuencial   [0.006]
  multiprocessing      mediana    0.087 s   × 1.2 vs secuencial   [0.087]
  ThreadPoolExecutor   mediana    0.014 s   × 7.1 vs secuencial   [0.014]
  ProcessPoolExecutor  mediana    0.071 s   × 1.4 vs secuencial   [0.071]
                       misma suma en las 6: 2470

$ python3.14t medir.py tiempos espera --reps 1 --tareas 20 --ms 5 --trabajadores 10
  secuencial           mediana    0.102 s   × 1.0 vs secuencial   [0.102]
  threading            mediana    0.010 s   ×10.5 vs secuencial   [0.010]
  asyncio              mediana    0.006 s   ×18.4 vs secuencial   [0.006]
  multiprocessing      mediana    0.113 s   × 0.9 vs secuencial   [0.113]
  ThreadPoolExecutor   mediana    0.014 s   × 7.1 vs secuencial   [0.014]
  ProcessPoolExecutor  mediana    0.080 s   × 1.3 vs secuencial   [0.080]
                       misma suma en las 6: 2470

== 4 · Tarea de E/S de red (socket TCP a un servidor local que tarda) ==
$ python3.14 medir.py tiempos red --reps 1 --tareas 20 --ms 5 --trabajadores 10
  secuencial           mediana    0.114 s   × 1.0 vs secuencial   [0.114]
  threading            mediana    0.011 s   ×10.3 vs secuencial   [0.011]
  asyncio              mediana    0.007 s   ×15.4 vs secuencial   [0.007]
  multiprocessing      mediana    0.091 s   × 1.3 vs secuencial   [0.091]
  ThreadPoolExecutor   mediana    0.016 s   × 7.2 vs secuencial   [0.016]
  ProcessPoolExecutor  mediana    0.072 s   × 1.6 vs secuencial   [0.072]
                       misma suma en las 6: 2470

$ python3.14t medir.py tiempos red --reps 1 --tareas 20 --ms 5 --trabajadores 10
  secuencial           mediana    0.114 s   × 1.0 vs secuencial   [0.114]
  threading            mediana    0.011 s   ×10.7 vs secuencial   [0.011]
  asyncio              mediana    0.007 s   ×16.7 vs secuencial   [0.007]
  multiprocessing      mediana    0.102 s   × 1.1 vs secuencial   [0.102]
  ThreadPoolExecutor   mediana    0.018 s   × 6.5 vs secuencial   [0.018]
  ProcessPoolExecutor  mediana    0.090 s   × 1.3 vs secuencial   [0.090]
                       misma suma en las 6: 2470

== 5 · Coste: 200 hilos contra 200 tareas de asyncio ==
$ python3.14 medir.py coste --n 200 --reps 1
  hilos    n=200  crear=25.6ms  memoria=+4.8MB (24.34 KB cada una)  reservada=+13828MB  hilos_del_SO=201
  asyncio  n=200  crear=0.4ms  memoria=+0.4MB (2.16 KB cada una)  reservada=+0MB  hilos_del_SO=1

$ python3.14t medir.py coste --n 200 --reps 1
  hilos    n=200  crear=39.5ms  memoria=+46.6MB (238.82 KB cada una)  reservada=+19976MB  hilos_del_SO=201
  asyncio  n=200  crear=2.1ms  memoria=+0.4MB (2.06 KB cada una)  reservada=+0MB  hilos_del_SO=1

== 6 · La trampa: un contador sin lock, 4 hilos ==
$ python3.14 medir.py carrera --hilos 4 --vueltas 20000 --reps 1
  sin  lock  esperado=80000  totales: 80000  (mediana 0.002 s)
  lock lock  esperado=80000  totales: 80000  (mediana 0.005 s)

$ python3.14t medir.py carrera --hilos 4 --vueltas 20000 --reps 1
  sin  lock  esperado=80000  totales: 43977  (mediana 0.003 s)
  lock lock  esperado=80000  totales: 80000  (mediana 0.010 s)

== 7 · Tabla: mediana en segundos, 3.14 (con GIL) · 3.14t (sin GIL) ==
  cpu
    secuencial              0.003 ·    0.004
    threading               0.004 ·    0.002
    asyncio                 0.003 ·    0.004
    multiprocessing         0.076 ·    0.092
    ThreadPoolExecutor      0.005 ·    0.004
    ProcessPoolExecutor     0.060 ·    0.069
  espera
    secuencial              0.102 ·    0.102
    threading               0.007 ·    0.010
    asyncio                 0.006 ·    0.006
    multiprocessing         0.087 ·    0.113
    ThreadPoolExecutor      0.014 ·    0.014
    ProcessPoolExecutor     0.071 ·    0.080
  red
    secuencial              0.114 ·    0.114
    threading               0.011 ·    0.011
    asyncio                 0.007 ·    0.007
    multiprocessing         0.091 ·    0.102
    ThreadPoolExecutor      0.016 ·    0.018
    ProcessPoolExecutor     0.072 ·    0.090
```
