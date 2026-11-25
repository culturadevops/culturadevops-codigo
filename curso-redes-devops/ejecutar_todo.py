# -*- coding: utf-8 -*-
"""Construye la imagen del laboratorio, corre las 7 lecciones y regenera SALIDA.md.

La regla de la casa: nada de lo que sale en el vídeo se escribe a mano. Sale de aquí.
Hace falta Docker y Python 3.10+. Cada lección corre en un contenedor docker:cli que habla con tu
Docker: crea redes y contenedores con el prefijo «red-» y los borra al terminar. La lección 4 usa
también la imagen golang:1.26 (el cliente en Go).

    python ejecutar_todo.py
"""
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", MSYS_NO_PATHCONV="1")
IMAGEN = "curso-red:1"

LECCIONES = [
    ("01", "Escuchar en 127.0.0.1 o en 0.0.0.0", "01_escuchar.sh"),
    ("02", "Las redes de Docker y quién ve a quién", "02_dns_de_docker.sh"),
    ("03", "El DNS que resolvía a lo viejo", "03_cache_dns.sh"),
    ("04", "TLS: la cadena, el SAN, la caducidad y el nombre", "04_tls.sh"),
    ("05", "El MTU: el fallo que solo aparece con respuestas grandes", "05_mtu.sh"),
    ("06", "La IP que ves no es la del cliente", "06_ip_del_cliente.sh"),
    ("07", "El proyecto: diagnostico.sh", "07_proyecto.sh"),
]


def correr(cmd, timeout=1200):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       cwd=AQUI, env=ENV, timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    sello = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    print("  construyendo la imagen del laboratorio ...", flush=True)
    c, s = correr(["docker", "build", "-q", "-t", IMAGEN, "imagen"])
    if c != 0:
        raise SystemExit(f"la imagen no se construye:\n{s}")
    correr(["docker", "pull", "-q", "golang:1.26"])
    _, dv = correr(["docker", "version", "--format", "{{.Server.Version}}"])
    _, vers = correr(["docker", "run", "--rm", IMAGEN, "sh", "-c",
                      "curl --version | head -1 | cut -d' ' -f1,2; openssl version; nginx -v 2>&1; python3 --version"])
    partes = ["# SALIDA — curso «Redes para gente de DevOps: DNS, NAT, TLS y el «en mi máquina sí»»", "",
              "> Generado por `ejecutar_todo.py`. **No se escribe a mano.**", "",
              f"- fecha: `{sello}`", f"- Docker `{dv.strip()}` · anfitrión `{platform.system()} {platform.release()}`",
              *[f"- `{l.strip()}`" for l in vers.strip().splitlines()], ""]
    host = str(AQUI)
    fallos = 0
    for num, titulo, script in LECCIONES:
        print(f"  [{num}] {titulo} ...", end=" ", flush=True)
        codigo, salida = correr(["docker", "run", "--rm", "-e", f"CURSO_HOST={host}",
                                 "-v", "/var/run/docker.sock:/var/run/docker.sock",
                                 "-v", f"{AQUI / 'lecciones'}:/curso:ro", "docker:cli", "sh", f"/curso/{script}"])
        fallos += codigo != 0
        partes += [f"## Leccion {num} — {titulo}", "",
                   f"`sh lecciones/{script}   # en docker:cli, con el socket de Docker` · codigo de salida `{codigo}`",
                   "", "```", salida.strip("\n"), "```", ""]
        print("ok" if codigo == 0 else f"FALLO (codigo {codigo})")
    (AQUI / "SALIDA.md").write_text("\n".join(partes) + "\n", encoding="utf-8", newline="\n")
    print(f"\n  -> SALIDA.md regenerado (7 lecciones, {fallos} fallos)")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
