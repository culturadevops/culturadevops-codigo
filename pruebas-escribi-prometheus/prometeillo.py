#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""prometeillo — un Prometheus de juguete, en Python, sin una sola dependencia externa.

Vídeo 221 · «Escribí un Prometheus en Python y Grafana se conectó sin notarlo».

La promesa del vídeo es que GRAFANA OFICIAL se conecte a esto y pinte un panel. Para eso no basta
con exponer métricas: hay que hacer las DOS mitades que hace Prometheus de verdad.

  1. IR A BUSCAR las métricas (el "scrape"). Prometheus NO recibe nada: llama él, cada X segundos,
     a la URL de cada objetivo. Por eso un proceso que vive 3 segundos no aparece NUNCA en tus
     gráficas: nadie estaba mirando cuando existía.

  2. CONTESTAR la API de consulta que habla Grafana:
       /api/v1/query          instante
       /api/v1/query_range    rango  (es el que usa un panel de serie temporal)
       /api/v1/labels, /api/v1/label/<x>/values, /api/v1/metadata, /api/v1/status/buildinfo
     Grafana no sabe que esto es Python. Solo ve JSON con la forma que espera.

⛔ LO QUE NO ES: esto no es Prometheus. No hay PromQL de verdad (solo se resuelve el nombre de la
   métrica con sus etiquetas), no hay almacenamiento en disco, no hay reglas, ni alertas, ni
   federación. Se dice en el vídeo con estas palabras.
