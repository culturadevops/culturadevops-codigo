# -*- coding: utf-8 -*-
"""Restic — banco de pruebas del vídeo 325 (cultura-devops, serie herramientas).

Todo en Docker y todo a SALIDA.md: lo que sale en el vídeo se copia de ahí.
Datos de prueba: la biblioteca estándar de Python 3.12 (de la imagen python:3.12-slim),
copiada a un volumen. Repositorio en otro volumen. Contraseña por variable de entorno.

    python correr.py
"""
import subprocess
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RESTIC = "restic/restic:latest"
VD, VR = "rst-datos", "rst-repo"
ENV = ["-e", "RESTIC_REPOSITORY=/repo", "-e", "RESTIC_PASSWORD=una-clave-larga-de-prueba"]
salida = []


def sh(cmd, timeout=900):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout)
    return (r.stdout + r.stderr).strip()


def anota(titulo, cmd_txt, texto):
    salida.extend(["", f"### {titulo}", "", f"`$ {cmd_txt}`", "", "```", texto.strip(), "```"])
    print(f"--- {titulo}\n{texto.strip()[:900]}\n", flush=True)


def r(script, env=ENV, host="servidor"):
    """Un shell dentro de la imagen de restic, con datos y repo montados. Hostname FIJO salvo
    que se pida otro: restic agrupa las copias por host (ver la sección 8)."""
    h = ["--hostname", host] if host else []
    return sh(["docker", "run", "--rm", *h, *env, "-v", f"{VD}:/data", "-v", f"{VR}:/repo",
               "--entrypoint", "sh", RESTIC, "-c", script])


def ids():
    import json
    return [x["short_id"] for x in json.loads(r("restic snapshots --json"))]


def main():
    for v in (VD, VR):
        sh(["docker", "volume", "rm", "-f", v])
        sh(["docker", "volume", "create", v])
    sh(["docker", "run", "--rm", "-v", f"{VD}:/data", "python:3.12-slim", "sh", "-c",
        "cp -r /usr/local/lib/python3.12 /data/proyecto && rm -rf /data/proyecto/__pycache__"])

    salida.append("\n## 1 · Versión y datos")
    anota("versión", "restic version", r("restic version"))
    anota("los datos", "du -sh /data/proyecto; find /data/proyecto -type f | wc -l",
          r("du -sh /data/proyecto; find /data/proyecto -type f | wc -l"))

    salida.append("\n## 2 · Crear el repositorio")
    anota("init", "restic init", r("restic init"))
    anota("qué hay dentro del repo", "ls /repo", r("ls /repo"))

    salida.append("\n## 3 · Primera copia")
    anota("backup 1", "restic backup /data/proyecto", r("time -p restic backup /data/proyecto 2>&1"))

    salida.append("\n## 4 · Cambio pequeño y segunda copia (deduplicación)")
    r("echo '# cambio de prueba' >> /data/proyecto/os.py && "
      "cp /data/proyecto/json/encoder.py /data/proyecto/encoder_copia.py")
    anota("backup 2", "restic backup /data/proyecto", r("time -p restic backup /data/proyecto 2>&1"))
    anota("snapshots", "restic snapshots", r("restic snapshots"))
    anota("stats restore-size", "restic stats --mode restore-size", r("restic stats --mode restore-size"))
    anota("stats raw-data", "restic stats --mode raw-data", r("restic stats --mode raw-data"))
    anota("tamaño real del repo", "du -sh /repo", r("du -sh /repo"))

    salida.append("\n## 5 · Cifrado: el texto no aparece en el repo")
    anota("grep en los datos", "grep -rl 'cambio de prueba' /data/proyecto | head -3",
          r("grep -rl 'cambio de prueba' /data/proyecto | head -3"))
    anota("grep en el repo", "grep -rl 'cambio de prueba' /repo | wc -l",
          r("grep -rl 'cambio de prueba' /repo | wc -l"))
    anota("contraseña equivocada", "RESTIC_PASSWORD=otra restic snapshots",
          r("RESTIC_PASSWORD=otra restic snapshots; echo codigo=$?"))

    salida.append("\n## 6 · Restaurar un solo archivo")
    anota("borrar el archivo", "rm /data/proyecto/os.py", r("rm /data/proyecto/os.py && ls /data/proyecto/os.py; echo codigo=$?"))
    anota("buscarlo", "restic find os.py", r("restic find /data/proyecto/os.py"))
    anota("restore --include", "restic restore latest --target /tmp/r --include /data/proyecto/os.py",
          r("restic restore latest --target /tmp/r --include /data/proyecto/os.py && "
            "find /tmp/r -type f && tail -1 /tmp/r/data/proyecto/os.py"))
    anota("restaurar la versión vieja", "restic restore <snapshot 1> ... os.py",
          r(f"restic restore {ids()[0]} --target /tmp/v --include /data/proyecto/os.py && "
            "tail -2 /tmp/v/data/proyecto/os.py"))
    anota("dump a la salida", "restic dump latest /data/proyecto/os.py | tail -1",
          r("restic dump latest /data/proyecto/os.py | tail -1"))

    salida.append("\n## 7 · Limpiar copias viejas")
    for i in range(3):
        r(f"echo '# vuelta {i}' >> /data/proyecto/os.py 2>/dev/null || echo '# vuelta {i}' > /data/proyecto/os.py; "
          "restic backup -q /data/proyecto")
    anota("snapshots antes", "restic snapshots", r("restic snapshots"))
    anota("forget --dry-run", "restic forget --keep-last 2 --dry-run",
          r("restic forget --keep-last 2 --dry-run"))
    anota("forget --prune", "restic forget --keep-last 2 --prune",
          r("restic forget --keep-last 2 --prune"))
    anota("snapshots después", "restic snapshots", r("restic snapshots"))
    anota("check", "restic check", r("restic check"))

    salida.append("\n## 8 · La trampa: el hostname (contenedores sin --hostname)")
    sh(["docker", "volume", "rm", "-f", VR]); sh(["docker", "volume", "create", VR])
    r("restic init -q", host=None)
    anota("backup con hostname aleatorio 1", "docker run (sin --hostname) restic backup",
          r("hostname; restic backup -q /data/proyecto && echo ok", host=None))
    anota("backup con hostname aleatorio 2", "docker run (sin --hostname) restic backup",
          r("hostname; restic backup /data/proyecto 2>&1 | head -3", host=None))
    for _ in range(2):
        r("restic backup -q /data/proyecto", host=None)
    anota("forget agrupa por host", "restic forget --keep-last 1 --dry-run",
          r("restic forget --keep-last 1 --dry-run | grep -E 'keep|remove|snapshots$' ", host=None))
    anota("la solución: --group-by paths", "restic forget --keep-last 1 --group-by paths --dry-run",
          r("restic forget --keep-last 1 --group-by paths --dry-run | grep -E 'keep|remove|snapshots$'", host=None))

    for v in (VD, VR):
        sh(["docker", "volume", "rm", "-f", v])
    cab = [f"# SALIDA — Restic (vídeo 325)", "",
           f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. "
           f"Imagen {RESTIC}. Datos: biblioteca estándar de python:3.12-slim."]
    (AQUI / "SALIDA.md").write_text("\n".join(cab + salida) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
