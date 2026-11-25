# -*- coding: utf-8 -*-
"""Corre las 12 lecciones y regenera SALIDA.md con la salida LITERAL de cada una.

La regla de la casa: nada de lo que se ve en el video se copia a mano. Sale de aqui.

    python ejecutar_todo.py
"""
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent

LECCIONES = [
    ("01", "Comillas: una palabra o cinco", "01_comillas/comillas.sh"),
    ("02", "set -euo pipefail: lo que arregla y lo que no", "02_modo_estricto/modo_estricto.sh"),
    ("03", "La variable vacia y rm -rf", "03_rm_rf/variable_vacia.sh"),
    ("04", "Codigos de salida y tuberias", "04_codigos/codigos_y_tuberias.sh"),
    ("05", "Comparar: [ ] contra [[ ]]", "05_comparar/comparar.sh"),
    ("06", "Leer un archivo linea a linea", "06_leer/leer_lineas.sh"),
    ("07", "Arrays y argumentos", "07_arrays/arrays.sh"),
    ("08", "Expansiones", "08_expansion/expansion.sh"),
    ("09", "trap y limpieza", "09_trap/trap_y_limpieza.sh"),
    ("10", "En paralelo, sin perder los codigos", "10_paralelo/en_paralelo.sh"),
    ("11", "#!/bin/sh no es bash", "11_portable/portable.sh"),
    ("12", "Proyecto: respaldo.sh", "12_proyecto/escenario.sh"),
]


# En Windows, "bash" a secas lo resuelve CreateProcess al bash de WSL, que no ve estas
# rutas. Se busca el bash del PATH de verdad y se llama por su ruta completa.
BASH = shutil.which("bash") or "bash"


def bash_version():
    r = subprocess.run([BASH, "-c", "echo $BASH_VERSION"], capture_output=True, text=True)
    return r.stdout.strip()


def correr(rel):
    entorno = dict(os.environ, PYTHONIOENCODING="utf-8")
    # stderr va MEZCLADO con stdout (no pegado al final): asi las trazas de set -x
    # y los mensajes de error salen en el orden en que ocurren, que es lo que se ve
    # al ejecutar el script a mano.
    r = subprocess.run([BASH, str(AQUI / rel)], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                       errors="replace", cwd=AQUI, env=entorno, timeout=300)
    return r.returncode, r.stdout or ""


def main():
    sello = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    partes = [
        "# SALIDA — curso «Bash para administradores»",
        "",
        "> Generado por `ejecutar_todo.py`. **No se escribe a mano.**",
        "",
        f"- fecha: `{sello}`",
        f"- bash: `{bash_version()}`",
        f"- sistema: `{platform.system()} {platform.release()}`",
        "",
    ]
    fallos = 0
    for num, titulo, rel in LECCIONES:
        print(f"  [{num}] {titulo} ...", end=" ", flush=True)
        codigo, salida = correr(rel)
        esperado = 0
        ok = codigo == esperado
        print("ok" if ok else f"FALLO (codigo {codigo})")
        if not ok:
            fallos += 1
        partes += [f"## Leccion {num} — {titulo}", "",
                   f"`{rel}` · codigo de salida `{codigo}`", "",
                   "```", salida.rstrip(), "```", ""]

    (AQUI / "SALIDA.md").write_text("\n".join(partes), encoding="utf-8")
    print(f"\n  -> SALIDA.md regenerado ({len(LECCIONES)} lecciones, {fallos} fallos)")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
