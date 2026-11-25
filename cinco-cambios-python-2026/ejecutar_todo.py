# -*- coding: utf-8 -*-
"""715 · 5 cambios en Python (2026), medidos. Regenera medidas/ y SALIDA.md.

  python ejecutar_todo.py               # todo: imagen, bancos en Docker (de uno en uno), demo de Windows y SALIDA.md
  python ejecutar_todo.py --solo-salida # rehace SALIDA.md con lo que ya hay en medidas/

Docker: --rm siempre, nombres v715-*, --cpus 2 o 4 al medir. Al terminar: docker rmi v715-banco:1.
La demo de UTF-8 corre en Windows con los Python de uv (UV_PYTHON_INSTALL_DIR en una carpeta temporal; ver PY_WIN abajo).
"""
import json
import os
import pathlib
import statistics
import subprocess
import sys
import datetime

AQUI = pathlib.Path(__file__).parent
B = AQUI / "bancos"
M = AQUI / "medidas"
VOL = f"{B.as_posix()}:/banco:ro"
PY_WIN = os.environ.get("V715_PY_WIN", "")  # carpeta con cpython-3.14.10-windows* y cpython-3.15.2-windows*


def docker(nombre, args, salida, cpus=None, img="v715-banco:1", vol=VOL, wd="/banco"):
    c = ["docker", "run", "--rm", "--name", f"v715-{nombre}", "-v", vol, "-w", wd]
    c += ["--cpus", str(cpus)] if cpus else []
    with open(M / salida, "w", encoding="utf-8") as f:
        subprocess.run(c + [img] + args, stdout=f, stderr=subprocess.STDOUT, check=True,
                       env={**os.environ, "MSYS_NO_PATHCONV": "1"})


def medir():
    M.mkdir(exist_ok=True)
    subprocess.run(["docker", "build", "-q", "-t", "v715-banco:1", str(B)], check=True)
    for c in (2, 4):
        docker(f"hilos-{c}", ["python", "matriz_hilos.py", str(c)], f"hilos_cpus{c}.jsonl", cpus=c)
    docker("instalar", ["python", "matriz_instalar.py"], "instalar.jsonl", cpus=2)
    docker("lint", ["python", "matriz_lint.py"], "lint.jsonl", cpus=2)
    docker("pylock", ["sh", "/banco/pylock_demo.sh"], "pylock.txt")
    v315 = f"{(B / 'py315').as_posix()}:/d:ro"
    docker("py315", ["sh", "-c", "python -VV; pip install -q --root-user-action=ignore --disable-pip-version-check boto3==1.43.121 "
                     "&& python medir_lazy.py"], "lazy.jsonl", cpus=2, img="python:3.15.2-slim-trixie", vol=v315, wd="/d")
    docker("tstr", ["sh", "-c", "python -VV; python tstrings.py; echo '$ python3.14 -c \"lazy import json\"'; "
                    "python -c 'lazy import json' 2>&1 | tail -1"], "tstrings.txt", vol=v315, wd="/d")
    if PY_WIN:
        with open(M / "utf8_windows.txt", "w", encoding="utf-8") as f:
            for v in ("3.14.10", "3.15.2"):
                exe = next(pathlib.Path(PY_WIN).glob(f"cpython-{v}-windows*")) / "python.exe"
                subprocess.run([str(exe), "-I", str(B / "py315" / "utf8_windows.py")], stdout=f, check=True,
                               env={**os.environ, "PYTHONIOENCODING": "utf-8"})


def jl(nombre):
    return [json.loads(l) for l in (M / nombre).read_text(encoding="utf-8").splitlines() if l.startswith("{")]


def med(xs):
    return round(statistics.median(xs), 2)


