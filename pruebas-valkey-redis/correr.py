# -*- coding: utf-8 -*-
"""Valkey contra Redis — banco de pruebas del vídeo 279 (cultura-devops).

Todo en Docker y todo a SALIDA.md: lo que sale en el vídeo se copia de ahí.

    python correr.py              # todo
    python correr.py --sin-bench  # todo menos el benchmark (no necesita la máquina en reposo)

⚠️ El benchmark necesita la máquina EN REPOSO (nada renderizando): si no, los números no valen.
Mismo cliente (redis-benchmark de la imagen de Redis) contra los dos servidores, mismos límites
de CPU y memoria, un servidor cada vez, 3 pasadas y la mediana.
"""
import json
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RED = "vkbench"
VALKEY = "valkey/valkey:latest"
REDIS = "redis:latest"
PY = "python:3.12-slim"
LIM = ["--cpus=2", "--memory=1g"]
salida = []


def sh(cmd, check=False, timeout=900):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout)
    if check and r.returncode:
        raise SystemExit(f"falló: {' '.join(cmd)}\n{r.stdout}{r.stderr}")
    return (r.stdout + r.stderr).strip()


def anota(titulo, cmd_txt, texto):
    salida.extend(["", f"### {titulo}", "", f"`$ {cmd_txt}`", "", "```", texto.strip(), "```"])
    print(f"--- {titulo}\n{texto.strip()[:600]}\n", flush=True)


def servidor(nombre, imagen, *extra):
    sh(["docker", "rm", "-f", nombre])
    sh(["docker", "run", "-d", "--name", nombre, "--network", RED, *LIM, *extra, imagen,
        *(["valkey-server"] if "valkey" in imagen else ["redis-server"]),
        "--save", "", "--appendonly", "no"], check=True)
    for _ in range(50):
        if "PONG" in sh(["docker", "exec", nombre, "sh", "-c",
                         "valkey-cli ping 2>/dev/null || redis-cli ping"]):
            return
        time.sleep(0.2)
    raise SystemExit(f"{nombre} no arrancó")


def cli(servidor_host, *args):
    """redis-cli de la imagen de Redis contra cualquiera de los dos."""
    return sh(["docker", "run", "--rm", "--network", RED, REDIS, "redis-cli", "-h",
               servidor_host, *args])


def parar(*nombres):
    for n in nombres:
        sh(["docker", "rm", "-f", n])


def e1_versiones():
    salida.append("\n## 1 · Versiones")
    for nombre, img in (("valkey", VALKEY), ("redis", REDIS)):
        servidor(nombre, img)
        info = cli(nombre, "INFO", "server")
        lineas = [l for l in info.splitlines() if l.split(":")[0] in
                  ("redis_version", "valkey_version", "server_name", "redis_mode", "os",
                   "arch_bits", "multiplexing_api")]
        anota(f"INFO server · {nombre}", f"redis-cli -h {nombre} INFO server", "\n".join(lineas))
        anota(f"HELLO 3 · {nombre}", f"redis-cli -h {nombre} -3 HELLO 3",
              cli(nombre, "-3", "HELLO", "3"))
        parar(nombre)


