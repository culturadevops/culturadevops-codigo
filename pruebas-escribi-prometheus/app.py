#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""app — el servicio que va a ser medido. Expone /metrics en formato de exposición.

Esto es lo que en Prometheus se llama un "objetivo": no manda nada a ningún sitio, solo deja
un texto colgado en una URL y se olvida. Quien decide cuándo leerlo es el que recoge.

Sirve además para la demostración de CARDINALIDAD del vídeo: con MODO_CARDINALIDAD=1 la métrica
`peticiones_total` lleva una etiqueta con el identificador de usuario, y cada usuario nuevo crea
una SERIE nueva. Es el error caro de verdad, y aquí se ve el número creciendo.
"""
import os
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RUTAS = ["/", "/login", "/api/libros", "/salud"]
CARDINALIDAD = os.environ.get("MODO_CARDINALIDAD") == "1"

peticiones = {}      # (ruta, codigo, usuario) -> contador
latencia = {}        # ruta -> suma y cuenta
arranque = time.time()
candado = threading.Lock()


def trafico():
    """Simula tráfico para que haya algo que medir."""
    n = 0
    while True:
        n += 1
        ruta = random.choice(RUTAS)
        codigo = "500" if random.random() < 0.05 else "200"
        # ⛔ AQUÍ ESTÁ LA BOMBA: el identificador de usuario como etiqueta. Cada valor
        #    distinto es una serie NUEVA para siempre, no un dato más en la misma serie.
        usuario = f"u{n}" if CARDINALIDAD else ""
        with candado:
            k = (ruta, codigo, usuario)
            peticiones[k] = peticiones.get(k, 0) + 1
            s, c = latencia.get(ruta, (0.0, 0))
            latencia[ruta] = (s + random.uniform(0.01, 0.4), c + 1)
        time.sleep(0.01)


def texto():
    """El formato de exposición, escrito a mano. Es literalmente esto: líneas de texto."""
    lineas = [
        "# HELP peticiones_total Peticiones atendidas desde el arranque.",
        "# TYPE peticiones_total counter",
    ]
    with candado:
        for (ruta, codigo, usuario), n in sorted(peticiones.items()):
            etq = f'ruta="{ruta}",codigo="{codigo}"'
            if usuario:
                etq += f',usuario="{usuario}"'
            lineas.append(f"peticiones_total{{{etq}}} {n}")
        lineas += ["# HELP latencia_segundos_media Latencia media por ruta.",
                   "# TYPE latencia_segundos_media gauge"]
        for ruta, (s, c) in sorted(latencia.items()):
            lineas.append(f'latencia_segundos_media{{ruta="{ruta}"}} {s / c:.6f}')
    lineas += ["# HELP tiempo_encendido_segundos Segundos desde el arranque.",
               "# TYPE tiempo_encendido_segundos gauge",
               f"tiempo_encendido_segundos {time.time() - arranque:.3f}"]
    return "\n".join(lineas) + "\n"


class Manejador(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def do_GET(self):
        cuerpo = (texto() if self.path.startswith("/metrics") else "ok\n").encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)


if __name__ == "__main__":
    threading.Thread(target=trafico, daemon=True).start()
    print(f"app en :9101/metrics · cardinalidad={'SI' if CARDINALIDAD else 'no'}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 9101), Manejador).serve_forever()
