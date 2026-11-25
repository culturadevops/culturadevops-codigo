# -*- coding: utf-8 -*-
"""correr.py — banco del vídeo «System design: replicación» (cultura-devops, vídeo 351).

PostgreSQL 17 con réplicas en streaming, en Docker. Este script arranca, mata y promueve los
contenedores; las mediciones las hace lab.py dentro de la red (imagen curso-sd-cliente:1).
La réplica r1 va limitada a un cuarto de CPU, como una réplica pequeña o ocupada: así su retraso
se ve en una sola máquina. Se dice en el vídeo.

    python correr.py      -> SALIDA.md
"""
import datetime
import os
import subprocess
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ENV = dict(os.environ, MSYS_NO_PATHCONV="1")
PG = "postgres:17-alpine"
CLIENTE = "curso-sd-cliente:1"
RED = "sd-repl"
SUBRED = "10.77.20.0/24"
salida = []


def p(t=""):
    print(t)
    salida.append(t)


def titulo(t):
    p("")
    p(f"== {t} ==")


def run(args, check=False):
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    if check and r.returncode:
        raise SystemExit(f"[X] {' '.join(args[:4])}: {r.stdout}{r.stderr}")
    return r.returncode, (r.stdout + r.stderr).strip()


def docker(*a, check=False):
    return run(["docker", *a], check=check)


def lab(*a):
    c, o = docker("run", "--rm", "--network", RED, "-v", f"{AQUI.as_posix()}:/lab", CLIENTE, "python", "lab.py", *a)
    for l in o.splitlines():
        p(l)
    if c:
        p(f"  [X] lab.py {a[0]} terminó con código {c}")
    return c


def limpiar():
    docker("rm", "-f", "sd-primario", "sd-replica1", "sd-replica2")
    docker("network", "rm", RED)


def primario(sync=""):
    args = ["-c", "wal_level=replica", "-c", "max_wal_senders=10", "-c", "max_replication_slots=10"]
    if sync:
        args += ["-c", f"synchronous_standby_names={sync}"]
    docker("run", "-d", "--name", "sd-primario", "--hostname", "sd-primario", "--network", RED,
           "-e", "POSTGRES_PASSWORD=lab", "-e", "POSTGRES_DB=tienda",
           "-v", f"{(AQUI / 'init' / 'replicacion.sh').as_posix()}:/docker-entrypoint-initdb.d/replicacion.sh:ro",
           PG, *args, check=True)
    for _ in range(120):
        c, _ = docker("exec", "sd-primario", "psql", "-U", "postgres", "-d", "tienda", "-tAc",
                      "SELECT count(*) FROM pg_roles WHERE rolname = 'replicador'")
        if c == 0:
            break
        time.sleep(0.5)
    time.sleep(2)  # el entrypoint reinicia Postgres tras los scripts de init


def replica(n, cpus="0.25"):
    nombre = f"sd-replica{n}"
    docker("run", "-d", "--name", nombre, "--hostname", nombre, "--network", RED, f"--cpus={cpus}",
           "-e", f"NOMBRE=r{n}", "-e", "POSTGRES_PASSWORD=lab",
           "-v", f"{(AQUI / 'init' / 'arranque-replica.sh').as_posix()}:/arranque.sh:ro",
           "--entrypoint", "sh", PG, "/arranque.sh", check=True)
    for _ in range(120):
        c, o = docker("exec", "sd-primario", "psql", "-U", "postgres", "-tAc",
                      f"SELECT state FROM pg_stat_replication WHERE application_name = 'r{n}'")
        if o.strip() == "streaming":
            return
        time.sleep(0.5)
    raise SystemExit(f"[X] la réplica r{n} no llega a streaming")


def montar(sync="", replicas=(1,)):
    """La síncrona se activa DESPUÉS de conectar las réplicas: si se pone al arrancar, los commits de
    la inicialización esperan a una réplica que aún no existe y el primario se queda colgado."""
    limpiar()
    docker("network", "create", "--subnet", SUBRED, RED, check=True)
    primario()
    for n in replicas:
        replica(n)
    if sync:
        docker("exec", "sd-primario", "psql", "-U", "postgres", "-c",
               f"ALTER SYSTEM SET synchronous_standby_names = '{sync}'", check=True)
        docker("exec", "sd-primario", "psql", "-U", "postgres", "-c", "SELECT pg_reload_conf()", check=True)
        time.sleep(1)
        _, o = docker("exec", "sd-primario", "psql", "-U", "postgres", "-tAc",
                      "SELECT application_name || ' ' || sync_state FROM pg_stat_replication ORDER BY 1")
        p(f"  synchronous_standby_names = '{sync}' -> " + ", ".join(o.split("\n")))


