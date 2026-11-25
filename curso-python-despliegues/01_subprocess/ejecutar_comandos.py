# -*- coding: utf-8 -*-
"""Leccion 1 — subprocess: el comando fallo y tu script siguio como si nada."""
import subprocess
import sys
import time

PY = [sys.executable, "-c"]
sys.stdout.reconfigure(line_buffering=True)   # que lo nuestro salga en orden con lo del hijo

print("== 1.1 · LA TRAMPA: run() sin check=True no se queja ==")
r = subprocess.run(PY + ["import sys; print('compilando...'); sys.exit(3)"])
print(f"  codigo de salida del comando: {r.returncode}")
print("  y el script sigue: 'desplegado con exito'   <- mentira")

print()
print("== 1.2 · check=True: si falla, se para ==")
try:
    subprocess.run(PY + ["import sys; sys.exit(3)"], check=True)
    print("  desplegado con exito")
except subprocess.CalledProcessError as e:
    print(f"  CalledProcessError: codigo {e.returncode}. No se despliega.")

print()
print("== 1.3 · LA TRAMPA: shell=True con un dato que viene de fuera ==")
rama = "main & echo INYECTADO"
print(f"  rama = {rama!r}")
r = subprocess.run(f"echo desplegando {rama}", shell=True,
                   capture_output=True, text=True)
for linea in r.stdout.splitlines():
    print(f"  shell=True  -> {linea.strip()}")
r = subprocess.run(PY + ["import sys; print('argumentos:', sys.argv[1:])", rama],
                   capture_output=True, text=True)
print(f"  lista       -> {r.stdout.strip()}")
print("  Con lista no hay shell: el dato llega entero, como UN argumento.")

print()
print("== 1.4 · Un comando colgado cuelga tu despliegue: timeout ==")
t0 = time.perf_counter()
try:
    subprocess.run(PY + ["import time; time.sleep(30)"], timeout=1)
except subprocess.TimeoutExpired:
    print(f"  TimeoutExpired a los {time.perf_counter() - t0:.1f} s (sin timeout: 30 s, o nunca)")

print()
print("== 1.5 · El motivo del fallo esta en stderr ==")
r = subprocess.run(PY + ["import sys; print('paso 1 ok'); "
                         "sys.stderr.write('error: disco lleno\\n'); sys.exit(1)"],
                   capture_output=True, text=True)
print(f"  stdout: {r.stdout.strip()!r}")
print(f"  stderr: {r.stderr.strip()!r}")
print("  Si solo guardas stdout, en el log queda 'paso 1 ok' y el porque se pierde.")
