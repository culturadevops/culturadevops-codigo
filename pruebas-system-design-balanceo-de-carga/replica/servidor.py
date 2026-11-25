# Una réplica de la API: responde a / tras RETRASO_MS milisegundos y dice quién es (cabecera X-Replica).
# /salud responde al momento: es lo que mira el chequeo activo del balanceador.
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

NOMBRE = os.environ["NOMBRE"]
RETRASO = int(os.environ.get("RETRASO_MS", "10")) / 1000


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    # Sin esto, la cabecera y el cuerpo salen en dos escrituras: la segunda espera al ACK de la
    # primera (Nagle) y, detrás de un proxy, el ACK llega retrasado ~40 ms. Medido: 53 ms de
    # mediana a través de HAProxy contra 11 ms directo. Es del servidor de prueba, no del balanceador.
    disable_nagle_algorithm = True

    def do_GET(self):
        if self.path == "/morir":  # el generador la mata en el segundo exacto de SU carga
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()
            self.wfile.flush()
            os._exit(1)
        if self.path != "/salud":
            time.sleep(RETRASO)
        cuerpo = NOMBRE.encode()
        self.send_response(200)
        self.send_header("X-Replica", NOMBRE)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_POST(self):
        largo = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(largo)
        self.do_GET()

    def log_message(self, *a):
        pass


# La cola de conexiones por defecto de Python es de 5: con 30 clientes a la vez rechaza conexiones y
# el balanceador reintenta (o, en nginx, devuelve 502). Medido en la primera versión de este banco.
ThreadingHTTPServer.request_queue_size = 128
with open("/tmp/pid", "w") as f:
    f.write(str(os.getpid()))  # para matar el proceso sin parar el contenedor
ThreadingHTTPServer(("0.0.0.0", 8000), H).serve_forever()
