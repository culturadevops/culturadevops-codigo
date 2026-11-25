# -*- coding: utf-8 -*-
"""correr.py — banco del vídeo «System design: hashing consistente» (cultura-devops, vídeo 354).

Solo cálculo, sin red ni disco: lab/main.go reparte 100.000 claves entre servidores con módulo, con un
anillo de hashing consistente (1 a 1.000 nodos virtuales) y con rendezvous, y mide qué se mueve al añadir
o quitar un servidor, lo justo del reparto y lo que cuesta cada búsqueda. Go 1.27.2 en Docker.

    python correr.py      -> SALIDA.md
"""
import datetime
import os
import subprocess
from pathlib import Path

AQUI = Path(__file__).resolve().parent
r = subprocess.run(["docker", "run", "--rm", "-v", f"{(AQUI / 'lab').as_posix()}:/w", "-w", "/w",
                    "-v", "fab-go-mod:/go/pkg/mod", "-v", "fab-go-cache:/root/.cache/go-build", "golang:1.27.2",
                    "sh", "-c", "go version && go run ."], capture_output=True, text=True, encoding="utf-8",
                   errors="replace", env=dict(os.environ, MSYS_NO_PATHCONV="1"))
o = (r.stdout + r.stderr).strip().splitlines()
cab = ["# SALIDA — «System design: hashing consistente» (cultura-devops, vídeo 354)", "",
       "> Generado por `correr.py`. **No se escribe a mano.**", "",
       f"- fecha: `{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%SZ}` · `{o[0]}`",
       "- hash: FNV-1a de 64 bits + el mezclador de splitmix64. Los tiempos son de esta máquina."]
(AQUI / "SALIDA.md").write_bytes(("\n".join(cab) + "\n\n```\n" + "\n".join(o[1:]) + "\n```\n").encode("utf-8"))
print("\n".join(o))
