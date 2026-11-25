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
    ("01", "Leer sin cargar el log entero", "01_memoria/leer_sin_cargar.py"),
    ("02", "Partir la linea (y contar lo que se descarta)", "02_parsear/partir_la_linea.py"),
    ("03", "Horas, UTC y zonas", "03_tiempo/horas_y_zonas.py"),
    ("04", "Contar: 3.000 errores que son tres", "04_contar/agrupar_mensajes.py"),
    ("05", "Ventanas: la media de la hora miente", "05_ventanas/la_media_miente.py"),
    ("06", "Correlacionar dos logs", "06_correlacionar/dos_fuentes.py"),
    ("07", "Percentiles", "07_percentiles/la_media_no_sirve.py"),
    ("08", "Logs en JSON rotos", "08_json/logs_json.py"),
    ("09", "Rotados y comprimidos", "09_rotados/ficheros_rotados.py"),
    ("10", "Solo el final de un log enorme", "10_final/solo_el_final.py"),
    ("11", "Muestreo: no te mientas", "11_muestreo/no_te_mientas.py"),
    ("12", "Proyecto: triaje.py", "12_proyecto/escenario.py"),
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
        "# SALIDA — curso «Python para la guardia»",
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
