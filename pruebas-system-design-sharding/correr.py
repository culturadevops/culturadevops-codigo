# -*- coding: utf-8 -*-
"""correr.py — banco del vídeo «System design: sharding, partir una base de datos en varias»
(cultura-devops, vídeo 347).

Sharding a mano: cuatro Postgres 17 (s0..s3) y uno con todo (mono), en una red de Docker
(10.77.23.0/24). lab/ (Go, pgx v5.11.0) hace de router. Un millón de pedidos de 10.000 clientes;
el cliente 777 hace el 20 %. Tres claves de reparto: hash por cliente, rango por cliente y hash por
pedido. Todo en una máquina: los tiempos son de esta.

    python correr.py      -> SALIDA.md
"""
import datetime
import os
import subprocess
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ENV = dict(os.environ, MSYS_NO_PATHCONV="1")
RED, SUBRED = "sd-shard", "10.77.23.0/24"
PG, GO = "postgres:17-alpine", "golang:1.27.2"
BASES = ["s0", "s1", "s2", "s3", "mono"]
salida = []


def p(t=""):
    print(t, flush=True)
    salida.append(t)


def docker(*a, check=False):
    r = subprocess.run(["docker", *a], capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    if check and r.returncode:
        raise SystemExit(f"[X] docker {' '.join(a[:3])}: {r.stdout}{r.stderr}")
    return (r.stdout + r.stderr).strip()


def lab(orden):
    p(f"$ lab {orden}")
    o = docker("run", "--rm", "--network", RED, "-v", f"{(AQUI / 'lab').as_posix()}:/w:ro", "alpine:3.22",
               "/w/lab", orden)
    for l in o.splitlines():
        p(l)


def limpiar():
    docker("rm", "-f", *BASES)
    docker("network", "rm", RED)


def main():
    docker("run", "--rm", "-v", f"{(AQUI / 'lab').as_posix()}:/w", "-w", "/w", "-e", "CGO_ENABLED=0",
           "-v", "fab-go-mod:/go/pkg/mod", "-v", "fab-go-cache:/root/.cache/go-build", GO,
           "go", "build", "-o", "lab", ".", check=True)
    cab = ["# SALIDA — «System design: sharding» (cultura-devops, vídeo 347)", "",
           "> Generado por `correr.py`. **No se escribe a mano.**", "",
           f"- fecha: `{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%SZ}`",
           f"- `{docker('run', '--rm', PG, 'postgres', '--version')}` × 5 (4 shards + 1 monolito)",
           "- 1.000.000 de pedidos, 10.000 clientes; el cliente 777 hace el 20 %. Una sola máquina."]
    limpiar()
    docker("network", "create", "--subnet", SUBRED, RED, check=True)
    try:
        for b in BASES:
            docker("run", "-d", "--name", b, "--network", RED, "-e", "POSTGRES_PASSWORD=lab",
                   "-e", "POSTGRES_DB=tienda", PG, check=True)
        for b in BASES:
            for _ in range(60):
                if "accepting" in docker("exec", b, "pg_isready", "-U", "postgres", "-d", "tienda"):
                    break
                time.sleep(1)
        time.sleep(3)
        salida.append("\n```")
        p("== 0 · Cargar los mismos pedidos de tres formas ==")
        lab("cargar")
        p("")
        p("== 1 · Cómo se reparten las filas entre los 4 shards ==")
        lab("reparto")
        p("")
        p("== 2 · Una consulta que va a un shard, y una que va a todos ==")
        lab("consultas")
        p("")
        p("== 3 · Los 5 clientes que más gastan: ¿sale bien sumando shard a shard? ==")
        lab("top")
        p("")
        p("== 3b · El cliente grande, un pedido por su número y un email repetido ==")
        lab("extra")
        p("")
        p("== 4 · Añadir un quinto shard: cuántas filas cambian de sitio ==")
        lab("mover")
        salida.append("```")
    finally:
        limpiar()
    (AQUI / "SALIDA.md").write_bytes(("\n".join(cab) + "\n" + "\n".join(salida) + "\n").encode("utf-8"))
    print("\n[ok] SALIDA.md")


if __name__ == "__main__":
    main()