def e2_bench():
    salida.append("\n## 2 · Benchmark (mismo cliente, mismos límites, 3 pasadas, mediana)")
    pruebas = [("pipeline 16", ["-t", "set,get", "-n", "10000000", "-c", "50", "-P", "16", "--threads", "2"]),
               ("sin pipeline", ["-t", "set,get", "-n", "1000000", "-c", "50", "--threads", "2"])]
    resumen = {}
    for nombre, img in (("valkey", VALKEY), ("redis", REDIS)):
        servidor(nombre, img)
        for etiqueta, args in pruebas:
            pasadas = {"SET": [], "GET": []}
            for i in range(3):
                txt = sh(["docker", "run", "--rm", "--network", RED, "--cpus=2", REDIS,
                          "redis-benchmark", "-h", nombre, "--csv", *args], timeout=1800)
                for l in txt.splitlines():
                    p = [x.strip('"') for x in l.split(",")]
                    if p and p[0] in pasadas:
                        pasadas[p[0]].append(float(p[1]))
                anota(f"{nombre} · {etiqueta} · pasada {i + 1}",
                      f"redis-benchmark -h {nombre} --csv {' '.join(args)}", txt)
            for op, v in pasadas.items():
                resumen[(nombre, etiqueta, op)] = statistics.median(v) if v else None
        parar(nombre)
    filas = ["prueba          op    valkey (req/s)   redis (req/s)   valkey/redis"]
    for etiqueta, _ in pruebas:
        for op in ("SET", "GET"):
            v, r = resumen[("valkey", etiqueta, op)], resumen[("redis", etiqueta, op)]
            filas.append(f"{etiqueta:<15} {op:<5} {v:>14,.0f} {r:>15,.0f}   {v / r:>10.2f}x")
    anota("resumen (medianas)", "calculado de las pasadas de arriba", "\n".join(filas))


def e3_clientes():
    salida.append("\n## 3 · Clientes de Redis contra Valkey")
    servidor("valkey", VALKEY)
    anota("redis-cli contra valkey", "redis-cli -h valkey SET/GET/INCR/EXPIRE/TTL",
          "\n".join([cli("valkey", "SET", "saludo", "hola"), cli("valkey", "GET", "saludo"),
                     cli("valkey", "INCR", "contador"), cli("valkey", "EXPIRE", "saludo", "60"),
                     cli("valkey", "TTL", "saludo")]))
    py = ("import redis, sys; r = redis.Redis(host='valkey'); "
          "print('redis-py', redis.__version__); r.set('k', 'v'); print('GET k =', r.get('k')); "
          "p = r.pipeline(); [p.incr('n') for _ in range(1000)]; print('1000 INCR en pipeline =', p.execute()[-1]); "
          "print('server:', {k: v for k, v in r.info('server').items() if 'version' in k or k == 'server_name'})")
    anota("redis-py contra valkey", "pip install redis && python -c ...",
          sh(["docker", "run", "--rm", "--network", RED, PY, "sh", "-c",
              f'pip install -q redis 2>/dev/null; python -c "{py}"'], timeout=600))
    parar("valkey")