def failover(etiqueta):
    """Commits sin parar + carga de fondo; a los 4 s se mata el primario y se promueve r1."""
    fichero = "/lab/_acks.txt"
    escritor = subprocess.Popen(["docker", "run", "--rm", "--network", RED, "-v", f"{AQUI.as_posix()}:/lab",
                                 CLIENTE, "python", "lab.py", "acks", "30", fichero],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", env=ENV)
    fondo = subprocess.Popen(["docker", "run", "--rm", "--network", RED, "-v", f"{AQUI.as_posix()}:/lab",
                              CLIENTE, "python", "-c",
                              "import lab, time; lab.carga(30)"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=ENV)
    # Esperar a que el escritor lleve 100 commits confirmados (no un tiempo fijo: con la máquina cargada,
    # su contenedor tardó más en arrancar y la versión con «sleep 2» midió 0 commits en la síncrona).
    acks = AQUI / "_acks.txt"
    for _ in range(600):
        if acks.exists() and sum(1 for _ in acks.open()) >= 100:
            break
        time.sleep(0.05)
    # La réplica se queda atrás: se congela 2 s (docker pause), como un corte de red. Sin esto, en una
    # sola máquina recibe el WAL casi al instante y no se ve la pérdida (primera medición: 0 perdidos).
    docker("pause", "sd-replica1")
    p(f"$ docker pause sd-replica1   ({etiqueta}: con 100 commits confirmados, la réplica deja de recibir, como un corte de red)")
    time.sleep(2)
    docker("kill", "sd-primario")
    docker("unpause", "sd-replica1")
    p("$ docker kill sd-primario    (2 s después, con escrituras en marcha) · docker unpause sd-replica1")
    out, _ = escritor.communicate(timeout=120)
    fondo.wait(timeout=120)
    for l in out.strip().splitlines():
        p(l)
    c, o = docker("exec", "sd-replica1", "gosu", "postgres", "psql", "-U", "postgres", "-tAc", "SELECT pg_promote()")
    p(f"$ SELECT pg_promote();   -> {o.strip()}")
    lab("perdidos", fichero, "sd-replica1")
    (AQUI / "_acks.txt").unlink(missing_ok=True)


def disco_libre_gb():
    import shutil
    return shutil.disk_usage("C:\\").free / 1024 ** 3


def main():
    # Freno: la primera versión de este banco escribió 1,2 GB de WAL en un momento en que el disco
    # estaba justo, y Docker Desktop se cayó (2026-10-08). Si no hay holgura, no se arranca.
    libre = disco_libre_gb()
    if libre < 30:
        raise SystemExit(f"[X] solo {libre:.0f} GB libres en C:; el banco necesita 30. No arranco.")
    docker("pull", "-q", PG)
    _, v = docker("run", "--rm", PG, "postgres", "--version")
    _, dv = docker("version", "--format", "{{.Server.Version}}")
    cab = ["# SALIDA — «System design: replicación» (cultura-devops, vídeo 351)", "",
           "> Generado por `correr.py`. **No se escribe a mano.**", "",
           f"- fecha: `{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%SZ}`",
           f"- `{v.strip()}` · Docker `{dv.strip()}`",
           "- la réplica r1 va limitada a 0,25 CPU (`--cpus=0.25`) para que su retraso se vea en una sola máquina"]
    fallos = 0
    try:
        salida.append("\n```")
        montar()
        titulo("1 · Un primario y una réplica en streaming, asíncrona (lo que viene por defecto)")
        fallos += lab("retraso")

        titulo("2 · Leer de la réplica justo después de escribir en el primario")
        fallos += lab("leer", "500")

        titulo("3 · Failover con replicación asíncrona: se cae el primario y se promueve la réplica")
        failover("asíncrona")

        titulo("4 · Failover con replicación síncrona (synchronous_standby_names = 'r1')")
        montar(sync="r1")
        failover("síncrona")

        titulo("5 · Lo que cuesta la síncrona: latencia de cada commit")
        montar(sync="r1")
        fallos += lab("latencias", "300")

        titulo("6 · La otra cara: la réplica síncrona se cae")
        docker("stop", "sd-replica1")
        p("$ docker stop sd-replica1")
        fallos += lab("colgado", "8")

        titulo("7 · Lo correcto: dos réplicas y ANY 1 (basta con que confirme una)")
        montar(sync="ANY 1 (r1, r2)", replicas=(1, 2))
        docker("stop", "sd-replica1")
        p("$ docker stop sd-replica1   (synchronous_standby_names = 'ANY 1 (r1, r2)')")
        fallos += lab("colgado", "5")
        salida.append("```")
    finally:
        limpiar()
    (AQUI / "SALIDA.md").write_bytes(("\n".join(cab) + "\n" + "\n".join(salida) + "\n").encode("utf-8"))
    print(f"\n[{'ok' if not fallos else 'X'}] SALIDA.md · {fallos} fallos")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
