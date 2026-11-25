# -*- coding: utf-8 -*-
"""Levanta el laboratorio limpio, corre las 9 lecciones y regenera SALIDA.md.

La regla de la casa: nada de lo que sale en el vídeo se escribe a mano. Sale de aquí.
Hace falta Docker (con compose) y Python 3.10+. Todo corre en contenedores: no instala nada.

    python ejecutar_todo.py            # y al terminar borra el laboratorio (contenedores y volúmenes)
    python ejecutar_todo.py --dejar    # lo deja levantado, para jugar
"""
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", MSYS_NO_PATHCONV="1")

# (número, título, script, dónde corre). «operador» = dentro del laboratorio; «docker» = en un
# contenedor docker:cli que habla con el Docker de la máquina (la lección de volúmenes).
LECCIONES = [
    ("01", "La copia que vale 20 bytes", "01_la_copia_vacia.sh", "operador"),
    ("02", "El ensayo cronometrado: RPO y RTO", "02_ensayo_cronometrado.sh", "operador"),
    ("03", "Lo que pg_dump no lleva: los roles", "03_lo_que_no_viaja.sh", "operador"),
    ("04", "Volver a un segundo concreto: punto en el tiempo", "04_punto_en_el_tiempo.sh", "operador"),
    ("05", "Los volúmenes de Docker", "05_volumenes.sh", "docker"),
    ("06", "El repositorio: lo que no viaja en un clon", "06_git.sh", "operador"),
    ("07", "Los secretos: la clave que estaba en la máquina", "07_secretos.sh", "operador"),
    ("08", "La retención que se come la última copia buena", "08_retencion.sh", "operador"),
    ("09", "El proyecto: ensayo.sh", "09_proyecto.sh", "operador"),
]


def correr(cmd, timeout=1200):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       cwd=AQUI, env=ENV, timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def compose(*args, timeout=1200):
    return correr(["docker", "compose", *args], timeout=timeout)


def main():
    sello = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    print("  levantando el laboratorio limpio ...", flush=True)
    compose("down", "-v")
    c, s = compose("up", "-d", "--build", "--wait")
    if c != 0:
        raise SystemExit(f"el laboratorio no arranca:\n{s}")
    _, pgv = compose("exec", "-T", "db", "postgres", "--version")
    _, dv = correr(["docker", "version", "--format", "{{.Server.Version}}"])
    _, agev = compose("exec", "-T", "operador", "age", "--version")
    _, gitv = compose("exec", "-T", "operador", "git", "--version")
    partes = ["# SALIDA — curso «Restaurar, no copiar: copias de seguridad que de verdad funcionan»", "",
              "> Generado por `ejecutar_todo.py`. **No se escribe a mano.**", "",
              f"- fecha: `{sello}`", f"- servidor: `{pgv.strip()}` (imagen `postgres:17`, WAL archivado)",
              f"- Docker `{dv.strip()}` · age `{agev.strip()}` · `{gitv.strip()}`",
              f"- anfitrión: `{platform.system()} {platform.release()}`", ""]
    fallos = 0
    for num, titulo, script, donde in LECCIONES:
        print(f"  [{num}] {titulo} ...", end=" ", flush=True)
        if donde == "operador":
            codigo, salida = compose("exec", "-T", "operador", "bash", f"/curso/{script}")
            cmd_txt = f"bash lecciones/{script}   # dentro del operador"
        else:
            codigo, salida = correr(["docker", "run", "--rm", "-v", "/var/run/docker.sock:/var/run/docker.sock",
                                     "-v", f"{AQUI / 'lecciones'}:/curso:ro", "docker:cli", "sh", f"/curso/{script}"])
            cmd_txt = f"sh lecciones/{script}   # en docker:cli, con el socket de Docker"
        fallos += codigo != 0
        partes += [f"## Leccion {num} — {titulo}", "", f"`{cmd_txt}` · codigo de salida `{codigo}`", "",
                   "```", salida.strip("\n"), "```", ""]
        print("ok" if codigo == 0 else f"FALLO (codigo {codigo})")

    (AQUI / "SALIDA.md").write_text("\n".join(partes) + "\n", encoding="utf-8", newline="\n")
    if "--dejar" not in sys.argv:
        compose("down", "-v")
    print(f"\n  -> SALIDA.md regenerado (9 lecciones, {fallos} fallos)")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