"""
import json
import re
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

OBJETIVOS = ["http://app:9101/metrics"]
CADA = 2.0          # segundos entre scrapes
RETENCION = 3600    # segundos de historia que guardamos en memoria


# ══════════════════════════════════════════════════════════════════════════
#  1 · EL ALMACÉN
#
#  Una serie NO es "una métrica". Una serie es una métrica MÁS una combinación
#  concreta de etiquetas. `peticiones{ruta="/a"}` y `peticiones{ruta="/b"}` son
#  DOS series distintas, cada una con su propia lista de puntos en el tiempo.
#  De ahí sale la explosión de cardinalidad, y por eso `series` es un dict cuya
#  clave es el conjunto entero de etiquetas.
# ══════════════════════════════════════════════════════════════════════════
series = {}          # clave -> {"metrica":str, "etiquetas":dict, "puntos":[(ts, valor)]}
candado = threading.Lock()


def clave(metrica, etiquetas):
    partes = ",".join(f"{k}={v}" for k, v in sorted(etiquetas.items()))
    return f"{metrica}{{{partes}}}"


def guardar(metrica, etiquetas, valor, ts):
    k = clave(metrica, etiquetas)
    with candado:
        s = series.setdefault(k, {"metrica": metrica, "etiquetas": etiquetas, "puntos": []})
        s["puntos"].append((ts, valor))
        corte = ts - RETENCION
        while s["puntos"] and s["puntos"][0][0] < corte:
            s["puntos"].pop(0)


# ══════════════════════════════════════════════════════════════════════════
#  2 · EL FORMATO DE EXPOSICIÓN
#
#  Es TEXTO PLANO. Una línea por serie:  nombre{etiqueta="valor"} numero
#  Nada de binario, nada de protobuf, nada de esquema. Se lee con un curl y se
#  depura a ojo, y eso vale igual para el Prometheus de tu empresa.
# ══════════════════════════════════════════════════════════════════════════
LINEA = re.compile(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)(?:\{(.*)\})?\s+([^\s]+)\s*$')
PAR = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*)="((?:[^"\\]|\\.)*)"')


def parsear(texto):
    """Devuelve [(metrica, etiquetas, valor)] de un cuerpo en formato de exposición."""
    fuera = []
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):   # # HELP y # TYPE son metadatos
            continue
        m = LINEA.match(linea)
        if not m:
            continue
        nombre, etqs, valor = m.group(1), m.group(2) or "", m.group(3)
        try:
            v = float(valor)
        except ValueError:
            continue   # NaN, +Inf y demás: fuera, que no es el tema del vídeo
        fuera.append((nombre, dict(PAR.findall(etqs)), v))
    return fuera


# ══════════════════════════════════════════════════════════════════════════
#  3 · EL SCRAPE — la mitad que sorprende a todo el mundo
#
#  Prometheus va a buscar. Cada CADA segundos, llama a cada objetivo, lee el
#  texto y guarda un punto por serie. Si tu proceso no estaba vivo en ese
#  instante, ese punto no existe y no existirá nunca.
#
#  Y se guarda `up`, que es la métrica que Prometheus se INVENTA por cada
#  objetivo: 1 si contestó, 0 si no. No la expone nadie: la escribe el que
#  recoge. Por eso puedes alertar de que algo se cayó aunque esté muerto.
# ══════════════════════════════════════════════════════════════════════════
def recoger():
    while True:
        for url in OBJETIVOS:
            ts = time.time()
            etq_obj = {"instance": urlparse(url).netloc, "job": "demo"}
            try:
                with urllib.request.urlopen(url, timeout=CADA) as r:
                    cuerpo = r.read().decode("utf-8", "replace")
                arriba = 1.0
            except Exception:
                cuerpo, arriba = "", 0.0
            guardar("up", etq_obj, arriba, ts)
            for metrica, etqs, valor in parsear(cuerpo):
                guardar(metrica, {**etq_obj, **etqs}, valor, ts)
        time.sleep(CADA)


# ══════════════════════════════════════════════════════════════════════════
#  4 · LA API QUE HABLA GRAFANA
#
#  Un selector aquí es `nombre{etiqueta="valor"}`. No hay funciones, ni rate(),
#  ni operadores: eso es PromQL de verdad y no cabe en un vídeo. Lo que sí cabe
#  es la FORMA de la respuesta, que es lo único que Grafana mira.
# ══════════════════════════════════════════════════════════════════════════
SELECTOR = re.compile(r'^\s*([a-zA-Z_:][a-zA-Z0-9_:]*)\s*(?:\{(.*)\})?\s*$')


def seleccionar(consulta):
    m = SELECTOR.match(consulta or "")
    if not m:
        return []
    nombre, filtros = m.group(1), dict(PAR.findall(m.group(2) or ""))
    with candado:
        elegidas = [s for s in series.values()
                    if s["metrica"] == nombre
                    and all(s["etiquetas"].get(k) == v for k, v in filtros.items())]
        return [{"etiquetas": dict(s["etiquetas"], __name__=s["metrica"]),
                 "puntos": list(s["puntos"])} for s in elegidas]


def ok(datos):
    return {"status": "success", "data": datos}


class Manejador(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def responder(self, obj, codigo=200):
        cuerpo = json.dumps(obj).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        # ⛔ Sin esto Grafana se queda esperando: HTTP/1.1 mantiene la conexión abierta y el
        #    cliente no sabe dónde acaba el cuerpo si nadie declara cuánto mide.
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, *a):
        pass

    def do_POST(self):
        # Grafana manda las consultas por POST desde hace varias versiones.
        n = int(self.headers.get("Content-Length") or 0)
        cuerpo = self.rfile.read(n).decode() if n else ""
        self.ruta(urlparse(self.path).path, parse_qs(cuerpo))

    def do_GET(self):
        u = urlparse(self.path)
        self.ruta(u.path, parse_qs(u.query))

    def ruta(self, camino, q):
        uno = lambda k, d=None: (q.get(k) or [d])[0]  # noqa: E731

        if camino == "/api/v1/status/buildinfo":
            return self.responder(ok({"version": "0.0.1-prometeillo", "features": {}}))

        if camino == "/api/v1/labels":
            with candado:
                etq = {"__name__"} | {k for s in series.values() for k in s["etiquetas"]}
            return self.responder(ok(sorted(etq)))

        if camino.startswith("/api/v1/label/") and camino.endswith("/values"):
            nombre = camino[len("/api/v1/label/"):-len("/values")]
            with candado:
                if nombre == "__name__":
                    vals = {s["metrica"] for s in series.values()}
                else:
                    vals = {s["etiquetas"][nombre] for s in series.values()
                            if nombre in s["etiquetas"]}
            return self.responder(ok(sorted(vals)))

        if camino == "/api/v1/metadata":
            return self.responder(ok({}))

        if camino == "/api/v1/query":
            ahora = float(uno("time") or time.time())
            res = []
            for s in seleccionar(uno("query")):
                previos = [p for p in s["puntos"] if p[0] <= ahora]
                if previos:
                    ts, v = previos[-1]
                    res.append({"metric": s["etiquetas"], "value": [ts, str(v)]})
            return self.responder(ok({"resultType": "vector", "result": res}))

        if camino == "/api/v1/query_range":
            # El panel de serie temporal pide una REJILLA regular: desde, hasta y cada cuánto.
            # Prometheus no devuelve los puntos crudos: devuelve, para cada instante de la
            # rejilla, el último valor conocido. A eso se le llama "muestreo escalonado" y es
            # por lo que una gráfica no tiene huecos aunque el scrape se pierda una vuelta.
            desde = float(uno("start") or 0)
            hasta = float(uno("end") or time.time())
            paso = max(float(uno("step") or 15), 1.0)
            res = []
            for s in seleccionar(uno("query")):
                puntos, valores, i = s["puntos"], [], 0
                ultimo = None
                t = desde
                while t <= hasta:
                    while i < len(puntos) and puntos[i][0] <= t:
                        ultimo = puntos[i][1]
                        i += 1
                    if ultimo is not None:
                        valores.append([t, str(ultimo)])
                    t += paso
                if valores:
                    res.append({"metric": s["etiquetas"], "values": valores})
            return self.responder(ok({"resultType": "matrix", "result": res}))

        if camino == "/-/healthy":
            return self.responder({"ok": True})

        self.responder({"status": "error", "errorType": "not_found",
                        "error": camino}, codigo=404)


if __name__ == "__main__":
    threading.Thread(target=recoger, daemon=True).start()
    print("prometeillo escuchando en :9090 · yendo a buscar", OBJETIVOS, "cada", CADA, "s",
          flush=True)
    ThreadingHTTPServer(("0.0.0.0", 9090), Manejador).serve_forever()
