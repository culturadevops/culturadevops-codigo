# -*- coding: utf-8 -*-
"""Leccion 12 — Pone a prueba desplegar.py: una app de juguete y siete despliegues."""
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

AQUI = Path(__file__).resolve().parent
tmp = Path(tempfile.mkdtemp())
base, build = tmp / "srv", tmp / "build"

# Las builds: la v3 sale rota (no pasa su propia salud).
for v, sana in (("v1", True), ("v2", True), ("v3", False), ("v4", True), ("v5", True)):
    (build / v).mkdir(parents=True)
    (build / v / "app.json").write_text(json.dumps({"version": v, "sana": sana}))


class App(BaseHTTPRequestHandler):
    """La 'aplicacion': sirve la release a la que apunta ACTUAL."""

    def do_GET(self):
        try:
            actual = (base / "ACTUAL").read_text().strip()
            app = json.loads((base / "releases" / actual / "app.json").read_text())
            codigo = 200 if app["sana"] else 500
        except (OSError, ValueError):
            codigo, app = 503, {}
        datos = json.dumps({"version": app.get("version")}).encode()
        self.send_response(codigo)
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def log_message(self, *a):
        pass


srv = ThreadingHTTPServer(("127.0.0.1", 0), App)
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f"http://127.0.0.1:{srv.server_address[1]}/salud"


def desplegar(version, *extra):
    cmd = [sys.executable, str(AQUI / "desplegar.py"), "--version", version,
           "--origen", str(build / version), "--base", str(base), "--url", URL,
           "--plazo", "1.5", *extra]
    t0 = time.perf_counter()
    r = subprocess.run(cmd, capture_output=True, text=True)
    dur = time.perf_counter() - t0
    for linea in (r.stdout + r.stderr).splitlines():
        print(f"    {linea}")
    return r.returncode, dur


def estado():
    if not (base / "releases").exists():
        return f"(no existe {base.name}/releases: el simulacro no creo nada)"
    rel = sorted(p.name for p in (base / "releases").iterdir())
    act = (base / "ACTUAL").read_text() if (base / "ACTUAL").exists() else None
    return f"ACTUAL={act}  releases={rel}"


def paso(titulo, version, *extra):
    print(f"== {titulo} ==")
    codigo, dur = desplegar(version, *extra)
    print(f"  -> codigo {codigo} en {dur:.1f} s   {estado()}")
    print()
    return codigo


paso("1 · Simulacro de la v1", "v1", "--dry-run")
paso("2 · La v1 de verdad", "v1")
paso("3 · La v2", "v2")
paso("4 · La v2 OTRA vez (el pipeline reintento)", "v2")
paso("5 · La v3, que sale rota", "v3")
paso("6 · La v4", "v4")
paso("7 · La v5 (y la limpieza, que conserva 3)", "v5")

print("== 8 · Con otro despliegue en curso (su cerrojo esta puesto) ==")
(base / "desplegar.lock").write_text('{"pid": 4242}')
codigo, _ = desplegar("v5")
print(f"  -> codigo {codigo}")

srv.shutdown()
shutil.rmtree(tmp)
