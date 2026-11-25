# -*- coding: utf-8 -*-
"""Banco extra del vídeo 414: lo que pierdes entre una copia y el desastre (lo que en las empresas se llama RPO).
  · 10.000 pedidos; copia; entran 25 pedidos más; el disco se muere; restaurar: faltan esos 25.
    python correr_extra.py   -> SALIDA-extra.md
"""
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
OUT = []
IMG = "postgres:17-alpine"


def run(args):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (p.stdout + p.stderr).strip(), p.returncode


def sh(c, cmd):
    return run(["docker", "exec", c, "sh", "-c", cmd])


def bloque(titulo, mostrado, res, nota=None):
    s, rc = res
    OUT.append(f"### {titulo}\n\n`$ {mostrado}`\n\n```\n{s}\n```\n(código de salida {rc})\n" + (f"\n> {nota}\n" if nota else ""))
    print(f"[{rc}] {titulo}")


def listo(c):
    for _ in range(60):
        s, rc = sh(c, "pg_isready -U postgres -q && psql -U postgres -tAc 'select 1'")
        if rc == 0 and s.strip() == "1":
            return
        time.sleep(1)


def main():
    for c in ("pg-a", "pg-b"):
        run(["docker", "rm", "-f", "-v", c])
    run(["docker", "run", "-d", "--name", "pg-a", "-e", "POSTGRES_PASSWORD=x", IMG])
    listo("pg-a")
    OUT.append(f"# SALIDA extra — lo que se pierde entre copias (vídeo 414)\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con "
               f"`python correr_extra.py`. `{IMG}` en Docker.\n")
    sh("pg-a", "psql -U postgres -c \"create table pedidos (id int primary key, total numeric)\" "
               "-c \"insert into pedidos select g, 10 from generate_series(1,10000) g\"")
    bloque("antes de la copia", "psql -c 'select count(*), max(id) from pedidos'", sh("pg-a", "psql -U postgres -tAc 'select count(*), max(id) from pedidos'"))
    bloque("la copia de las 03:00", "pg_dump -Fc -f copia.dump", sh("pg-a", "pg_dump -U postgres -Fc -f /tmp/copia.dump postgres && echo copia hecha"))
    run(["docker", "cp", "pg-a:/tmp/copia.dump", str(AQUI / "copias" / "copia-rpo.dump")])
    bloque("durante la mañana entran 25 pedidos más", "psql -c 'insert … generate_series(10001,10025)'",
           sh("pg-a", "psql -U postgres -c \"insert into pedidos select g, 10 from generate_series(10001,10025) g\" -tAc 'select count(*), max(id) from pedidos'"))
    bloque("el disco se muere", "docker rm -f -v pg-a", run(["docker", "rm", "-f", "-v", "pg-a"]))
    run(["docker", "run", "-d", "--name", "pg-b", "-e", "POSTGRES_PASSWORD=x", IMG])
    listo("pg-b")
    run(["docker", "cp", str(AQUI / "copias" / "copia-rpo.dump"), "pg-b:/tmp/copia.dump"])
    bloque("restaurar la copia de las 03:00", "pg_restore -d postgres copia.dump; select count(*), max(id)",
           sh("pg-b", "pg_restore -U postgres -d postgres /tmp/copia.dump && psql -U postgres -tAc 'select count(*), max(id) from pedidos'"),
           "Los 25 pedidos posteriores a la copia (10001-10025) no están.")
    run(["docker", "rm", "-f", "-v", "pg-b"])
    (AQUI / "SALIDA-extra.md").write_text("\n".join(OUT), encoding="utf-8")
    print("ok SALIDA-extra.md")


if __name__ == "__main__":
    main()
