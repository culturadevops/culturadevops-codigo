# SALIDA · 715 · 5 cambios en Python que están pasando ahora (2026), medidos

Generado por `ejecutar_todo.py` el 2026-10-30. Máquina: Windows 11 + Docker Desktop (WSL2, 24 hilos lógicos); cada banco con `--cpus` fijo. Mediana de 3 repeticiones con el orden de los lados intercalado. Muestras pequeñas: es una medición en una máquina, no un estudio.

## 1 · Free-threaded (sin GIL), Python 3.14.10

Imagen `v715-banco:1` = `python:3.14.10-slim-trixie` + uv 0.13.6, y por uv las dos builds de CPython 3.14.10 del mismo proyecto (python-build-standalone): `3.14.10` (con GIL) y `3.14.10t` (free-threaded). Tercer lado: el MISMO binario `3.14.10t` con `PYTHON_GIL=1`. Trabajos (`bancos/hilos.py`): `primos` = contar primos hasta 3.000.000 en Python puro; `json` = `json.loads` de 400.000 líneas de log y contar los estados 500. El resultado es el mismo en todos los lados (se comprueba abajo).

### --cpus 2

| trabajo | lado | 1 hilo (s) | 2 hilos (s) | 4 hilos (s) | 4 hilos frente a 1 |
|---|---|---|---|---|---|
| primos | 3.14 con GIL | 3.72 | 3.73 | 3.77 | ×0.99 |
| primos | 3.14t sin GIL | 4.07 | 2.21 | 2.07 | ×1.97 |
| primos | 3.14t con PYTHON_GIL=1 | 4.08 | 4.12 | 4.12 | ×0.99 |
| json | 3.14 con GIL | 0.26 | 0.26 | 0.27 | ×0.96 |
| json | 3.14t sin GIL | 0.3 | 0.2 | 0.23 | ×1.3 |
| json | 3.14t con PYTHON_GIL=1 | 0.3 | 0.3 | 0.3 | ×1.0 |

Resultados distintos por trabajo: [('json', 66666), ('primos', 216816)] (uno por trabajo = los lados hicieron lo mismo). GIL activo según `sys._is_gil_enabled()`: [('3.14 con GIL', True), ('3.14t con PYTHON_GIL=1', True), ('3.14t sin GIL', False)].

### --cpus 4

| trabajo | lado | 1 hilo (s) | 2 hilos (s) | 4 hilos (s) | 4 hilos frente a 1 |
|---|---|---|---|---|---|
| primos | 3.14 con GIL | 3.73 | 3.74 | 3.73 | ×1.0 |
| primos | 3.14t sin GIL | 4.04 | 2.18 | 1.14 | ×3.54 |
| primos | 3.14t con PYTHON_GIL=1 | 4.05 | 4.09 | 4.12 | ×0.98 |
| json | 3.14 con GIL | 0.26 | 0.26 | 0.26 | ×1.0 |
| json | 3.14t sin GIL | 0.3 | 0.22 | 0.14 | ×2.14 |
| json | 3.14t con PYTHON_GIL=1 | 0.3 | 0.3 | 0.3 | ×1.0 |

Resultados distintos por trabajo: [('json', 66666), ('primos', 216816)] (uno por trabajo = los lados hicieron lo mismo). GIL activo según `sys._is_gil_enabled()`: [('3.14 con GIL', True), ('3.14t con PYTHON_GIL=1', True), ('3.14t sin GIL', False)].


## 2 · pip frente a uv: el mismo requirements.txt

`bancos/requirements.in` (12 dependencias directas de automatización) → `uv pip compile --exclude-newer 2026-10-29` → `requirements.txt` con 56 paquetes y versión exacta. Los dos instalan ese archivo, en un venv nuevo (`python -m venv --without-pip`) sobre el python oficial 3.14.10, `--cpus 2`. pip 26.2.2 (`--python`); uv 0.13.6 con `--compile-bytecode` porque pip compila los .pyc por defecto. Frío = caché vacía, descarga de PyPI por la red de casa; caliente = venv nuevo con la caché de la vuelta anterior.

| lado | frío (s) | caliente (s) | paquetes | .pyc |
|---|---|---|---|---|
| pip | 19.81 | 12.58 | 56 | 6047 |
| uv | 10.07 | 5.04 | 56 | 6046 |
| uv sin compilar | 5.21 | 0.12 | 56 | 0 |

