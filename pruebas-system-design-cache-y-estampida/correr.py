# -*- coding: utf-8 -*-
"""correr.py — banco del vídeo «System design: caché delante de la base de datos, y la estampida»
(cultura-devops, vídeo 346).

Postgres 17 + Valkey 9.1.2 en una red de Docker (10.77.22.0/24) y lab/ (Go: go-redis v9.23.0,
pgx v5.11.0, x/sync/singleflight). La consulta «cara» es una lectura por clave con pg_sleep(0.02):
20 ms siempre iguales, para que lo que se mida sea la caché y no la carga de la máquina. Se dice.

  1 sin caché · 2 cache-aside · 3 la lectura vieja · 4 la estampida (y sus arreglos)
  5 mil claves que expiran a la vez, sin y con jitter · 6 TTL corto y largo · 7 la caché se llena
  8 pedir lo que no existe (caché negativa) · 9 la caché se cae

    python correr.py      -> SALIDA.md
"""
import datetime
import os
import subprocess
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ENV = dict(os.environ, MSYS_NO_PATHCONV="1")
RED, SUBRED = "sd-cache", "10.77.22.0/24"
PG, VK, GO = "postgres:17-alpine", "valkey/valkey:9.1.2-alpine", "golang:1.27.2"
salida = []


def p(t=""):
    print(t, flush=True)
    salida.append(t)


def docker(*a, check=False):
    r = subprocess.run(["docker", *a], capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    if check and r.returncode:
        raise SystemExit(f"[X] docker {' '.join(a[:3])}: {r.stdout}{r.stderr}")
    return (r.stdout + r.stderr).strip()


def lab(*args, mostrar=None):
    p(f"$ lab {mostrar or ' '.join(args)}")
    o = docker("run", "--rm", "--network", RED, "-v", f"{(AQUI / 'lab').as_posix()}:/w:ro", "alpine:3.22",
               "/w/lab", *args)
    avisos = [l for l in o.splitlines() if l.startswith("redis:")]
    for l in o.splitlines():
        if not l.startswith("redis:"):
            p(l)
    if avisos:  # el log de go-redis repite la misma línea cientos de veces: se resume
        p(f"  ({len(avisos)} avisos de go-redis, como: {avisos[0].split('pool.go:770: ')[-1]})")


def limpiar():
    docker("rm", "-f", "sd-pg", "sd-valkey")
    docker("network", "rm", RED)


def main():
    docker("pull", "-q", VK)
    docker("run", "--rm", "-v", f"{(AQUI / 'lab').as_posix()}:/w", "-w", "/w", "-e", "CGO_ENABLED=0",
           "-v", "fab-go-mod:/go/pkg/mod", "-v", "fab-go-cache:/root/.cache/go-build", GO,
           "go", "build", "-o", "lab", ".", check=True)
    cab = ["# SALIDA — «System design: caché y estampida» (cultura-devops, vídeo 346)", "",
           "> Generado por `correr.py`. **No se escribe a mano.**", "",
           f"- fecha: `{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%SZ}`",
           f"- `{docker('run', '--rm', PG, 'postgres', '--version')}` · "
           f"`{docker('run', '--rm', VK, 'valkey-server', '--version').split(' sha=')[0]}`",
           "- la consulta a la BD lleva pg_sleep(0.02): 20 ms fijos, a propósito (en la estampida, 0.2: la "
           "clave caliente es cara de reconstruir). Una sola máquina."]
    limpiar()
    docker("network", "create", "--subnet", SUBRED, RED, check=True)
    try:
        docker("run", "-d", "--name", "sd-pg", "--network", RED, "-e", "POSTGRES_PASSWORD=lab",
               "-e", "POSTGRES_DB=tienda", PG, "-c", "max_connections=200", check=True)
        docker("run", "-d", "--name", "sd-valkey", "--network", RED, VK, check=True)
        for _ in range(60):
            if "accepting" in docker("exec", "sd-pg", "pg_isready", "-U", "postgres", "-d", "tienda"):
                break
            time.sleep(1)
        time.sleep(2)
        salida.append("\n```")
        lab("preparar")
        p("")
        p("== 1 · Sin caché: 2.000 lecturas, 20 a la vez, productos populares (Zipf) ==")
        lab("sincache", "-n", "2000")
        p("")
        p("== 2 · Cache-aside con Valkey (TTL 60 s) ==")
        lab("concache", "-n", "2000")
        p("")
        p("== 3 · La lectura vieja: actualizar la BD sin tocar la caché ==")
        lab("vieja")
        p("")
        p("== 4 · La estampida: expira la clave más pedida (200 ms reconstruirla) y llegan 100 peticiones a la vez ==")
        for m in ("nada", "instancias", "singleflight", "cerrojo"):
            lab("estampida", "-modo", m)
        p("")
        p("== 5 · 1.000 claves cargadas de golpe con TTL de 5 s, 50 lectores sin parar ==")
        lab("expiracion", mostrar="expiracion   # TTL 5 s exactos")
        lab("expiracion", "-jitter", mostrar="expiracion -jitter   # TTL entre 3,5 y 6,5 s")
        p("")
        p("== 6 · El TTL: más corto, dato más fresco y más consultas (20 lectores, 6 s) ==")
        for ttl in ("1s", "5s", "30s"):
            lab("ttl", "-ttl", ttl)
        p("")
        p("== 7 · La caché se llena: maxmemory = lo usado + 1 MB, allkeys-lru, productos de ~2 KB ==")
        lab("llena", "-n", "2000")
        p("")
        p("== 8 · Pedir algo que no existe ==")
        lab("inexistente")
        p("")
        p("== 9 · La caché se cae ==")
        docker("stop", "sd-valkey")
        p("$ docker stop sd-valkey")
        lab("caida", "-n", "400")
        salida.append("```")
    finally:
        limpiar()
    (AQUI / "SALIDA.md").write_bytes(("\n".join(cab) + "\n" + "\n".join(salida) + "\n").encode("utf-8"))
    print("\n[ok] SALIDA.md")


if __name__ == "__main__":
    main()
