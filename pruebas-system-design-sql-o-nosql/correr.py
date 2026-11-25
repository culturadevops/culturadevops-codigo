# -*- coding: utf-8 -*-
"""correr.py — banco del vídeo «System design: SQL o NoSQL, con el mismo caso» (cultura-devops, 352).

PostgreSQL 17 y MongoDB 8.0 en Docker, con los datos en tmpfs (la máquina renderiza vídeo a la vez y el disco
mete ruido). Las mediciones las hace lab.py dentro de la red (imagen sd-sql-cliente:1).

  1 cargar · 2 leer un pedido entero · 3 cambiar el esquema · 4 una consulta que cruza datos
  5 renombrar un producto copiado en los pedidos · 6 una transacción entre dos documentos · 7 JSONB

    python correr.py      -> SALIDA.md
"""
import datetime
import os
import subprocess
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ENV = dict(os.environ, MSYS_NO_PATHCONV="1")
RED, SUBRED = "sd-sql", "10.77.28.0/24"
PG, MONGO, CLIENTE = "postgres:17-alpine", "mongo:8.0.15", "sd-sql-cliente:1"
salida = []


def p(t=""):
    print(t, flush=True)
    salida.append(t)


def docker(*a, check=False):
    r = subprocess.run(["docker", *a], capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    if check and r.returncode:
        raise SystemExit(f"[X] docker {' '.join(a[:3])}: {r.stdout}{r.stderr}")
    return (r.stdout + r.stderr).strip()


def lab(*a):
    p(f"$ python lab.py {' '.join(a)}")
    for l in docker("run", "--rm", "--network", RED, "--cpu-shares", "8192", "-v", f"{AQUI.as_posix()}:/lab", "-w", "/lab", CLIENTE,
                    "python", "lab.py", *a).splitlines():
        p("  " + l.strip() if not l.startswith("    ") else l)


def mongo(rs=False):
    docker("rm", "-f", "mongo")
    extra = ["--replSet", "rs0"] if rs else []
    docker("run", "-d", "--name", "mongo", "--hostname", "mongo", "--network", RED, "--tmpfs", "/data/db",
           "--cpu-shares", "8192",
           MONGO, *extra, check=True)
    for _ in range(60):
        if "1" in docker("exec", "mongo", "mongosh", "--quiet", "--eval", "db.adminCommand('ping').ok"):
            break
        time.sleep(1)
    if rs:
        docker("exec", "mongo", "mongosh", "--quiet", "--eval",
               "rs.initiate({_id: 'rs0', members: [{_id: 0, host: 'mongo:27017'}]})")
        for _ in range(60):
            if "true" in docker("exec", "mongo", "mongosh", "--quiet", "--eval", "db.hello().isWritablePrimary"):
                break
            time.sleep(1)


def limpiar():
    docker("rm", "-f", "pg", "mongo")
    docker("network", "rm", RED)


def main():
    if not docker("images", "-q", CLIENTE):
        (AQUI / "_cliente").mkdir(exist_ok=True)
        (AQUI / "_cliente" / "Dockerfile").write_text(
            "FROM python:3.13-slim\nRUN pip install --no-cache-dir 'psycopg[binary]==3.2.3' pymongo==4.10.1\n", encoding="utf-8")
        docker("build", "-t", CLIENTE, str(AQUI / "_cliente"), check=True)
    limpiar()
    docker("network", "create", "--subnet", SUBRED, RED, check=True)
    try:
        docker("run", "-d", "--name", "pg", "--network", RED, "-e", "POSTGRES_PASSWORD=lab", "--shm-size", "512m",
               "--cpu-shares", "8192",
               "--tmpfs", "/var/lib/postgresql:size=4g", PG, "-c", "shared_buffers=512MB", check=True)
        for _ in range(240):
            if "init process complete" in docker("logs", "pg"):
                break
            time.sleep(0.5)
        for _ in range(60):
            if "ok" in docker("exec", "pg", "psql", "-U", "postgres", "-tAc", "SELECT 'ok'"):
                break
            time.sleep(0.5)
        mongo()
        cab = ["# SALIDA — «System design: SQL o NoSQL» (cultura-devops, vídeo 352)", "",
               "> Generado por `correr.py`. **No se escribe a mano.**", "",
               f"- fecha: `{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%SZ}`",
               f"- PostgreSQL {docker('exec', 'pg', 'psql', '-U', 'postgres', '-tAc', 'SHOW server_version')} · "
               f"MongoDB {docker('exec', 'mongo', 'mongosh', '--quiet', '--eval', 'db.version()')} · "
               "cliente Python 3.13 (psycopg 3.2.3, pymongo 4.10.1) dentro de la red",
               "- datos de las dos en tmpfs (memoria); una sola máquina, sin renders a la vez; los contenedores del "
               "banco van con prioridad de CPU (--cpu-shares 8192 frente a 1024)."]
        salida.append("\n```")
        p("== 1 · La misma tienda en las dos ==")
        lab("cargar")
        p("")
        p("== 2 · Leer un pedido entero ==")
        lab("leer")
        p("")
        p("== 3 · Cambiar el esquema: los pedidos ahora llevan moneda ==")
        lab("esquema")
        p("")
        p("== 4 · Una consulta que cruza datos: ventas por categoría ==")
        lab("cruzar")
        p("")
        p("== 5 · Cambiar el nombre de un producto ==")
        lab("renombrar")
        p("")
        p("== 6 · Una transacción entre dos documentos ==")
        lab("transaccion")
        p("  [MongoDB se reinicia como replica set de un nodo, se vuelve a cargar]")
        mongo(rs=True)
        docker("run", "--rm", "--network", RED, "--cpu-shares", "8192", "-v", f"{AQUI.as_posix()}:/lab", "-w", "/lab",
               CLIENTE, "python", "lab.py", "cargar")
        lab("transaccion", "rs")
        p("")
        p("== 7 · El término medio: JSONB en Postgres ==")
        lab("jsonb")
        salida.append("```")
    finally:
        limpiar()
    (AQUI / "SALIDA.md").write_bytes(("\n".join(cab) + "\n" + "\n".join(salida) + "\n").encode("utf-8"))
    print("\n[ok] SALIDA.md")


if __name__ == "__main__":
    main()