Tiempos de cada vuelta: pip r0: 19.86 / 12.58; uv r0: 10.07 / 5.04; uv sin compilar r0: 5.18 / 0.12; uv sin compilar r1: 5.22 / 0.12; uv r1: 10.1 / 5.17; pip r1: 19.15 / 12.46; pip r2: 19.81 / 12.7; uv r2: 10.05 / 5.01; uv sin compilar r2: 5.21 / 0.12

Listas instaladas (`uv pip freeze`) distintas entre todos los lados y vueltas: 1 (1 = instalaron exactamente lo mismo). Frío y caliente iguales: True.

## 3 · pylock.toml (PEP 751): uv lo escribe, pip lo instala

```
$ uv --version
uv 0.13.6 (x86_64-unknown-linux-gnu)
$ python -m pip --version
pip 26.2.2
$ uv add requests==2.34.2 pyyaml==6.0.3
$ uv export --format pylock.toml -o pylock.toml
$ head -12 pylock.toml
lock-version = "1.0"
created-by = "uv"
requires-python = ">=3.14"

[[packages]]
name = "certifi"
version = "2026.10.23"
index = "https://pypi.org/simple"
sdist = { url = "https://files.pythonhosted.org/packages/fd/11/b524cbd9bbdaca58608e4cf4053fd463417549e1959fa8d3aa18319f9555/certifi-2026.10.23.tar.gz", upload-time = 2026-10-23T11:36:16Z, size = 136225, hashes = { sha256 = "a9895e6e2758b371e0545e321a3a8fd1fcfd9829ada8824a936dfb16aaaf36cd" } }
wheels = [{ url = "https://files.pythonhosted.org/packages/32/d1/a3652fe2c19134d0d15922177821d863cbd7e842d53a21bbe7e8e3a1b5ac/certifi-2026.10.23-py3-none-any.whl", upload-time = 2026-10-23T11:36:14Z, size = 135082, hashes = { sha256 = "e9b54de76e530bb6cf0ccd036787103acb58fd42ba930ea8bf948ddbaa2f61d1" } }]

[[packages]]
paquetes en el lock: 6 · hashes sha256: 114
$ pip install -r pylock.toml
WARNING: Using pylock.toml as a requirements source is an experimental feature. It may be removed/changed in a future release without prior warning.
# exit=0
$ pip freeze
certifi==2026.10.23
charset-normalizer==3.5.2
idna==3.20
PyYAML==6.0.3
requests==2.34.2
urllib3==2.8.0
$ pip install -r pylock.toml   # con un carácter cambiado en el hash de requests
WARNING: Using pylock.toml as a requirements source is an experimental feature. It may be removed/changed in a future release without prior warning.
ERROR: THESE PACKAGES DO NOT MATCH THE HASHES FROM THE REQUIREMENTS FILE. If you have updated the package versions, please update the hashes. Otherwise, examine the package contents carefully; someone may have tampered with them.
    requests==2.34.2 from https://files.pythonhosted.org/packages/a0/f4/c67b0b3f1b9245e8d266f0f112c500d50e5b4e83cb6f3b71b6528104182a/requests-2.34.2-py3-none-any.whl (from pylock.toml):
        Expected sha256 0a0d60c172f83ac6ab31e4554906c0f3b3588d37b5cb939b1c061f4907e278e0
             Got        2a0d60c172f83ac6ab31e4554906c0f3b3588d37b5cb939b1c061f4907e278e0
# exit=1
$ pip lock requests==2.34.2 -o pylock.pip.toml   # pip también lo escribe (experimental)
WARNING: pip lock is currently an experimental command. It may be removed/changed in a future release without prior warning.
lock-version = "1.0"
created-by = "pip"
```

## 4 · ruff frente a flake8 + isort, y ty frente a mypy

Código: biblioteca estándar de Python 3.14.10 sin `test` ni `site-packages`: 655 archivos .py, 321593 líneas. Tipos: fuente de rich 15.0.0 (100 archivos, 38515 líneas). `--cpus 2`, dos hilos o procesos por herramienta, sin caché. Versiones: ruff: ruff 0.17.3; flake8: 7.5.0 (mccabe: 0.7.0, pycodestyle: 2.15.0, pyflakes: 4.1.0) CPython 3.14.10 on; isort: VERSION 9.0.2 (compiled yes); mypy: mypy 2.4.1 (compiled: yes); ty: ty 0.0.95.

