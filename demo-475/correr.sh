#!/usr/bin/env bash
# Demo del vídeo 475 «¿Debo aprender Python en la era de la IA?» — se EJECUTA y su salida va a SALIDA.md.
# El equivalente en Python a la demo del 455 (Go): un programa con dos fallos típicos de código generado
# (una variable que nadie usa y un texto que se trata como número). Python lo ejecuta hasta que revienta;
# ruff y mypy lo encuentran ANTES de ejecutarlo. Después, el arreglo. Y uv: un script con sus dependencias dentro.
# Entorno virtual propio en un directorio temporal: no instala nada en el sistema.
set -u
T=$(mktemp -d)
cd "$T"
python -m venv .venv >/dev/null 2>&1
. .venv/Scripts/activate 2>/dev/null || . .venv/bin/activate
pip install -q ruff==0.14.0 mypy==1.18.2 uv==0.9.2 >/dev/null 2>&1

cat > precios.py <<'EOF'
import sys


def con_impuesto(precio: int) -> float:
    return precio * 118 / 100


def main() -> None:
    total = 0
    precio = sys.argv[1]
    print("con impuesto:", con_impuesto(precio))


main()
EOF

echo '$ python --version'; python --version
echo '$ cat precios.py'; cat precios.py
echo
echo '$ python precios.py 100'
python precios.py 100 2>&1 | tail -3
echo "(código de salida: ${PIPESTATUS[0]})"
echo
echo '$ ruff check precios.py'
ruff check precios.py 2>&1 | grep -vE "^\s*$" | head -12
echo
echo '$ mypy precios.py'
mypy precios.py 2>&1
echo
# el arreglo: convertir el texto a número y quitar la variable que nadie usa
sed -i 's/    precio = sys.argv\[1\]/    precio = int(sys.argv[1])/; /    total = 0/d' precios.py
echo '$ # arreglo: int(sys.argv[1]) y fuera la variable sin usar'
echo '$ ruff check precios.py && mypy precios.py && python precios.py 100'
ruff check precios.py 2>&1 && mypy precios.py 2>&1 && python precios.py 100
echo

cat > resumen.py <<'EOF'
# /// script
# requires-python = ">=3.11"
# dependencies = ["rich==14.2.0"]
# ///
from rich.console import Console

Console().print("[bold]script con sus dependencias dentro[/bold]: listo")
EOF
echo '$ head -4 resumen.py'; head -4 resumen.py
echo '$ uv run resumen.py'
uv run -q resumen.py 2>&1
echo '$ ruff --version && mypy --version && uv --version'
ruff --version; mypy --version; uv --version
deactivate 2>/dev/null
cd / && rm -rf "$T"
