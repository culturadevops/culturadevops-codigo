# -*- coding: utf-8 -*-
"""La tienda del laboratorio de incidentes. Sin bibliotecas raras: métricas a mano, logs a Loki.

Cada incidente del curso es un interruptor que alguien deja encendido, como en la vida real:
    POST /admin/depuracion    -> el log de auditoría escribe 50 KB por pedido   (incidente 1)
    variable FUGA=1           -> una caché sin límite que crece en cada pedido  (incidente 2)
    variable APAGADO=bueno    -> al recibir SIGTERM termina lo que tiene a medias (incidente 4)
    GET /historial?cliente=N  -> una consulta a Postgres                       (incidente 5)

Métricas en /metrics (formato de texto de Prometheus) y logs en JSON a Loki.
"""
import json
import os
import random
import signal
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

NOMBRE = os.environ.get("NOMBRE", "tienda")
LOKI = os.environ.get("LOKI", "http://loki:3100/loki/api/v1/push")
AUDITORIA = os.environ.get("AUDITORIA", "/datos/auditoria.log")
FUGA = os.environ.get("FUGA") == "1"
CACHE_MAX = int(os.environ.get("CACHE_MAX", "0"))    # 0 = sin límite (la fuga)
APAGADO_BUENO = os.environ.get("APAGADO") == "bueno"
DSN = os.environ.get("DSN", "")

DEPURACION = False
CACHE = {}
CANDADO = threading.Lock()
CONTADOR = {}       # (ruta, codigo) -> n
SUMA, CUENTA = {}, {}
EN_CURSO = 0
INICIO = time.time()


def log(nivel, mensaje, **extra):
    linea = json.dumps({"msg": mensaje, "instancia": NOMBRE, **extra}, ensure_ascii=False)
    cuerpo = {"streams": [{"stream": {"app": "tienda", "nivel": nivel},
                           "values": [[str(time.time_ns()), linea]]}]}
    try:
        req = urllib.request.Request(LOKI, data=json.dumps(cuerpo).encode(),
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=2)
    except Exception:
        pass


def memoria():
    try:
        with open("/proc/self/statm") as f:
            return int(f.read().split()[1]) * os.sysconf("SC_PAGE_SIZE")
    except OSError:
        return 0


def anota(ruta, codigo, segundos):
    with CANDADO:
        CONTADOR[(ruta, str(codigo))] = CONTADOR.get((ruta, str(codigo)), 0) + 1
        SUMA[ruta] = SUMA.get(ruta, 0.0) + segundos
        CUENTA[ruta] = CUENTA.get(ruta, 0) + 1


def metricas():
    out = ["# TYPE tienda_peticiones_total counter"]
    with CANDADO:
        for (r, c), n in sorted(CONTADOR.items()):
            out.append(f'tienda_peticiones_total{{ruta="{r}",codigo="{c}"}} {n}')
        out.append("# TYPE tienda_latencia_suma_segundos counter")
        for r, s in sorted(SUMA.items()):
            out.append(f'tienda_latencia_suma_segundos{{ruta="{r}"}} {s:.4f}')
        out.append("# TYPE tienda_latencia_cuenta counter")
        for r, c in sorted(CUENTA.items()):
            out.append(f'tienda_latencia_cuenta{{ruta="{r}"}} {c}')
        out += ["# TYPE tienda_memoria_bytes gauge", f"tienda_memoria_bytes {memoria()}",
                "# TYPE tienda_cache_entradas gauge", f"tienda_cache_entradas {len(CACHE)}",
                "# TYPE tienda_en_curso gauge", f"tienda_en_curso {EN_CURSO}",
                "# TYPE tienda_arranque_segundos gauge", f"tienda_arranque_segundos {INICIO:.0f}"]
    return "\n".join(out) + "\n"


