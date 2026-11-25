# -*- coding: utf-8 -*-
"""Banco del vídeo 406 «¿Vale la pena GitHub Actions en 2027?».
  · Un workflow ejecutado EN LOCAL con act (nektos/act) dentro de un contenedor Linux con el socket de Docker.
  · Las etiquetas de una action se mueven: git ls-remote de actions/checkout (v4 y la última v4.x.y).
    python correr.py   -> SALIDA.md
"""
import subprocess
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
OUT = []
WF = """name: ci
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - name: tests
        run: |
          echo "probando con la version ${{ matrix.version }}"
          test -f app.txt && echo "app.txt encontrado"
  despliegue:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - run: echo "solo llego aqui si los tests pasan"
"""


def run(args):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (p.stdout + p.stderr).strip(), p.returncode


def ex(cmd):
    return run(["docker", "exec", "-w", "/work", "actlab", "sh", "-c", cmd])


def bloque(titulo, mostrado, cmd, nota=None):
    s, rc = ex(cmd)
    OUT.append(f"### {titulo}\n\n`$ {mostrado}`\n\n```\n{s}\n```\n(código de salida {rc})\n" + (f"\n> {nota}\n" if nota else ""))
    print(f"[{rc}] {titulo}")
    return s, rc


def main():
    run(["docker", "rm", "-f", "actlab"])
    run(["docker", "run", "-d", "--name", "actlab", "-v", "//var/run/docker.sock:/var/run/docker.sock", "alpine:3.22", "sh", "-c", "mkdir -p /work && sleep infinity"])
    ex("mkdir -p /work && apk add -q curl git docker-cli >/dev/null && "
       "curl -sL https://github.com/nektos/act/releases/latest/download/act_Linux_x86_64.tar.gz | tar xz -C /usr/local/bin act")
    ex(f"mkdir -p .github/workflows && cat > .github/workflows/ci.yml <<'EOF'\n{WF}EOF\n"
       "echo hola > app.txt && git init -q && git config user.email a@b.c && git config user.name lab && git add -A && git commit -qm inicio")

    OUT.append(f"# SALIDA — GitHub Actions (vídeo 406)\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`.\n")
    OUT.append("## 1 · Ejecutar un workflow sin subir nada\n")
    bloque("la versión de act", "act --version", "act --version")
    bloque("el workflow", "cat .github/workflows/ci.yml", "cat .github/workflows/ci.yml")
    bloque("qué trabajos hay", "act -l", "act -l")
    bloque("ejecutarlo en local", "act push -P ubuntu-latest=catthehacker/ubuntu:act-latest",
           "act push -P ubuntu-latest=catthehacker/ubuntu:act-latest 2>&1 | grep -E \"Job succeeded|Job failed|probando|encontrado|llego aqui|Success - |Failure - \" | sed 's/^.*\\] //'")
    ex("rm app.txt && git add -A && git commit -qm 'sin app.txt'")
    bloque("y si un test falla", "rm app.txt; act push …",
           "act push -P ubuntu-latest=catthehacker/ubuntu:act-latest 2>&1 | grep -E \"Job succeeded|Job failed|probando|encontrado|llego aqui|Failure - |Success - \" | sed 's/^.*\\] //'",
           "El trabajo «despliegue» no aparece: depende de «test», que falló.")

    OUT.append("## 2 · Una etiqueta de action se mueve\n")
    bloque("actions/checkout: v4 y sus versiones 4.x", "git ls-remote --tags https://github.com/actions/checkout | grep v4",
           "git ls-remote --tags https://github.com/actions/checkout | grep -E \"refs/tags/v4$\"; "
           "git ls-remote --tags https://github.com/actions/checkout | grep -E \"refs/tags/v4\\.[0-9]+\\.[0-9]+$\" | sort -k2 -V | tail -3")
    bloque("y la v5", "git ls-remote --tags https://github.com/actions/checkout | grep v5",
           "git ls-remote --tags https://github.com/actions/checkout | grep -E \"refs/tags/v5$\"; "
           "git ls-remote --tags https://github.com/actions/checkout | grep -E \"refs/tags/v5\\.[0-9]+\\.[0-9]+$\" | sort -k2 -V | tail -2")

    (AQUI / "SALIDA.md").write_text("\n".join(OUT), encoding="utf-8")
    print("ok SALIDA.md")


if __name__ == "__main__":
    main()
