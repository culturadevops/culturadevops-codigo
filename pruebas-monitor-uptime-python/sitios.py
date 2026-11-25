# -*- coding: utf-8 -*-
"""Sitios de prueba del banco (cultura-devops 799). Solo biblioteca estándar.
  :8001 web    → siempre 200
  :8002 pagos  → 500 una sí, una no
  :8003 lento  → 200, pero tarda 3 s
El sitio «api» es otro contenedor aparte (python -m http.server), para poder apagarlo y encenderlo."""
import http.server
import itertools
import socketserver
import threading
import time

contador = itertools.count()


def manejador(tipo):
    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            codigo = 200
            if tipo == "pagos" and next(contador) % 2 == 0:
                codigo = 500
            if tipo == "lento":
                time.sleep(3)
            cuerpo = f"{tipo} {codigo}\n".encode()
            self.send_response(codigo)
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)

        def log_message(self, *a):
            pass
    return H


class Servidor(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


for tipo, puerto in (("web", 8001), ("pagos", 8002), ("lento", 8003)):
    s = Servidor(("0.0.0.0", puerto), manejador(tipo))
    threading.Thread(target=s.serve_forever, daemon=True).start()
print("sitios listos: web:8001 pagos:8002 lento:8003", flush=True)
threading.Event().wait()