def auditar(pedido, pais, total):
    """Cada pedido deja una línea de auditoría en disco. Si no se puede escribir, el pedido falla:
    la auditoría es obligatoria (eso es lo que convierte un disco lleno en errores 500)."""
    relleno = "x" * 50_000 if DEPURACION else ""
    with open(AUDITORIA, "a") as f:
        f.write(json.dumps({"pedido": pedido, "pais": pais, "total": total, "depuracion": relleno}) + "\n")


def historial(cliente):
    import psycopg
    with psycopg.connect(DSN, connect_timeout=3) as c:
        return c.execute("SELECT id, total FROM pedidos WHERE cliente = %s ORDER BY creado DESC LIMIT 10",
                         (cliente,)).fetchall()


class Mano(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def do_POST(self):
        global DEPURACION
        if self.path == "/admin/depuracion":
            DEPURACION = True
            log("info", "modo depuracion ACTIVADO", por=self.headers.get("X-Usuario", "?"))
            return self._json(200, {"depuracion": True})
        self._json(404, {"error": "no existe"})

    def do_GET(self):
        global EN_CURSO
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
        if ruta == "/salud":
            return self._json(200, {"ok": True})
        with CANDADO:
            EN_CURSO += 1
        try:
            if ruta == "/pedido":
                self._pedido(t0)
            elif ruta == "/lento":
                time.sleep(1.0)              # un pedido con pago: tarda un segundo
                self._json(200, {"ok": True}, ruta, t0)
            elif ruta == "/historial":
                cliente = self.path.split("cliente=")[-1]
                try:
                    filas = historial(cliente)
                    self._json(200, {"pedidos": len(filas)}, ruta, t0)
                except Exception as e:
                    log("error", "historial fallido", error=str(e)[:200])
                    self._json(500, {"error": "historial"}, ruta, t0)
            else:
                self._json(404, {"error": "no existe"}, ruta, t0)
        finally:
            with CANDADO:
                EN_CURSO -= 1

    def _pedido(self, t0):
        pedido = random.randint(1, 10**9)
        pais = random.choice(["ES", "MX", "AR", "CO", "CL"])
        total = round(random.uniform(10, 200), 2)
        if FUGA:
            # ⛔ La caché que «acelera» los pedidos: guarda cada respuesta y no borra nunca nada.
            CACHE[pedido] = bytearray(200_000)
            if CACHE_MAX and len(CACHE) > CACHE_MAX:
                CACHE.pop(next(iter(CACHE)))
        try:
            auditar(pedido, pais, total)
        except OSError as e:
            log("error", "no se pudo auditar el pedido", error=str(e))
            return self._json(500, {"error": "auditoria"}, "/pedido", t0)
        self._json(200, {"pedido": pedido, "total": total}, "/pedido", t0)

    def _json(self, codigo, datos, ruta=None, t0=None):
        cuerpo = json.dumps(datos).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)
        if ruta:
            anota(ruta, codigo, time.time() - t0)


def main():
    srv = ThreadingHTTPServer(("0.0.0.0", 8000), Mano)
    srv.daemon_threads = False      # al cerrar, se esperan los hilos con peticiones a medias
    if APAGADO_BUENO:
        def apagar(*_):
            log("info", "SIGTERM: dejo de aceptar y termino lo que tengo a medias", en_curso=EN_CURSO)
            threading.Thread(target=srv.shutdown).start()
        signal.signal(signal.SIGTERM, apagar)
    # Sin APAGADO=bueno no hay manejador: como PID 1 del contenedor, el núcleo IGNORA el SIGTERM.
    # docker stop espera 10 s y lo mata con SIGKILL (código 137), con lo que lleve a medias.
    log("info", "la tienda arranca", fuga=FUGA, apagado=("bueno" if APAGADO_BUENO else "de golpe"))
    srv.serve_forever()
    srv.server_close()               # espera a los hilos en curso
    log("info", "apagada limpia")
    sys.exit(0)


if __name__ == "__main__":
    main()
