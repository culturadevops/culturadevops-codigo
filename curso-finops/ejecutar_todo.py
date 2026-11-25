# -*- coding: utf-8 -*-
"""Corre las 6 lecciones del curso de FinOps y regenera SALIDA.md.

La regla de la casa: nada de lo que sale en el vídeo se escribe a mano. Sale de aquí.
Hace falta Python 3.10+ con boto3 y moto[server], y OpenTofu (lección 6). No hace falta cuenta de
AWS: todo corre contra moto, y los precios salen de la lista pública (precios/, FUENTES.md).

    python ejecutar_todo.py
"""
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
LECCIONES = [
    ("01", "El plan gratuito ya no es un año: son créditos", "l01_plan_gratuito.py"),
    ("02", "El presupuesto, por código, y lo que no hace", "l02_presupuesto.py"),
    ("03", "Etiquetar: ¿de quién es este gasto?", "l03_etiquetas.py"),
    ("04", "Lo que sigue cobrando cuando crees que borraste todo", "l04_lo_que_sigue_cobrando.py"),
    ("05", "Pagar por hora o por petición", "l05_hora_o_peticion.py"),
    ("06", "El guion de destrucción, y lo que no destruye", "l06_destruir.py"),
]


def version(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, env=ENV)
    return (r.stdout or r.stderr).strip().splitlines()[0]


def main():
    sello = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    sys.path.insert(0, str(AQUI))
    import precios as PR
    import boto3
    import moto
    libs = f"moto {moto.__version__} · boto3 {boto3.__version__}"
    partes = ["# SALIDA — curso «La factura: FinOps para el que paga de su bolsillo»", "",
              "> Generado por `ejecutar_todo.py`. **No se escribe a mano.** Importes: precio de lista × uso (estimación).", "",
              f"- fecha: `{sello}` · anfitrión `{platform.system()} {platform.release()}`",
              f"- precios: {PR.fuentes()}",
              f"- `{libs}`",
              f"- `{version(['tofu', 'version'])}`", ""]
    fallos = 0
    for num, titulo, script in LECCIONES:
        print(f"  [{num}] {titulo} ...", end=" ", flush=True)
        r = subprocess.run([sys.executable, str(AQUI / "lecciones" / script)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=ENV, timeout=900)
        fallos += r.returncode != 0
        partes += [f"## Leccion {num} — {titulo}", "", f"`python lecciones/{script}` · codigo de salida `{r.returncode}`",
                   "", "```", (r.stdout + r.stderr).strip("\n"), "```", ""]
        print("ok" if r.returncode == 0 else f"FALLO (codigo {r.returncode})")
    (AQUI / "SALIDA.md").write_text("\n".join(partes) + "\n", encoding="utf-8", newline="\n")
    print(f"\n  -> SALIDA.md regenerado (6 lecciones, {fallos} fallos)")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
