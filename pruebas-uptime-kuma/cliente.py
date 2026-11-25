# -*- coding: utf-8 -*-
"""Cliente socket.io mínimo para Uptime Kuma 2.x (corre DENTRO de la red Docker `uk`).
La librería uptime-kuma-api no habla con la 2.x (se cuelga en `needSetup`, que ya no existe),
así que se usan los eventos del servidor tal cual: setup, login, addNotification, add."""
import json
import sys
import time

import socketio

URL = "http://kuma:3001"
sio = socketio.Client()
latidos = []


@sio.on("heartbeat")
def _hb(d):
    latidos.append(d)


def call(ev, *args):
    return sio.call(ev, args if len(args) > 1 else args[0] if args else None, timeout=30) \
        if False else sio.call(ev, data=args if len(args) != 1 else args[0], timeout=30)


def emit(ev, *args):
    box = {}
    sio.emit(ev, args, callback=lambda *r: box.setdefault("r", r[0] if r else None))
    for _ in range(300):
        if "r" in box:
            return box["r"]
        time.sleep(0.1)
    raise SystemExit(f"sin respuesta a {ev}")


BASE = dict(interval=20, retryInterval=20, maxretries=0, resendInterval=0, upsideDown=False,
            accepted_statuscodes=["200-299"], kafkaProducerBrokers=[], kafkaProducerSaslOptions={},
            conditions=[], rabbitmqNodes=[], active=True, ignoreTls=False, maxredirects=10,
            method="GET", timeout=16, packetSize=56, notificationIDList={})


def main():
    paso = sys.argv[1]
    sio.connect(URL, transports=["websocket"])
    if paso == "setup":
        print("setup:", emit("setup", "admin", "Clave-de-prueba-123"))
    print("login:", {k: v for k, v in emit("login", {"username": "admin", "password": "Clave-de-prueba-123",
                                                     "token": ""}).items() if k != "token"})
    if paso == "setup":
        n = emit("addNotification", {"name": "ntfy propio", "type": "ntfy", "isDefault": True,
                                     "ntfyserverurl": "http://ntfy", "ntfytopic": "alertas",
                                     "ntfyPriority": 5, "applyExisting": True}, None)
        print("addNotification:", n)
        nid = n.get("id")
        for m in (dict(type="http", name="Web (HTTP)", url="http://web"),
                  dict(type="port", name="Redis (TCP)", hostname="redis", port=6379),
                  dict(type="dns", name="DNS de web", hostname="web", dns_resolve_server="127.0.0.11",
                       dns_resolve_type="A", port=53)):
            r = emit("add", {**BASE, **m, "notificationIDList": {str(nid): True}})
            print("add:", m["name"], "->", r)
    if paso == "estado":
        lista = emit("getMonitorList") or {}
        time.sleep(float(sys.argv[2]) if len(sys.argv) > 2 else 3)
    sio.disconnect()


if __name__ == "__main__":
    main()
