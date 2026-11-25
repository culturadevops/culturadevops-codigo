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
    ("01", "subprocess: el comando fallo y seguiste", "01_subprocess/ejecutar_comandos.py"),
    ("02", "Dry-run: un simulacro que simule", "02_dry_run/simulacro.py"),
    ("03", "Idempotencia: se va a ejecutar dos veces", "03_idempotencia/dos_veces.py"),
    ("04", "Escritura atomica", "04_atomico/escribir_sin_romper.py"),
    ("05", "Reintentos: cuales, cuantos y cuanto esperar", "05_reintentos/reintentar_bien.py"),
    ("06", "Timeouts: por defecto, para siempre", "06_timeouts/sin_limite.py"),
    ("07", "Health check: que conteste TU version", "07_salud/comprobar_salud.py"),
    ("08", "Marcha atras", "08_marcha_atras/volver_atras.py"),
    ("09", "Cerrojo: uno a la vez", "09_cerrojo/uno_a_la_vez.py"),
    ("10", "Configuracion y secretos", "10_secretos/config_y_secretos.py"),
    ("11", "Codigos de salida y logs", "11_salida/codigos_de_salida.py"),
    ("12", "Proyecto: desplegar.py", "12_proyecto/escenario.py"),
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
        "# SALIDA — curso «Python para automatizar despliegues»",
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
