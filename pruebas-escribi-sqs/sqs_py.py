# -*- coding: utf-8 -*-
"""sqs_py.py — un SQS escrito en Python, para el video 217 de cultura-devops.

LA PROMESA DEL VIDEO: que **boto3 oficial** haga SendMessage, ReceiveMessage y DeleteMessage
contra esto sin notar nada. Lo unico que cambia es `endpoint_url`.

🥇 EL GIRO, y es el mejor de toda la linea porque descoloca a todo el mundo:
**RECIBIR UN MENSAJE NO LO SACA DE LA COLA. LO ESCONDE.**

El mensaje sigue ahi, invisible durante un rato, y si no lo borras VUELVE A APARECER. Escribirlo
es lo que lo hace evidente: al implementarlo descubres que NO PUEDES borrar al entregar, porque
no sabes si el consumidor va a terminar. Y de ahi salen de golpe tres cosas que la gente sufre
sin entender:

  · el tiempo de invisibilidad (VisibilityTimeout)
  · por que hay que borrar EXPLICITAMENTE, y con un "recibo" y no con el id del mensaje
  · por que "al menos una vez" significa que tu consumidor tiene que aguantar duplicados

LO QUE NO HACE: colas de mensajes muertos, orden estricto (FIFO), deduplicacion, atributos.

Sin dependencias: solo la biblioteca estandar.

    python sqs_py.py --puerto 9324
"""
import argparse
import json
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

# cola -> lista de mensajes. Cada uno:
#   {"id", "cuerpo", "recibo", "invisible_hasta", "entregas"}
#
# ⚠️ MIRALO BIEN: no hay dos listas. No existe una "cola de en vuelo". Un mensaje entregado sigue
# EN LA MISMA LISTA, solo que con una fecha hasta la que nadie mas lo puede ver.
COLAS = {}
CANDADO = threading.Lock()

INVISIBILIDAD = 5.0        # segundos. En SQS de verdad, 30 por defecto.


class SQS(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _ok(self, obj):
        cuerpo = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/x-amz-json-1.0")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def _err(self, tipo, mensaje):
        cuerpo = json.dumps({"__type": tipo, "message": mensaje}).encode()
        self.send_response(400)
        self.send_header("Content-Type", "application/x-amz-json-1.0")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        crudo = self.rfile.read(n) if n else b""
        objetivo = (self.headers.get("X-Amz-Target") or "").split(".")[-1]
        if objetivo:                                   # protocolo JSON (boto3 moderno)
            c = json.loads(crudo or b"{}")
        else:                                          # protocolo de formulario (el viejo)
            f = parse_qs(crudo.decode())
            objetivo = f.get("Action", [""])[0]
            c = {k: v[0] for k, v in f.items()}
        try:
            return getattr(self, f"op_{objetivo}")(c)
        except AttributeError:
            return self._err("InvalidAction", f"no implemento {objetivo}")

    # ── operaciones ─────────────────────────────────────────────────────
    def op_CreateQueue(self, c):
        nombre = c["QueueName"]
        with CANDADO:
            COLAS.setdefault(nombre, [])
        return self._ok({"QueueUrl": f"http://{self.headers.get('Host')}/cola/{nombre}"})

    def op_GetQueueUrl(self, c):
        return self._ok({"QueueUrl": f"http://{self.headers.get('Host')}/cola/{c['QueueName']}"})

    def _cola(self, url):
        return COLAS.setdefault(url.rsplit("/", 1)[-1], [])

    def op_SendMessage(self, c):
        with CANDADO:
            m = {"id": str(uuid.uuid4()), "cuerpo": c["MessageBody"],
                 "recibo": None, "invisible_hasta": 0.0, "entregas": 0}
            self._cola(c["QueueUrl"]).append(m)
        return self._ok({"MessageId": m["id"], "MD5OfMessageBody": "no-lo-calculo"})

    def op_ReceiveMessage(self, c):
        """AQUI ESTA EL VIDEO.

        No se borra nada. Se marca invisible y se entrega un RECIBO nuevo. Si el consumidor se
        muere sin borrar, pasada la invisibilidad el mensaje reaparece para otro.
        """
        cuantos = int(c.get("MaxNumberOfMessages", 1))
        ahora = time.monotonic()
        salida = []
        with CANDADO:
            for m in self._cola(c["QueueUrl"]):
                if len(salida) >= cuantos:
                    break
                if m["invisible_hasta"] > ahora:
                    continue                            # entregado a otro hace poco: no se ve
                m["invisible_hasta"] = ahora + INVISIBILIDAD
                m["entregas"] += 1
                # El recibo cambia EN CADA ENTREGA. Por eso no puedes borrar con el id del
                # mensaje: el recibo demuestra que TU lo recibiste en ESTA vuelta.
                m["recibo"] = str(uuid.uuid4())
                salida.append({"MessageId": m["id"], "Body": m["cuerpo"],
                               "ReceiptHandle": m["recibo"],
                               "Attributes": {"ApproximateReceiveCount": str(m["entregas"])}})
        return self._ok({"Messages": salida} if salida else {})

    def op_DeleteMessage(self, c):
        with CANDADO:
            cola = self._cola(c["QueueUrl"])
            for i, m in enumerate(cola):
                if m["recibo"] == c["ReceiptHandle"]:
                    cola.pop(i)
                    break
        return self._ok({})

    def op_GetQueueAttributes(self, c):
        ahora = time.monotonic()
        with CANDADO:
            cola = self._cola(c["QueueUrl"])
            visibles = sum(1 for m in cola if m["invisible_hasta"] <= ahora)
            ocultos = len(cola) - visibles
        return self._ok({"Attributes": {
            "ApproximateNumberOfMessages": str(visibles),
            "ApproximateNumberOfMessagesNotVisible": str(ocultos)}})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=9324)
    ap.add_argument("--bind", default="127.0.0.1")
    a = ap.parse_args()
    s = ThreadingHTTPServer((a.bind, a.puerto), SQS)
    print(f"escuchando en {a.bind}:{a.puerto}", flush=True)
    s.serve_forever()


if __name__ == "__main__":
    main()