def e4_migracion():
    salida.append("\n## 4 · Migrar datos (RDB y réplica)")
    vol = "vkdatos"
    for origen_img, destino_img, o, d in ((REDIS, VALKEY, "redis", "valkey"),
                                          (VALKEY, REDIS, "valkey", "redis")):
        sh(["docker", "volume", "rm", "-f", vol])
        sh(["docker", "rm", "-f", "origen"])
        sh(["docker", "run", "-d", "--name", "origen", "--network", RED, "-v", f"{vol}:/data",
            origen_img], check=True)
        time.sleep(1.5)
        sh(["docker", "run", "--rm", "--network", RED, PY, "sh", "-c",
            "pip install -q redis 2>/dev/null; python -c \"import redis; r=redis.Redis(host='origen'); "
            "p=r.pipeline(); [p.set(f'clave:{i}', 'x'*50) for i in range(100000)]; p.execute()\""],
           timeout=600)
        antes = cli("origen", "DBSIZE")
        cli("origen", "SAVE")
        firma = sh(["docker", "run", "--rm", "-v", f"{vol}:/data", "busybox", "head", "-c", "9",
                    "/data/dump.rdb"])
        sh(["docker", "rm", "-f", "origen"])
        sh(["docker", "rm", "-f", "destino"])
        sh(["docker", "run", "-d", "--name", "destino", "--network", RED, "-v", f"{vol}:/data",
            destino_img])
        time.sleep(2)
        despues = cli("destino", "DBSIZE")
        log = sh(["docker", "logs", "destino"])
        claves = [l for l in log.splitlines() if any(k in l.lower() for k in
                  ("rdb format", "signature", "fatal", "can't", "keys loaded", "done loading",
                   "db loaded"))]
        anota(f"RDB de {o} cargado en {d}",
              f"SAVE en {o} → arrancar {d} con el mismo /data → DBSIZE",
              f"primeros 9 bytes del dump.rdb de {o}: {firma}\n"
              f"DBSIZE en {o} antes: {antes}\nDBSIZE en {d} después: {despues}\n\nlog de {d}:\n"
              + "\n".join(claves[-12:]))
        sh(["docker", "rm", "-f", "destino"])
    sh(["docker", "volume", "rm", "-f", vol])

    # El punto del fork: Valkey nació de Redis 7.2.4. ¿Lee un RDB de Redis 7.2?
    sh(["docker", "volume", "rm", "-f", vol])
    sh(["docker", "run", "-d", "--name", "origen", "--network", RED, "-v", f"{vol}:/data",
        "redis:7.2"], check=True)
    time.sleep(1.5)
    sh(["docker", "run", "--rm", "--network", RED, PY, "sh", "-c",
        "pip install -q redis 2>/dev/null; python -c \"import redis; r=redis.Redis(host='origen'); "
        "p=r.pipeline(); [p.set(f'clave:{i}', 'x'*50) for i in range(100000)]; p.execute()\""],
       timeout=600)
    antes = cli("origen", "DBSIZE")
    ver = cli("origen", "INFO", "server").splitlines()
    ver = next((l for l in ver if l.startswith("redis_version")), "?")
    cli("origen", "SAVE")
    firma = sh(["docker", "run", "--rm", "-v", f"{vol}:/data", "busybox", "head", "-c", "9",
                "/data/dump.rdb"])
    sh(["docker", "rm", "-f", "origen"])
    sh(["docker", "run", "-d", "--name", "destino", "--network", RED, "-v", f"{vol}:/data", VALKEY])
    time.sleep(2)
    despues = cli("destino", "DBSIZE")
    anota("RDB de redis 7.2 cargado en valkey", "SAVE en redis:7.2 → arrancar valkey con el mismo /data",
          f"{ver}\nprimeros 9 bytes del dump.rdb: {firma}\nDBSIZE en redis 7.2: {antes}\n"
          f"DBSIZE en valkey después: {despues}")
    sh(["docker", "rm", "-f", "destino"])
    sh(["docker", "volume", "rm", "-f", vol])

    # Redis 8 → Valkey en caliente: DUMP/RESTORE y copia lógica
    servidor("redis", REDIS)
    servidor("valkey", VALKEY)
    copia = (
        "import redis, time; o=redis.Redis(host='redis'); d=redis.Redis(host='valkey'); "
        "p=o.pipeline(); [p.set(f'c:{i}', 'x'*50) for i in range(100000)]; p.execute(); "
        "o.set('una','hola'); "
        "\ntry:\n d.restore('una', 0, o.dump('una')); print('DUMP/RESTORE: OK')\n"
        "except Exception as e:\n print('DUMP/RESTORE:', type(e).__name__, e)\n"
        "t=time.perf_counter(); n=0\n"
        "cur=0\nwhile True:\n cur, ks = o.scan(cur, count=1000)\n"
        " if ks:\n  vs=o.mget(ks); q=d.pipeline(); [q.set(k,v) for k,v in zip(ks,vs) if v is not None]; q.execute(); n+=len(ks)\n"
        " if cur==0: break\n"
        "print(f'copia lógica SCAN+MGET+SET: {n} claves en {time.perf_counter()-t:.2f} s'); "
        "print('DBSIZE en valkey:', d.dbsize())")
    open(AQUI / "_copia.py", "w", encoding="utf-8").write(copia)
    anota("redis 8 → valkey en caliente", "python _copia.py   (DUMP/RESTORE y copia lógica)",
          sh(["docker", "run", "--rm", "--network", RED, "-v", f"{AQUI}:/w", PY, "sh", "-c",
              "pip install -q redis 2>/dev/null; python /w/_copia.py"], timeout=900))
    parar("redis", "valkey")

    # réplica: valkey como réplica de redis
    servidor("redis", REDIS)
    servidor("valkey", VALKEY)
    sh(["docker", "run", "--rm", "--network", RED, PY, "sh", "-c",
        "pip install -q redis 2>/dev/null; python -c \"import redis; r=redis.Redis(host='redis'); "
        "p=r.pipeline(); [p.set(f'rep:{i}', i) for i in range(10000)]; p.execute()\""], timeout=600)
    cli("valkey", "REPLICAOF", "redis", "6379")
    time.sleep(5)
    info = cli("valkey", "INFO", "replication")
    lin = [l for l in info.splitlines() if l.split(":")[0] in
           ("role", "master_host", "master_link_status", "master_sync_in_progress")]
    log = [l for l in sh(["docker", "logs", "valkey"]).splitlines()
           if any(k in l.lower() for k in ("master", "primary", "sync", "rdb", "error", "replica"))]
    anota("valkey como réplica de redis", "redis-cli -h valkey REPLICAOF redis 6379 ; INFO replication ; DBSIZE",
          "\n".join(lin) + f"\nDBSIZE en valkey: {cli('valkey', 'DBSIZE')}\n\nlog de valkey:\n"
          + "\n".join(log[-10:]))
    parar("redis", "valkey")