def salida():
    L = []
    w = L.append
    w("# SALIDA · 715 · 5 cambios en Python que están pasando ahora (2026), medidos")
    w(f"\nGenerado por `ejecutar_todo.py` el {datetime.date.today().isoformat()}. Máquina: Windows 11 + Docker Desktop "
      "(WSL2, 24 hilos lógicos); cada banco con `--cpus` fijo. Mediana de 3 repeticiones con el orden de los lados intercalado. "
      "Muestras pequeñas: es una medición en una máquina, no un estudio.")

    w("\n## 1 · Free-threaded (sin GIL), Python 3.14.10\n")
    w("Imagen `v715-banco:1` = `python:3.14.10-slim-trixie` + uv 0.13.6, y por uv las dos builds de CPython 3.14.10 del mismo "
      "proyecto (python-build-standalone): `3.14.10` (con GIL) y `3.14.10t` (free-threaded). Tercer lado: el MISMO binario "
      "`3.14.10t` con `PYTHON_GIL=1`. Trabajos (`bancos/hilos.py`): `primos` = contar primos hasta 3.000.000 en Python puro; "
      "`json` = `json.loads` de 400.000 líneas de log y contar los estados 500. El resultado es el mismo en todos los lados "
      "(se comprueba abajo).\n")
    for c in (2, 4):
        filas = jl(f"hilos_cpus{c}.jsonl")
        res = {(f["modo"], f["resultado"]) for f in filas}
        w(f"### --cpus {c}\n")
        w("| trabajo | lado | 1 hilo (s) | 2 hilos (s) | 4 hilos (s) | 4 hilos frente a 1 |")
        w("|---|---|---|---|---|---|")
        for modo in ("primos", "json"):
            for lado in ("3.14 con GIL", "3.14t sin GIL", "3.14t con PYTHON_GIL=1"):
                t = {h: med([f["seg"] for f in filas if f["modo"] == modo and f["lado"] == lado and f["hilos"] == h]) for h in (1, 2, 4)}
                w(f"| {modo} | {lado} | {t[1]} | {t[2]} | {t[4]} | ×{round(t[1] / t[4], 2)} |")
        gil = {(f["lado"], f["gil"]) for f in filas}
        w(f"\nResultados distintos por trabajo: {sorted(res)} (uno por trabajo = los lados hicieron lo mismo). "
          f"GIL activo según `sys._is_gil_enabled()`: {sorted(gil)}.\n")

    w("\n## 2 · pip frente a uv: el mismo requirements.txt\n")
    pins = [l for l in (B / "requirements.txt").read_text(encoding="utf-8").splitlines() if "==" in l]
    w(f"`bancos/requirements.in` (12 dependencias directas de automatización) → `uv pip compile --exclude-newer 2026-10-29` → "
      f"`requirements.txt` con {len(pins)} paquetes y versión exacta. Los dos instalan ese archivo, en un venv nuevo "
      "(`python -m venv --without-pip`) sobre el python oficial 3.14.10, `--cpus 2`. pip 26.2.2 (`--python`); uv 0.13.6 con "
      "`--compile-bytecode` porque pip compila los .pyc por defecto. Frío = caché vacía, descarga de PyPI por la red de casa; "
      "caliente = venv nuevo con la caché de la vuelta anterior.\n")
    filas = jl("instalar.jsonl")
    w("| lado | frío (s) | caliente (s) | paquetes | .pyc |")
    w("|---|---|---|---|---|")
    for lado in ("pip", "uv", "uv sin compilar"):
        fs = [f for f in filas if f["lado"] == lado]
        w(f"| {lado} | {med([f['frio'] for f in fs])} | {med([f['caliente'] for f in fs])} | {fs[0]['paquetes']} | {fs[0]['pyc']} |")
    w(f"\nTiempos de cada vuelta: " + "; ".join(f"{f['lado']} r{f['rep']}: {f['frio']} / {f['caliente']}" for f in filas))
    listas = {json.dumps(f["lista"]) for f in filas}
    w(f"\nListas instaladas (`uv pip freeze`) distintas entre todos los lados y vueltas: {len(listas)} "
      f"(1 = instalaron exactamente lo mismo). Frío y caliente iguales: {all(f['igual_frio_caliente'] for f in filas)}.")

    w("\n## 3 · pylock.toml (PEP 751): uv lo escribe, pip lo instala\n")
    w("```\n" + (M / "pylock.txt").read_text(encoding="utf-8").strip() + "\n```")

    w("\n## 4 · ruff frente a flake8 + isort, y ty frente a mypy\n")
    filas = jl("lint.jsonl")
    info = next(f for f in filas if f.get("info") == "codigo")
    vers = {f["caso"]: f["v"] for f in filas if f.get("info") == "version"}
    w(f"Código: biblioteca estándar de Python 3.14.10 sin `test` ni `site-packages`: {info['archivos']} archivos .py, "
      f"{info['lineas']} líneas. Tipos: fuente de rich 15.0.0 ({info['rich_archivos']} archivos, {info['rich_lineas']} líneas). "
      "`--cpus 2`, dos hilos o procesos por herramienta, sin caché. Versiones: "
      + "; ".join(f"{k}: {' '.join(v)}" for k, v in vers.items()) + ".\n")
    w("| herramienta | segundos (mediana) | líneas de salida | última línea |")
    w("|---|---|---|---|")
    for k in ("flake8", "isort", "ruff", "mypy", "ty"):
        fs = [f for f in filas if f.get("caso") == k and "seg" in f]
        w(f"| {k} | {med([f['seg'] for f in fs])} | {fs[0]['lineas_salida']} | `{(fs[0]['cola'] or [''])[-1][:110]}` |")
    w("\nComandos exactos en `bancos/matriz_lint.py`. Los conteos no coinciden uno a uno: no es la misma implementación de las "
      "reglas (ruff reimplementa pycodestyle, pyflakes e isort; ty y mypy no tienen las mismas reglas; mypy lee la configuración de rich, `strict = true` en su pyproject.toml, y ty "
      "usa la suya por defecto). Se compara el tiempo de revisar el mismo código. Totales: flake8 + isort = "
      f"{round(med([f['seg'] for f in filas if f.get('caso') == 'flake8' and 'seg' in f]) + med([f['seg'] for f in filas if f.get('caso') == 'isort' and 'seg' in f]), 2)} s.")

    w("\n## 5 · Python 3.15: lazy import y UTF-8 por defecto; 3.14: t-strings\n")
    w("### lazy import (PEP 810), `python:3.15.2-slim-trixie`, `--cpus 2`, boto3 1.43.121\n")
    w("Arranque de `mi-cli --version`: mediana de 21 ejecuciones (`bancos/py315/medir_lazy.py`). Los dos archivos solo se "
      "diferencian en la palabra `lazy`.\n")
    w("| caso | ms | salida |")
    w("|---|---|---|")
    for f in jl("lazy.jsonl"):
        w(f"| {f['caso']} | {f['ms']} | `{f['salida']}` |")
    w("\n### t-strings (PEP 750) y `lazy` en 3.14\n")
    w("```\n" + (M / "tstrings.txt").read_text(encoding="utf-8").strip() + "\n```")
    if (M / "utf8_windows.txt").exists():
        w("\n### UTF-8 por defecto (PEP 686), en Windows 11, el mismo script con 3.14.10 y 3.15.2 (de uv 0.13.6)\n")
        w("```\n" + (M / "utf8_windows.txt").read_text(encoding="utf-8").strip() + "\n```")

    w("\n## Fuentes (consultadas el 2026-10-30)\n")
    for s in ("What's New in Python 3.14 (publicado el 7 de octubre de 2025): https://docs.python.org/3.14/whatsnew/3.14.html — "
              "«Free-threaded Python is officially supported»; penalización en un hilo «roughly 5-10%».",
              "PEP 779 (Final, 16-jun-2025): free-threaded «officially supported but still optional»: https://peps.python.org/pep-0779/",
              "What's New in Python 3.15 (publicado el 9 de octubre de 2026): https://docs.python.org/3/whatsnew/3.15.html",
              "PEP 810 lazy imports: https://peps.python.org/pep-0810/ · PEP 686 UTF-8: https://peps.python.org/pep-0686/ · "
              "PEP 750 t-strings: https://peps.python.org/pep-0750/",
              "PEP 751 (Final, aceptada el 31-mar-2025): https://peps.python.org/pep-0751/",
              "pip: `pip lock` experimental desde 25.1 (2025-04-26); `-r pylock.toml` experimental desde 26.1 (2026-04-26): "
              "https://pip.pypa.io/en/stable/news/",
              "uv export --format pylock.toml: https://docs.astral.sh/uv/concepts/projects/export/",
              "ruff: https://docs.astral.sh/ruff/ · ty (beta): https://docs.astral.sh/ty/",
              "707 (paquetes inventados por la IA): canales/cultura-devops/recursos/ia-paquetes-python-inventados/SALIDA.md"):
        w(f"- {s}")
    (AQUI / "SALIDA.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("SALIDA.md escrito")


if __name__ == "__main__":
    if "--solo-salida" not in sys.argv:
        medir()
    salida()
