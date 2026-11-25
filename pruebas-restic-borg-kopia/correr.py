# -*- coding: utf-8 -*-
"""Restic vs Borg vs Kopia — banco de pruebas del vídeo 336 (cultura-devops, serie versus).

La MISMA carpeta respaldada con los tres, y la MISMA prueba: tiempo, espacio en disco tras una
segunda copia con un cambio pequeño, deduplicación, cifrado, y restaurar un archivo. Datos: la
biblioteca estándar de Python 3.12 (unos 1.300 archivos). Todo en Docker, un volumen por datos y
un repositorio por herramienta.

    python correr.py
"""
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RESTIC = "restic/restic:latest"
BORG = "lab-borg"
KOPIA = "kopia/kopia:latest"
PW = "una-clave-larga-de-prueba"
salida = []


def sh(cmd, timeout=900, env=None):
    import os
    e = {**os.environ, **(env or {})}
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, env=e)
    return (r.stdout + r.stderr).strip()


def anota(titulo, cmd_txt, texto):
    salida.extend(["", f"### {titulo}", "", f"`$ {cmd_txt}`", "", "```", texto.strip(), "```"])
    print(f"--- {titulo}\n{texto.strip()[:1200]}\n", flush=True)


def datos():
    sh(["docker", "volume", "rm", "-f", "bk-datos"])
    sh(["docker", "volume", "create", "bk-datos"])
    sh(["docker", "run", "--rm", "-v", "bk-datos:/d", "python:3.12-slim", "sh", "-c",
        "cp -r /usr/local/lib/python3.12 /d/proyecto && rm -rf /d/proyecto/__pycache__"])


def vol(nombre):
    sh(["docker", "volume", "rm", "-f", nombre])
    sh(["docker", "volume", "create", nombre])


def du(nombre):
    return sh(["docker", "run", "--rm", "-v", f"{nombre}:/r", "alpine", "du", "-sh", "/r"]).split()[0]


def cambiar():
    sh(["docker", "run", "--rm", "-v", "bk-datos:/d", "alpine", "sh", "-c",
        "echo cambio >> /d/proyecto/os.py && cp /d/proyecto/json/encoder.py /d/proyecto/copia.py"])


def restic(script, v="bk-restic"):
    return sh(["docker", "run", "--rm", "-e", f"RESTIC_PASSWORD={PW}", "-e", "RESTIC_REPOSITORY=/repo",
               "-v", "bk-datos:/data:ro", "-v", f"{v}:/repo", "--entrypoint", "sh", RESTIC, "-c", script])


def borg(script, v="bk-borg"):
    return sh(["docker", "run", "--rm", "-e", f"BORG_PASSPHRASE={PW}", "-e", "BORG_REPO=/repo",
               "-v", "bk-datos:/data:ro", "-v", f"{v}:/repo", BORG, "sh", "-c", script])


def kopia(script, v="bk-kopia"):
    return sh(["docker", "run", "--rm", "-e", f"KOPIA_PASSWORD={PW}",
               "-v", "bk-datos:/data:ro", "-v", f"{v}:/repo", "-v", "bk-kopia-cfg:/app/config",
               "-v", "bk-kopia-cache:/app/cache", "--entrypoint", "sh", KOPIA, "-c", script])


def cronometra(f):
    t = time.time()
    out = f()
    return out, time.time() - t