| herramienta | segundos (mediana) | líneas de salida | última línea |
|---|---|---|---|
| flake8 | 6.58 | 44172 | `/tmp/code/zoneinfo/_zoneinfo.py:729:80: E501 line too long (83 > 79 characters)` |
| isort | 0.69 | 408 | `ERROR: /tmp/code/html/parser.py Imports are incorrectly sorted and/or formatted.` |
| ruff | 0.2 | 44617 | `[*] 38703 fixable with `--fix` (214 unsafe fixes available with `--fix --unsafe-fixes`).` |
| mypy | 0.9 | 5 | `Found 2 errors in 2 files (checked 100 source files)` |
| ty | 0.19 | 44 | `Found 43 diagnostics` |

Comandos exactos en `bancos/matriz_lint.py`. Los conteos no coinciden uno a uno: no es la misma implementación de las reglas (ruff reimplementa pycodestyle, pyflakes e isort; ty y mypy no tienen las mismas reglas; mypy lee la configuración de rich, `strict = true` en su pyproject.toml, y ty usa la suya por defecto). Se compara el tiempo de revisar el mismo código. Totales: flake8 + isort = 7.27 s.

## 5 · Python 3.15: lazy import y UTF-8 por defecto; 3.14: t-strings

### lazy import (PEP 810), `python:3.15.2-slim-trixie`, `--cpus 2`, boto3 1.43.121

Arranque de `mi-cli --version`: mediana de 21 ejecuciones (`bancos/py315/medir_lazy.py`). Los dos archivos solo se diferencian en la palabra `lazy`.

| caso | ms | salida |
|---|---|---|
| python -c pass | 6.8 | `` |
| import boto3 | 134.8 | `mi-cli 1.0 · boto3 cargado: True` |
| lazy import boto3 | 10.4 | `mi-cli 1.0 · boto3 cargado: False` |
| import boto3 + -X lazy_imports=all | 10.4 | `mi-cli 1.0 · boto3 cargado: False` |

### t-strings (PEP 750) y `lazy` en 3.14

```
Python 3.14.10 (main, Oct 28 2026, 01:59:47) [GCC 14.2.0]
f-string : cat informe.txt; rm -rf /tmp/x
tipo     : Template
strings  : ('cat ', '')
valores  : ('informe.txt; rm -rf /tmp/x',)
t-string : cat 'informe.txt; rm -rf /tmp/x'
$ python3.14 -c "lazy import json"
SyntaxError: invalid syntax
```

### UTF-8 por defecto (PEP 686), en Windows 11, el mismo script con 3.14.10 y 3.15.2 (de uv 0.13.6)

```
Python 3.14.10 · utf8_mode=0 · open() usa cp1252
bytes escritos: b'a\xf1o=2026\r\n'
leído como UTF-8: UnicodeDecodeError: invalid continuation byte
Python 3.15.2 · utf8_mode=1 · open() usa utf-8
bytes escritos: b'a\xc3\xb1o=2026\r\n'
leído como UTF-8: año=2026
```

## Fuentes (consultadas el 2026-10-30)

- What's New in Python 3.14 (publicado el 7 de octubre de 2025): https://docs.python.org/3.14/whatsnew/3.14.html — «Free-threaded Python is officially supported»; penalización en un hilo «roughly 5-10%».
- PEP 779 (Final, 16-jun-2025): free-threaded «officially supported but still optional»: https://peps.python.org/pep-0779/
- What's New in Python 3.15 (publicado el 9 de octubre de 2026): https://docs.python.org/3/whatsnew/3.15.html
- PEP 810 lazy imports: https://peps.python.org/pep-0810/ · PEP 686 UTF-8: https://peps.python.org/pep-0686/ · PEP 750 t-strings: https://peps.python.org/pep-0750/
- PEP 751 (Final, aceptada el 31-mar-2025): https://peps.python.org/pep-0751/
- pip: `pip lock` experimental desde 25.1 (2025-04-26); `-r pylock.toml` experimental desde 26.1 (2026-04-26): https://pip.pypa.io/en/stable/news/
- uv export --format pylock.toml: https://docs.astral.sh/uv/concepts/projects/export/
- ruff: https://docs.astral.sh/ruff/ · ty (beta): https://docs.astral.sh/ty/
- 707 (paquetes inventados por la IA): canales/cultura-devops/recursos/ia-paquetes-python-inventados/SALIDA.md