def e5_memoria():
    salida.append("\n## 5 · Memoria con los mismos datos (100.000 claves de 50 bytes)")
    filas = []
    for nombre, img in (("valkey", VALKEY), ("redis", REDIS)):
        servidor(nombre, img)
        vacia = cli(nombre, "INFO", "memory")
        sh(["docker", "run", "--rm", "--network", RED, PY, "sh", "-c",
            f"pip install -q redis 2>/dev/null; python -c \"import redis; r=redis.Redis(host='{nombre}'); "
            "p=r.pipeline(); [p.set(f'clave:{i}', 'x'*50) for i in range(100000)]; p.execute()\""],
           timeout=600)
        llena = cli(nombre, "INFO", "memory")
        g = lambda t, k: next((l.split(":")[1] for l in t.splitlines() if l.startswith(k + ":")), "?")
        u0, u1 = int(g(vacia, "used_memory")), int(g(llena, "used_memory"))
        filas.append(f"{nombre:<7} vacío {u0:>10,} B   con datos {u1:>11,} B   "
                     f"por clave {(u1 - u0) / 100000:>6.1f} B   ({g(llena, 'used_memory_human')})")
        parar(nombre)
    anota("used_memory", "INFO memory antes y después de 100.000 SET", "\n".join(filas))


def main():
    sin_bench = "--sin-bench" in sys.argv
    sh(["docker", "network", "create", RED])
    cab = ["# SALIDA — Valkey contra Redis", "",
           "Generado por `python correr.py`. **No se edita a mano.**", "",
           f"- fecha: {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC",
           f"- {sh(['docker', 'version', '--format', 'Docker {{.Server.Version}}'])}",
           f"- imágenes: {VALKEY} · {REDIS} · {PY}",
           f"- límites por contenedor: {' '.join(LIM)}"]
    try:
        e1_versiones()
        e3_clientes()
        e4_migracion()
        e5_memoria()
        if not sin_bench:
            e2_bench()
    finally:
        parar("valkey", "redis", "origen", "destino")
        sh(["docker", "network", "rm", RED])
    nombre = "SALIDA.md" if not sin_bench else "SALIDA-sin-bench.md"
    (AQUI / nombre).write_text("\n".join(cab + salida) + "\n", encoding="utf-8")
    print("escrito", nombre)


if __name__ == "__main__":
    main()