def main():
    for v in ("bk-restic", "bk-borg", "bk-kopia", "bk-kopia-cfg", "bk-kopia-cache"):
        vol(v)
    datos()
    salida.append("\n## 1 · Versiones y datos")
    anota("versiones", "restic/borg/kopia version",
          sh(["docker", "run", "--rm", RESTIC, "version"]).split("\n")[0] + "\n"
          + "borg " + sh(["docker", "run", "--rm", BORG, "borg", "--version"]).split()[-1] + "\n"
          + "kopia " + sh(["docker", "run", "--rm", "--entrypoint", "kopia", KOPIA, "--version"]).split()[0])
    anota("los datos", "du -sh; nº de archivos",
          sh(["docker", "run", "--rm", "-v", "bk-datos:/d", "alpine", "sh", "-c",
              "du -sh /d/proyecto; find /d/proyecto -type f | wc -l"]))

    salida.append("\n## 2 · Crear el repositorio y la primera copia")
    o, t = cronometra(lambda: restic("restic init -q >/dev/null; restic backup -q /data/proyecto; echo ok"))
    anota("Restic", "restic init; restic backup", f"{o}\n(1.ª copia en {t:.0f} s) · repo: {du('bk-restic')}")
    o, t = cronometra(lambda: borg("borg init -e repokey /repo >/dev/null 2>&1; borg create /repo::c1 /data/proyecto 2>&1; echo ok"))
    anota("Borg", "borg init -e repokey; borg create ::c1", f"{o}\n(1.ª copia en {t:.0f} s) · repo: {du('bk-borg')}")
    o, t = cronometra(lambda: kopia(
        "kopia repository create filesystem --path=/repo --cache-directory=/app/cache >/dev/null 2>&1; "
        "kopia snapshot create /data/proyecto 2>&1 | tail -1; echo ok"))
    anota("Kopia", "kopia repository create filesystem; kopia snapshot create", f"{o}\n(1.ª copia en {t:.0f} s) · repo: {du('bk-kopia')}")

    salida.append("\n## 3 · Un cambio pequeño y segunda copia (deduplicación)")
    cambiar()
    o, t = cronometra(lambda: restic("restic backup /data/proyecto 2>&1 | grep -E 'Added|new,'; echo ok"))
    anota("Restic", "restic backup", f"{o}\n(2.ª copia en {t:.0f} s) · repo ahora: {du('bk-restic')}")
    o, t = cronometra(lambda: borg("borg create --stats /repo::c2 /data/proyecto 2>&1 | grep -E 'This archive|Deduplicated'; echo ok"))
    anota("Borg", "borg create --stats ::c2", f"{o}\n(2.ª copia en {t:.0f} s) · repo ahora: {du('bk-borg')}")
    o, t = cronometra(lambda: kopia("kopia snapshot create /data/proyecto 2>&1 | tail -1; echo ok"))
    anota("Kopia", "kopia snapshot create", f"{o}\n(2.ª copia en {t:.0f} s) · repo ahora: {du('bk-kopia')}")
    anota("espacio en disco tras 2 copias", "du -sh de cada repositorio",
          f"Restic: {du('bk-restic')}\nBorg:   {du('bk-borg')}\nKopia:  {du('bk-kopia')}")

    salida.append("\n## 4 · Cifrado: ¿se ve el texto en el repositorio?")
    anota("grep del cambio en cada repo", "grep -rl 'cambio' /repo | wc -l",
          "Restic: " + sh(["docker", "run", "--rm", "-v", "bk-restic:/r", "alpine", "sh", "-c", "grep -rl cambio /r | wc -l"]) + "\n"
          "Borg:   " + sh(["docker", "run", "--rm", "-v", "bk-borg:/r", "alpine", "sh", "-c", "grep -rl cambio /r | wc -l"]) + "\n"
          "Kopia:  " + sh(["docker", "run", "--rm", "-v", "bk-kopia:/r", "alpine", "sh", "-c", "grep -rl cambio /r | wc -l"]) + "\n"
          "(cada uno cifra por defecto: 0 = no aparece)")

    salida.append("\n## 5 · Restaurar un solo archivo")
    anota("Restic", "restic dump latest .../os.py | tail -1", restic("restic dump latest /data/proyecto/os.py | tail -1"))
    anota("Borg", "borg extract ::c2 .../os.py", borg(
        "cd /tmp && borg extract /repo::c2 data/proyecto/os.py 2>&1 && tail -1 data/proyecto/os.py"))
    anota("Kopia", "kopia restore <root>/os.py /tmp/os.py",
          kopia("ROOT=$(kopia snapshot list /data/proyecto 2>/dev/null | tail -1 | awk '{print $4}'); "
                "kopia restore $ROOT/os.py /tmp/os.py 2>&1 >/dev/null; tail -1 /tmp/os.py"))

    salida.append("\n## 6 · Listar las copias")
    anota("Restic", "restic snapshots", restic("restic snapshots"))
    anota("Borg", "borg list", borg("borg list /repo"))
    anota("Kopia", "kopia snapshot list", kopia("kopia snapshot list /data/proyecto 2>&1"))

    for v in ("bk-datos", "bk-restic", "bk-borg", "bk-kopia", "bk-kopia-cfg", "bk-kopia-cache"):
        sh(["docker", "volume", "rm", "-f", v])
    cab = ["# SALIDA — Restic vs Borg vs Kopia (vídeo 336)", "",
           f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. "
           "restic 0.19.1, borg 1.4.3, kopia 0.23.1; datos: biblioteca estándar de Python 3.12."]
    (AQUI / "SALIDA.md").write_text("\n".join(cab + salida) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
