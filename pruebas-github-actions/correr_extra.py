# -*- coding: utf-8 -*-
"""Banco extra del vídeo 406: lo que hace el contenedor actlab de correr.py, más cosas.
  · actionlint encuentra errores del workflow antes de hacer push.
  · act enmascara los secretos en el log.
  · act ejecuta un solo trabajo y una sola combinación de la matriz.
  · una action fijada a un commit completo funciona igual.
    python correr_extra.py   -> SALIDA-extra.md   (necesita el contenedor actlab de correr.py)
"""
import subprocess
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
OUT = []
IMG = "-P ubuntu-latest=catthehacker/ubuntu:act-latest"
FILTRO = " 2>&1 | grep -E \"Job succeeded|Job failed|probando|token|llego aqui|checkout|Failure - |Success - \" | sed 's/^.*\\] //'"

ROTO = """name: roto
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo "version ${{ matrix.versoin }}"
  despliegue:
    needs: tset
    runs-on: ubuntu-latest
    steps:
      - run: echo hola
"""
SECRETO = """name: secreto
on: [push]
jobs:
  usar:
    runs-on: ubuntu-latest
    steps:
      - run: echo "el token es ${{ secrets.TOKEN }}"
"""
FIJADO = """name: fijado
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0
      - run: ls app.txt && echo "checkout fijado a un commit, ok"
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
    # vuelve a dejar app.txt y aparta el ci.yml para que cada prueba corra sola
    ex("echo hola > app.txt && mkdir -p /otros && mv .github/workflows/ci.yml /otros/ 2>/dev/null; "
       "git add -A && git commit -qm 'con app.txt' || true")
    OUT.append(f"# SALIDA extra — GitHub Actions (vídeo 406)\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr_extra.py`.\n")

    OUT.append("## 1 · actionlint: los errores, antes del push\n")
    ex(f"mkdir -p /lint && cat > /lint/roto.yml <<'EOF'\n{ROTO}EOF")
    bloque("la versión de actionlint", "actionlint --version",
           "docker run --rm rhysd/actionlint:latest --version")
    bloque("un workflow con dos erratas", "actionlint roto.yml",
           "cat /lint/roto.yml | docker run --rm -i rhysd/actionlint:latest -oneline -",
           "matrix.versoin (en lugar de version) y needs: tset (en lugar de test).")

    OUT.append("## 2 · Los secretos salen enmascarados\n")
    ex(f"cat > .github/workflows/secreto.yml <<'EOF'\n{SECRETO}EOF")
    bloque("ejecutar con un secreto", "act push -s TOKEN=supersecreto123 …",
           f"act push {IMG} -s TOKEN=supersecreto123 -W .github/workflows/secreto.yml" + FILTRO)
    bloque("¿aparece el valor en el log?", "act push -s TOKEN=supersecreto123 … | grep -c supersecreto123",
           f"act push {IMG} -s TOKEN=supersecreto123 -W .github/workflows/secreto.yml 2>&1 | grep -c supersecreto123")
    ex("rm .github/workflows/secreto.yml")

    OUT.append("## 3 · Un solo trabajo, una sola combinación\n")
    ex("mv /otros/ci.yml .github/workflows/ci.yml")
    bloque("solo test, solo 3.13", "act push -j test --matrix version:3.13 …",
           f"act push {IMG} -W .github/workflows/ci.yml -j test --matrix version:3.13" + FILTRO)

    OUT.append("## 4 · Una action fijada a un commit completo\n")
    ex(f"mv .github/workflows/ci.yml /otros/ && cat > .github/workflows/fijado.yml <<'EOF'\n{FIJADO}EOF")
    bloque("el paso con el SHA", "grep uses: .github/workflows/fijado.yml", "grep uses: .github/workflows/fijado.yml")
    bloque("ejecutarlo", "act push …", f"act push {IMG} -W .github/workflows/fijado.yml" + FILTRO)
    ex("rm .github/workflows/fijado.yml && mv /otros/ci.yml .github/workflows/ci.yml")

    (AQUI / "SALIDA-extra.md").write_text("\n".join(OUT), encoding="utf-8")
    print("ok SALIDA-extra.md")


if __name__ == "__main__":
    main()
