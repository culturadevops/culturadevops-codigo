# -*- coding: utf-8 -*-
"""Demo de «GitHub Actions en 5 minutos» (cultura-devops). El workflow se ejecuta EN LOCAL con act (nektos/act v0.2.89)
dentro de un contenedor Alpine con el socket de Docker; los trabajos corren en node:22-bookworm-slim (la imagen
«micro» que propone act para ubuntu-latest). Nada se sube a GitHub; el secreto es inventado.
  · un workflow con matriz, un trabajo que depende de otro (needs) y un secreto;
  · ejecutarlo: los dos tests en paralelo, el despliegue después, el secreto enmascarado;
  · romper un test: el despliegue no corre.
    python correr.py   -> SALIDA.md
"""
import subprocess
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
ACT = "v0.2.89"
RUNNER = "node:22-bookworm-slim"
OUT = []
WF = """name: ci
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node: [20, 22]
    steps:
      - uses: actions/checkout@v4
      - name: tests
        run: |
          echo "probando con node ${{ matrix.node }}"
          test "$(cat precio.txt)" -gt 0 && echo "precio correcto"
  desplegar:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: desplegar
        env:
          CLAVE: ${{ secrets.CLAVE_DESPLIEGUE }}
        run: |
          echo "desplegando con la clave $CLAVE"
          echo "listo"
"""
FILTRO = ("grep -E \"Job succeeded|Job failed|probando|precio correcto|desplegando|listo|Success - |Failure - \" "
          "| sed 's/^.*\\] //' | sed 's/^ *| //'")


def run(args):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (p.stdout + p.stderr).strip(), p.returncode


def ex(cmd):
    return run(["docker", "exec", "-w", "/work", "act5", "sh", "-c", cmd])


def bloque(titulo, mostrado, cmd, nota=None):
    s, rc = ex(cmd)
    OUT.append(f"### {titulo}\n\n`$ {mostrado}`\n\n```\n{s}\n```\n(código de salida {rc})\n" + (f"\n> {nota}\n" if nota else ""))
    print(f"[{rc}] {titulo}")
    return s, rc


def main():
    run(["docker", "rm", "-f", "act5"])
    run(["docker", "pull", "-q", RUNNER])
    run(["docker", "run", "-d", "--name", "act5", "-v", "//var/run/docker.sock:/var/run/docker.sock", "alpine:3.22", "sh", "-c",
         "mkdir -p /work && sleep infinity"])
    ex("apk add -q curl git docker-cli >/dev/null && "
       f"curl -sL https://github.com/nektos/act/releases/download/{ACT}/act_Linux_x86_64.tar.gz | tar xz -C /usr/local/bin act")
    ex(f"mkdir -p .github/workflows && cat > .github/workflows/ci.yml <<'EOF'\n{WF}EOF\n"
       "echo 100 > precio.txt && git init -q && git config user.email a@b.c && git config user.name lab && git add -A && git commit -qm inicio")

    OUT.append(f"# SALIDA — GitHub Actions en 5 minutos (cultura-devops)\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con "
               f"`python correr.py`. act {ACT} con `-P ubuntu-latest={RUNNER}`; el secreto es inventado.\n")
    OUT.append("## 1 · El workflow\n")
    bloque("versión de act", "act --version", "act --version")
    bloque("el archivo", "cat .github/workflows/ci.yml", "cat .github/workflows/ci.yml")
    bloque("los trabajos y en qué orden", "act -l", "act -l")

    OUT.append("## 2 · Ejecutarlo\n")
    run_act = f"act push -P ubuntu-latest={RUNNER} -s CLAVE_DESPLIEGUE=s3cr3t0-de-prueba 2>&1 | {FILTRO}"
    bloque("un push", f"act push -s CLAVE_DESPLIEGUE=…", run_act,
           "El secreto aparece como *** en el registro.")

    OUT.append("## 3 · Un test falla\n")
    ex("echo 0 > precio.txt && git commit -qam 'precio a cero'")
    bloque("precio = 0", f"act push -s CLAVE_DESPLIEGUE=…", run_act, "El trabajo «desplegar» no aparece: depende de «test», que falló.")

    (AQUI / "SALIDA.md").write_text("\n".join(OUT), encoding="utf-8")
    run(["docker", "rm", "-f", "act5"])
    print("ok SALIDA.md")


if __name__ == "__main__":
    main()
