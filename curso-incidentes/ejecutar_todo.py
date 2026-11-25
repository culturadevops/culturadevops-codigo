# -*- coding: utf-8 -*-
"""Levanta el laboratorio limpio, provoca los 5 incidentes, escribe los postmortems y SALIDA.md.

La regla de la casa: nada de lo que sale en el vídeo se escribe a mano. Sale de aquí.
Hace falta Docker (con compose) y Python 3.10+. Tarda unos 12 minutos: las alertas esperan de
verdad (con los tiempos comprimidos que cuenta config/prometheus.yml).

    python ejecutar_todo.py            # y al terminar borra el laboratorio
    python ejecutar_todo.py --dejar
"""
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1", MSYS_NO_PATHCONV="1")

INCIDENTES = [
    ("1", "Se llenó el disco, y lo que falló fue otra cosa", "i1_disco_lleno.py"),
    ("2", "Una fuga de memoria que tarda días", "i2_fuga_de_memoria.py"),
    ("3", "El certificado que caducó un domingo", "i3_certificado.py"),
    ("4", "El despliegue que perdió peticiones a medias", "i4_despliegue.py"),
    ("5", "La consulta lenta que solo lo es en producción", "i5_consulta_lenta.py"),
]


def correr(cmd, cwd=AQUI, timeout=1500):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=ENV, timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    sello = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    print("  levantando el laboratorio limpio ...", flush=True)
    correr(["docker", "compose", "--profile", "certificado", "--profile", "despliegue", "down", "-v"])
    c, s = correr(["docker", "compose", "up", "-d", "--build", "--wait",
                   "tienda", "db", "loki", "prometheus", "alertmanager", "receptor"])
    if c != 0:
        raise SystemExit(f"el laboratorio no arranca:\n{s}")
    _, imgs = correr(["docker", "compose", "--profile", "certificado", "--profile", "despliegue", "config", "--images"])
    partes = ["# SALIDA — curso «Un incidente de principio a fin: romperlo, diagnosticarlo y el postmortem»", "",
              "> Generado por `ejecutar_todo.py`. **No se escribe a mano.** Los postmortems están en `postmortems/`.", "",
              f"- fecha: `{sello}` · anfitrión `{platform.system()} {platform.release()}`",
              "- tiempos comprimidos: Prometheus mide y evalúa cada 5 s; las alertas piden 10-15 s",
              *[f"- `{i}`" for i in sorted(set(imgs.split())) if "curso-incidentes" not in i], ""]
    fallos = 0
    for num, titulo, script in INCIDENTES:
        print(f"  [{num}] {titulo} ...", end=" ", flush=True)
        codigo, salida = correr([sys.executable, script], cwd=AQUI / "incidentes")
        fallos += codigo != 0
        partes += [f"## Incidente {num} — {titulo}", "", f"`python incidentes/{script}` · codigo de salida `{codigo}`",
                   "", "```", salida.strip("\n"), "```", ""]
        print("ok" if codigo == 0 else f"FALLO (codigo {codigo})")
    (AQUI / "SALIDA.md").write_text("\n".join(partes) + "\n", encoding="utf-8", newline="\n")
    if "--dejar" not in sys.argv:
        correr(["docker", "compose", "--profile", "certificado", "--profile", "despliegue", "down", "-v"])
    print(f"\n  -> SALIDA.md y postmortems/ regenerados (5 incidentes, {fallos} fallos)")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
