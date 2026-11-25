# -*- coding: utf-8 -*-
"""Regenera todo el 704: imagen del banco, prueba del banco, generación (reanudable), ejecución, SALIDA.md y limpieza de Docker.
Lo ya generado en muestras/ no se vuelve a pedir a ninguna IA: para repetirlo desde cero, mueve muestras/ a _ARCHIVO/.

  python ejecutar_todo.py
"""
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))


def py(*a):
    subprocess.run([sys.executable, *a], cwd=AQUI, check=True, env={**os.environ, "PYTHONUTF8": "1"})


if __name__ == "__main__":
    subprocess.run(["docker", "build", "-q", "-t", "v704-runner", "-f", "Dockerfile.runner", "."], cwd=AQUI, check=True)
    py("referencia.py")
    py("-c", "import banco,sys; r=banco.ejecutar([('ref',n,f'referencia/{n}.sh') for n in range(1,51)]); "
             "m=[k for k,v in r.items() if not (v['control'][1] and v['espacios'][1])]; print('banco:', 50-len(m), '/50 referencias OK'); "
             "sys.exit(1 if m else 0)")
    # dos scripts sin comillas a propósito: tienen que pasar el control y fallar con espacios
    py("-c", "import banco; r=banco.ejecutar([('neg',1,'negativos/1.sh'),('neg',6,'negativos/6.sh')]); "
             "[print('neg', k[1], ' control:', 'OK' if v['control'][1] else 'FALLA', '  espacios:', 'OK' if v['espacios'][1] else v['espacios'][2][:70]) "
             "for k, v in sorted(r.items())]")
    for quien in ("qwen", "claude", "cruzado"):
        py("generar.py", quien)
    py("analizar.py")
    py("resumen.py")
    py("ejemplos.py")
    subprocess.run(["docker", "rmi", "v704-runner"], cwd=AQUI)
