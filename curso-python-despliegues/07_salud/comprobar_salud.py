# -*- coding: utf-8 -*-
"""Leccion 7 — Health check: 200 OK no significa que tu version este funcionando."""
import json
import socket
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

INICIO = time.monotonic()


class App(BaseHTTPRequestHandler):
    """Hasta 1 s sirve la v1 (la vieja). De 1 a 2 s reinicia (503). Despues, la v2."""

    def do_GET(self):
        t = time.monotonic() - INICIO
        if t < 1.0:
            codigo, cuerpo = 200, {"estado": "ok", "version": "v1"}
        elif t < 2.0:
            codigo, cuerpo = 503, {"estado": "arrancando"}
        else:
            codigo, cuerpo = 200, {"estado": "ok", "version": "v2"}
        datos = json.dumps(cuerpo).encode()
        self.send_response(codigo)
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def log_message(self, *a):
        pass


srv = ThreadingHTTPServer(("127.0.0.1", 0), App)
threading.Thread(target=srv.serve_forever, daemon=True).start()
PUERTO = srv.server_address[1]
URL = f"http://127.0.0.1:{PUERTO}/salud"


def consultar():
    try:
        with urllib.request.urlopen(URL, timeout=1) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def reloj():
    return f"t={time.monotonic() - INICIO:.1f}s"


print("== 7.1 · LA TRAMPA: 'el puerto contesta' ==")
socket.create_connection(("127.0.0.1", PUERTO), timeout=1).close()
print(f"  {reloj()}  el puerto {PUERTO} acepta conexiones -> 'desplegado'")

print()
print("== 7.2 · LA TRAMPA 2: 'la salud da 200' ==")
codigo, cuerpo = consultar()
print(f"  {reloj()}  /salud -> {codigo} {cuerpo}")
print("  200... de la version VIEJA, que todavia no se ha ido.")

print()
print("== 7.3 · Bien: esperar a que conteste la version que desplegaste ==")


def esperar_version(esperada, plazo=5.0, cada=0.25):
    limite = time.monotonic() + plazo
    intentos = 0
    while time.monotonic() < limite:
        intentos += 1
        try:
            codigo, cuerpo = consultar()
        except OSError as e:
            codigo, cuerpo = None, {"error": type(e).__name__}
        if codigo == 200 and cuerpo.get("version") == esperada:
            print(f"  {reloj()}  {codigo} {cuerpo}  <- esta si (intento {intentos})")
            return True
        if intentos == 1 or codigo != 200:
            print(f"  {reloj()}  {codigo} {cuerpo}")
        time.sleep(cada)
    print(f"  {reloj()}  plazo agotado tras {intentos} intentos")
    return False


esperar_version("v2")

print()
print("== 7.4 · Y si nunca llega: el plazo decide, no la paciencia ==")
esperar_version("v3", plazo=1.0)
srv.shutdown()
