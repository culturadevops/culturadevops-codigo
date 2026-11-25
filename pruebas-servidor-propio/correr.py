# -*- coding: utf-8 -*-
"""Banco del vídeo 414 «¿Vale la pena la nube en 2027, o volver a servidores propios?».
Lo que la base de datos gestionada hace por ti y en un servidor propio haces tú: copia, desastre y restauración.
Todo en Docker con postgres:17-alpine.
  · 10.000 pedidos en una base de datos;
  · copia con pg_dump; se borra el contenedor Y el volumen (el disco «se muere»);
  · base de datos nueva, restaurar la copia, contar, y cuánto tarda.
    python correr.py   -> SALIDA.md
"""
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
OUT = []
IMG = "postgres:17-alpine"


def run(args, timeout=None):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return (p.stdout + p.stderr).strip(), p.returncode


def sh(c, cmd):
    return run(["docker", "exec", c, "sh", "-c", cmd])


def bloque(titulo, mostrado, res, nota=None):
    s, rc = res
    OUT.append(f"### {titulo}\n\n`$ {mostrado}`\n\n```\n{s}\n```\n(código de salida {rc})\n" + (f"\n> {nota}\n" if nota else ""))
    print(f"[{rc}] {titulo}")
    return s, rc


def listo(c):
    for _ in range(60):
        s, rc = sh(c, "pg_isready -U postgres -q && psql -U postgres -tAc 'select 1'")
        if rc == 0 and s.strip() == "1":
            return
        time.sleep(1)


def main():
    for c in ("pg-prod", "pg-nuevo"):
        run(["docker", "rm", "-f", "-v", c])
    run(["docker", "volume", "rm", "datos-prod"])
    (AQUI / "copias").mkdir(exist_ok=True)
    run(["docker", "run", "-d", "--name", "pg-prod", "-e", "POSTGRES_PASSWORD=x", "-v", "datos-prod:/var/lib/postgresql/data", IMG])
    listo("pg-prod")
    OUT.append(f"# SALIDA — servidor propio: copia y restauración (vídeo 414)\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC "
               f"con `python correr.py`. `{IMG}` en Docker.\n")

    OUT.append("## 1 · La base de datos\n")
    bloque("versión", "psql -c 'select version()'", sh("pg-prod", "psql -U postgres -tAc 'select version()' | cut -d, -f1"))
    bloque("10.000 pedidos", "psql -c 'create table pedidos …; insert … generate_series(1,10000)'",
           sh("pg-prod", "psql -U postgres -c \"create table pedidos (id int primary key, cliente text, total numeric)\" "
                         "-c \"insert into pedidos select g, 'cliente ' || (g % 500), round((random()*100)::numeric, 2) from generate_series(1,10000) g\""))
    bloque("contarlos y sumarlos", "psql -c 'select count(*), sum(total) from pedidos'",
           sh("pg-prod", "psql -U postgres -tAc 'select count(*), sum(total) from pedidos'"))

    OUT.append("## 2 · La copia\n")
    t0 = time.time()
    s, rc = sh("pg-prod", "pg_dump -U postgres -Fc -f /tmp/copia.dump postgres && ls -l /tmp/copia.dump | awk '{print $5\" bytes\"}'")
    bloque("pg_dump", "pg_dump -Fc -f copia.dump", (s + f"\n{time.time() - t0:.1f} s", rc))
    run(["docker", "cp", "pg-prod:/tmp/copia.dump", str(AQUI / "copias" / "copia.dump")])
    OUT.append("### sacarla del servidor\n\n`$ docker cp pg-prod:/tmp/copia.dump copias/`\n\n```\n"
               f"{(AQUI / 'copias' / 'copia.dump').stat().st_size} bytes en copias/\n```\n")

    OUT.append("## 3 · El disco se muere\n")
    bloque("borrar el servidor y su disco", "docker rm -f -v pg-prod; docker volume rm datos-prod",
           run(["sh", "-c", "docker rm -f -v pg-prod >/dev/null && docker volume rm datos-prod"]))
    bloque("¿queda algo?", "docker volume ls | grep datos-prod", run(["sh", "-c", "docker volume ls | grep datos-prod || echo '(nada)'"]))

    OUT.append("## 4 · Restaurar\n")
    t0 = time.time()
    run(["docker", "run", "-d", "--name", "pg-nuevo", "-e", "POSTGRES_PASSWORD=x", IMG])
    listo("pg-nuevo")
    run(["docker", "cp", str(AQUI / "copias" / "copia.dump"), "pg-nuevo:/tmp/copia.dump"])
    s, rc = sh("pg-nuevo", "pg_restore -U postgres -d postgres /tmp/copia.dump && psql -U postgres -tAc 'select count(*), sum(total) from pedidos'")
    bloque("servidor nuevo + pg_restore + contar y sumar",
           "docker run postgres; pg_restore -d postgres copia.dump; select count(*), sum(total)",
           (s + f"\n{time.time() - t0:.1f} s desde cero", rc), "Mismos pedidos y misma suma que antes de borrar el disco.")
    run(["docker", "rm", "-f", "-v", "pg-nuevo"])

    (AQUI / "SALIDA.md").write_text("\n".join(OUT), encoding="utf-8")
    print("ok SALIDA.md")


if __name__ == "__main__":
    main()
