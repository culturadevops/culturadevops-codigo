# -*- coding: utf-8 -*-
"""Discord FALSO (cultura-devops 799): imita un webhook de Discord y solo apunta lo que le llega.
Nada se envía a Discord de verdad.
  POST /api/webhooks/<id>/<token>  → 204 sin cuerpo (lo que devuelve Discord sin ?wait=true)
      con LIMITAR=1 la PRIMERA petición recibe 429 con {"message", "retry_after", "global"}, como describe
      la documentación de límites de Discord.
  POST /marca   → apunta una marca de la línea de tiempo («── api se apaga»), la manda el orquestador
  GET  /recibido → la lista JSON de todo lo recibido
"""
import http.server
import json
import os
import socketserver
import time

T0 = time.monotonic()
RECIBIDO = []
LIMITAR = os.environ.get("LIMITAR") == "1"
peticiones = 0


def t():
    return f"{time.monotonic() - T0:5.1f} s"


class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        global peticiones
        n = int(self.headers.get("Content-Length", "0"))
        cuerpo = json.loads(self.rfile.read(n) or b"{}")
        if self.path == "/marca":
            print(f"{t()}  ── {cuerpo['texto']}", flush=True)
            self._responder(204)
            return
        peticiones += 1
        if LIMITAR and peticiones == 1:
            print(f"{t()}  discord ← 429 (límite): le pido que espere 1.5 s", flush=True)
            self._responder(429, {"message": "You are being rate limited.", "retry_after": 1.5, "global": False})
            return
        RECIBIDO.append(cuerpo)
        texto = cuerpo.get("content") or ""
        emb = (cuerpo.get("embeds") or [{}])[0]
        print(f"{t()}  discord ← {texto} | {emb.get('title', '')}", flush=True)
        self._responder(204)

    def do_GET(self):
        self._responder(200, RECIBIDO)

    def _responder(self, codigo, datos=None):
        b = b"" if datos is None else json.dumps(datos, ensure_ascii=False, indent=2).encode()
        self.send_response(codigo)
        if datos is not None:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def log_message(self, *a):
        pass


class Servidor(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


print(f"{t()}  discord falso escuchando en :9000", flush=True)
Servidor(("0.0.0.0", 9000), H).serve_forever()
