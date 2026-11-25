# El servidor de la comparativa, en Python: SOLO librería estándar (http.server con hilos).
# El mismo contrato que el de Node: /suma hace CPU de verdad, /espera simula E/S.
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ARRANQUE = time.perf_counter()


class Manejador(BaseHTTPRequestHandler):
    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if u.path == "/suma":
            n = int(q.get("n", 0))
            t0 = time.perf_counter_ns()
            s = 0
            for i in range(1, n + 1):
                s += i * i % 1000003
            ns = time.perf_counter_ns() - t0
            cuerpo = {"lang": "python", "n": n, "suma": s, "ns": ns}
        elif u.path == "/espera":
            ms = int(q.get("ms", 0))
            time.sleep(ms / 1000)
            cuerpo = {"lang": "python", "n": ms, "suma": 0, "ns": 0}
        else:
            self.send_response(404)
            self.end_headers()
            return
        datos = json.dumps(cuerpo).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def log_message(self, *a):   # sin ruido por petición
        pass


class Servidor(ThreadingHTTPServer):
    # ⚠️ MEDIDO el 2026-08-30: con la cola por defecto (request_queue_size=5) 300 conexiones
    # simultáneas ATRAGANTAN al servidor (timeout a los 30 s). Node escucha con backlog 511
    # por defecto; se iguala aquí para que la comparación sea del runtime, no de la cola.
    request_queue_size = 511
    daemon_threads = True


if __name__ == "__main__":
    srv = Servidor(("0.0.0.0", 8080), Manejador)
    # La marca de «listo» del propio proceso: main → escuchando, sin el contenedor por medio.
    print(f"LISTO_EN_MS {(time.perf_counter() - ARRANQUE) * 1000:.3f}",
          file=sys.stderr, flush=True)
    srv.serve_forever()
