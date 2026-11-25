# -*- coding: utf-8 -*-
"""Corre las 12 lecciones y regenera SALIDA.md con la salida LITERAL de cada una.

La regla de la casa: nada de lo que se ve en el video se copia a mano. Sale de aqui.

    python ejecutar_todo.py
"""
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent

LECCIONES = [
    ("01", "El interprete y el entorno", "01_entorno/comprobar_entorno.py"),
    ("02", "Tipos: mutable contra inmutable", "02_tipos/mutable_vs_inmutable.py"),
    ("03", "Cadenas, f-strings y bytes", "03_cadenas/formatear_y_bytes.py"),
    ("04", "Colecciones: cual y por que", "04_colecciones/elegir_coleccion.py"),
    ("05", "Flujo y bucles sin romper nada", "05_flujo/recorrer_sin_romper.py"),
    ("06", "Funciones y el mutable por omision", "06_funciones/argumento_mutable.py"),
    ("07", "Ficheros, rutas y codificacion", "07_ficheros/rutas_y_encoding.py"),
    ("08", "Errores y excepciones", "08_errores/excepciones.py"),
    ("09", "Modulos e imports", "09_modulos/usar_modulo.py"),
    ("10", "La biblioteca estandar de DevOps", "10_stdlib/la_caja_de_herramientas.py"),
    ("11", "Clases, lo justo", "11_clases/cuando_una_clase.py"),
    ("12", "Proyecto: un script para una tuberia", "12_proyecto/revisar_servicios.py"),
]


def correr(rel):
    entorno = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, str(AQUI / rel)], capture_output=True,
                       text=True, encoding="utf-8", errors="replace",
                       cwd=AQUI, env=entorno, timeout=300)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    sello = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    partes = [
        "# SALIDA — curso «Python para DevOps desde cero»",
        "",
        "> Generado por `ejecutar_todo.py`. **No se escribe a mano.**",
        "",
        f"- fecha: `{sello}`",
        f"- Python: `{platform.python_version()}`",
        f"- sistema: `{platform.system()} {platform.release()}`",
        "",
    ]
    fallos = 0
    for num, titulo, rel in LECCIONES:
        print(f"  [{num}] {titulo} ...", end=" ", flush=True)
        codigo, salida = correr(rel)
        # La 12 sale con 1 a proposito: encuentra servicios con problemas.
        esperado = 1 if num == "12" else 0
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
