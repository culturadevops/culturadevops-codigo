# -*- coding: utf-8 -*-
"""Una tienda de mentira con un fallo de verdad, para el curso de observabilidad.

Expone sus métricas en /metrics (formato de texto de Prometheus, sin ninguna biblioteca) y manda
sus logs a Loki por HTTP. El fallo es real y reproducible: los pedidos del país "XX" revientan
al calcular el impuesto, porque ese país no está en la tabla.

    python tienda.py            # escucha en 8000
"""
import json
import random
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOKI = "http://localhost:3100/loki/api/v1/push"
IMPUESTO = {"ES": 0.21, "PT": 0.23, "FR": 0.20, "IT": 0.22}

# contadores en memoria: {(ruta, codigo): n}
CONTADOR = {}
LATENCIAS = []
SUMA = {}   # {ruta: segundos acumulados}
CUENTA = {}  # {ruta: peticiones}
CANDADO = threading.Lock()


def log(nivel, mensaje, **extra):
    """Manda una línea a Loki. Las etiquetas son POCAS a propósito (lección 9)."""
    linea = json.dumps({"msg": mensaje, **extra}, ensure_ascii=False)
    cuerpo = {"streams": [{"stream": {"app": "tienda", "nivel": nivel},
                           "values": [[str(time.time_ns()), linea]]}]}
    try:
        req = urllib.request.Request(LOKI, data=json.dumps(cuerpo).encode(),
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=2)
    except Exception:
        pass  # que la tienda no se caiga porque los logs no lleguen


ROTO = False   # cuando es True, se mete el id de pedido como etiqueta (leccion 12)


def anota(ruta, codigo, segundos, pedido=None):
    with CANDADO:
        if ROTO and pedido is not None:
            # ⛔ ESTO ES EL ERROR. Cada pedido crea una serie NUEVA que no se reutiliza jamas.
            CONTADOR[(ruta, str(codigo), str(pedido))] = 1
        CONTADOR[(ruta, str(codigo))] = CONTADOR.get((ruta, str(codigo)), 0) + 1
        LATENCIAS.append(segundos)
        SUMA[ruta] = SUMA.get(ruta, 0.0) + segundos
        CUENTA[ruta] = CUENTA.get(ruta, 0) + 1


def metricas():
    """El formato de texto de Prometheus, a mano: nombre{etiquetas} valor."""
    out = ["# HELP tienda_peticiones_total Peticiones atendidas",
           "# TYPE tienda_peticiones_total counter"]
    with CANDADO:
        for clave, n in sorted(CONTADOR.items()):
            if len(clave) == 3:
                out.append('tienda_peticiones_total{ruta="%s",codigo="%s",pedido="%s"} %d'
                           % (clave[0], clave[1], clave[2], n))
            else:
                out.append('tienda_peticiones_total{ruta="%s",codigo="%s"} %d' % (clave[0], clave[1], n))
        lat = sorted(LATENCIAS)
    out += ["# HELP tienda_latencia_segundos Latencia de la última petición",
            "# TYPE tienda_latencia_segundos gauge",
            "tienda_latencia_segundos %.4f" % (lat[-1] if lat else 0)]
    # suma y cuenta por ruta: con esas dos se calcula la media, y con ellas se demuestra
    # el error de promediar medias (lección 5)
    out += ["# HELP tienda_latencia_suma_segundos Segundos acumulados por ruta",
            "# TYPE tienda_latencia_suma_segundos counter"]
    for r, s in sorted(SUMA.items()):
        out.append('tienda_latencia_suma_segundos{ruta="%s"} %.4f' % (r, s))
    out += ["# HELP tienda_latencia_cuenta Peticiones por ruta",
            "# TYPE tienda_latencia_cuenta counter"]
    for r, c in sorted(CUENTA.items()):
        out.append('tienda_latencia_cuenta{ruta="%s"} %d' % (r, c))
    return "\n".join(out) + "\n"


class Mano(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # sin ruido en la consola: los logs van a Loki

    def do_GET(self):
        t0 = time.time()
        ruta = self.path.split("?")[0]
        if ruta == "/metrics":
            cuerpo = metricas().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)
            return
        if ruta == "/buscar":
            # ⚠️ A PROPOSITO: poca gente la usa y tarda mucho. Es la que se pierde al promediar.
            time.sleep(random.uniform(1.8, 2.4))
            self._responde(200, {"resultados": 3}, ruta, t0)
            log("info", "busqueda lenta", ms=int((time.time() - t0) * 1000))
            return
        if ruta == "/pedido":
            pais = (self.path.split("pais=")[-1] if "pais=" in self.path else "ES")[:2]
            try:
                # ⚠️ EL FALLO: si el país no está en la tabla, esto revienta con KeyError.
                total = round(100 * (1 + IMPUESTO[pais]), 2)
                time.sleep(random.uniform(0.01, 0.05))
                self._responde(200, {"pais": pais, "total": total}, ruta, t0)
                log("info", "pedido ok", pais=pais, total=total)
            except KeyError:
                self._responde(500, {"error": "pais desconocido"}, ruta, t0)
                log("error", "no se pudo calcular el impuesto: pais sin tarifa", pais=pais)
            return
        self._responde(404, {"error": "no existe"}, ruta, t0)

    def _responde(self, codigo, datos, ruta, t0):
        cuerpo = json.dumps(datos).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)
        anota(ruta, codigo, time.time() - t0, pedido=random.randint(1, 10**9))


if __name__ == "__main__":
    log("info", "la tienda arranca", puerto=8000)
    ThreadingHTTPServer(("0.0.0.0", 8000), Mano).serve_forever()
