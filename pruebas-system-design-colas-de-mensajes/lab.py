# -*- coding: utf-8 -*-
"""lab.py — las mediciones del vídeo de colas (cultura-devops, 350). Corre DENTRO de la red de Docker,
junto al contenedor «rabbit» (imagen sd-colas-cliente:1 = python 3.13 + pika 1.3.2).

Los consumidores son procesos hijos. Cuando un consumidor «se cae», se cae él mismo con os._exit justo
después de procesar el mensaje número N y ANTES de confirmarlo: así el punto de la caída es exacto y
los duplicados se pueden contar. Lo que hace cada consumidor se apunta en un fichero de /lab/datos.

    python lab.py autoack | ack1 | ack50 | idempotente | veneno | orden
"""
import multiprocessing as mp
import os
import random
import sys
import time
from collections import Counter, defaultdict

import pika

DATOS = "/lab/datos"
N = 1000


def conexion():
    for _ in range(60):
        try:
            return pika.BlockingConnection(pika.ConnectionParameters("rabbit", heartbeat=30))
        except pika.exceptions.AMQPConnectionError:
            time.sleep(0.5)
    raise SystemExit("[X] no conecta con rabbit")


def nueva_cola(cola, args=None):
    c = conexion()
    ch = c.channel()
    ch.queue_delete(cola)
    ch.queue_declare(cola, durable=True, arguments=args)
    c.close()


def publicar(cola, cuerpos, clave=None):
    c = conexion()
    ch = c.channel()
    ch.confirm_delivery()
    for b in cuerpos:
        ch.basic_publish("", clave(b) if clave else cola, b.encode(), pika.BasicProperties(delivery_mode=2))
    c.close()


def en_cola(cola):
    c = conexion()
    n = c.channel().queue_declare(cola, passive=True).method.message_count
    c.close()
    return n


def log(nombre):
    os.makedirs(DATOS, exist_ok=True)
    return os.path.join(DATOS, nombre)


def leer(nombre):
    f = log(nombre)
    return open(f).read().split() if os.path.exists(f) else []


def consumidor(cola, fichero, auto_ack=False, morir_tras=None, ack_cada=1, idem=False, prefetch=50, espera=0.0):
    c = conexion()
    ch = c.channel()
    ch.basic_qos(prefetch_count=prefetch)
    vistos = set(leer(fichero)) if idem else set()
    n, pend, ultimo = 0, 0, None
    with open(log(fichero), "a") as f:
        for m, _props, body in ch.consume(cola, auto_ack=auto_ack, inactivity_timeout=5):
            if m is None:
                break
            mid = body.decode()
            if not (idem and mid in vistos):     # idempotente: si ya se hizo, solo se confirma
                time.sleep(espera)
                f.write(mid + "\n")
                f.flush()
                vistos.add(mid)
            n += 1
            if morir_tras and n == morir_tras:
                os._exit(1)                      # la caída: procesado, sin confirmar
            if not auto_ack:
                pend, ultimo = pend + 1, m.delivery_tag
                if pend >= ack_cada:
                    ch.basic_ack(ultimo, multiple=True)
                    pend = 0
    if pend:
        ch.basic_ack(ultimo, multiple=True)
    c.close()


def correr(**kw):
    pr = mp.Process(target=consumidor, kwargs=kw)
    pr.start()
    pr.join()
    return pr.exitcode


def informe(fichero, cola):
    hechos = leer(fichero)
    c = Counter(hechos)
    dup = sum(v - 1 for v in c.values())
    print(f"  publicados {N} · procesados {len(hechos)} · distintos {len(c)} · duplicados {dup} · "
          f"perdidos {N - len(c)} · quedan en la cola {en_cola(cola)}")


def caida(nombre, **kw):
    cola = "pedidos-" + nombre
    nueva_cola(cola)
    publicar(cola, [str(i) for i in range(1, N + 1)])
    fichero = nombre + ".log"
    if os.path.exists(log(fichero)):
        os.remove(log(fichero))
    code = correr(cola=cola, fichero=fichero, morir_tras=300, espera=0.001, **kw)
    if code != 1:
        raise SystemExit(f"[X] el consumidor 1 no llegó a caerse en el 300 (código {code}): la prueba no vale")
    print("  consumidor 1: se cae tras procesar el mensaje 300, antes de confirmarlo")
    kw.pop("auto_ack", None)
    correr(cola=cola, fichero=fichero, espera=0.001, **kw)
    print("  consumidor 2: arranca y vacía la cola")
    informe(fichero, cola)


def veneno_consumidor(cola, segundos, contador):
    c = conexion()
    ch = c.channel()
    ch.basic_qos(prefetch_count=10)
    fin = time.time() + segundos
    for m, props, body in ch.consume(cola, inactivity_timeout=0.5):
        if time.time() > fin:
            break
        if m is None:
            continue
        if body == b"veneno":
            contador["veneno"] += 1
            if contador["veneno"] == 1:
                contador["primera"] = time.time()
            contador["ultima"] = time.time()
            ch.basic_nack(m.delivery_tag, requeue=True)   # «falló, vuelve a intentarlo»
        else:
            contador["buenos"] += 1
            ch.basic_ack(m.delivery_tag)
    c.close()


def veneno(tipo):
    cola = f"cobros-{tipo}"
    args = {"x-queue-type": "quorum"} if tipo != "clasica" else None
    if tipo == "quorum-dlq":
        c = conexion()
        ch = c.channel()
        ch.queue_delete("cobros-muertos")
        ch.queue_declare("cobros-muertos", durable=True)
        c.close()
        args.update({"x-delivery-limit": 3, "x-dead-letter-exchange": "", "x-dead-letter-routing-key": "cobros-muertos"})
    nueva_cola(cola, args)
    publicar(cola, ["bueno"] * 50 + ["veneno"] + ["bueno"] * 49)
    cnt = Counter()
    veneno_consumidor(cola, 5, cnt)
    print(f"  en 5 s: {cnt['buenos']} buenos confirmados · el veneno se entregó {cnt['veneno']} veces · "
          f"quedan en la cola {en_cola(cola)}")
    if tipo == "quorum-dlq":
        c = conexion()
        ch = c.channel()
        m, props, body = ch.basic_get("cobros-muertos", auto_ack=True)
        print(f"  cola cobros-muertos: {en_cola('cobros-muertos')} más · leído: {body!r}")
        if props and props.headers:
            d = props.headers.get("x-death", [{}])[0]
            print(f"  x-death: reason={d.get('reason', b'')!s} queue={d.get('queue', b'')!s} count={d.get('count')} "
                  f"x-delivery-count={props.headers.get('x-delivery-count')}")
        c.close()


EVENTOS = ["creado", "pagado", "enviado"]


def orden_consumidor(cola, nombre, semilla):
    rnd = random.Random(semilla)
    c = conexion()
    ch = c.channel()
    ch.basic_qos(prefetch_count=10)
    with open(log(f"orden-{nombre}.log"), "a") as f:
        for m, _p, body in ch.consume(cola, inactivity_timeout=2):
            if m is None:
                break
            time.sleep(rnd.uniform(0, 0.004))          # cada mensaje tarda distinto
            f.write(f"{time.time_ns()} {body.decode()}\n")
            f.flush()
            ch.basic_ack(m.delivery_tag)
    c.close()


def orden_informe(nombres):
    filas = []
    for n in nombres:
        lineas = open(log(f"orden-{n}.log")).read().split("\n")
        filas += [(int(l.split()[0]), l.split()[1], n) for l in lineas if l]
    filas.sort()
    por_pedido = defaultdict(list)
    for _, b, _n in filas:
        ped, ev = b.split(":")
        por_pedido[ped].append(EVENTOS.index(ev))
    mal = sum(1 for v in por_pedido.values() if v != sorted(v))
    reparto = Counter(n for *_x, n in filas)
    print(f"  pedidos: {len(por_pedido)} · procesados fuera de orden: {mal} · "
          + " · ".join(f"{k} hizo {v}" for k, v in sorted(reparto.items())))
    ejemplo = next((k for k, v in por_pedido.items() if v != sorted(v)), None)
    if ejemplo:
        print(f"  ejemplo, pedido {ejemplo}: " + " → ".join(EVENTOS[i] for i in por_pedido[ejemplo]))


def orden(modo):
    for f in os.listdir(DATOS) if os.path.exists(DATOS) else []:
        if f.startswith("orden-"):
            os.remove(log(f))
    cuerpos = [f"p{p}:{e}" for p in range(1, 201) for e in EVENTOS]
    if modo == "dos":
        nueva_cola("eventos")
        publicar("eventos", cuerpos)
        ps = [mp.Process(target=orden_consumidor, args=("eventos", f"c{i}", i)) for i in (1, 2)]
    elif modo == "unico":
        nueva_cola("eventos", {"x-single-active-consumer": True})
        publicar("eventos", cuerpos)
        ps = [mp.Process(target=orden_consumidor, args=("eventos", f"c{i}", i)) for i in (1, 2)]
    else:   # una cola por partición: el mismo pedido siempre a la misma
        for i in (0, 1):
            nueva_cola(f"eventos-{i}")
        publicar(None, cuerpos, clave=lambda b: f"eventos-{int(b.split(':')[0][1:]) % 2}")
        ps = [mp.Process(target=orden_consumidor, args=(f"eventos-{i}", f"c{i + 1}", i + 1)) for i in (0, 1)]
    for pr in ps:
        pr.start()
    for pr in ps:
        pr.join()
    orden_informe([f"c{i}" for i in (1, 2)])


if __name__ == "__main__":
    mp.set_start_method("fork")
    a = sys.argv[1]
    if a == "autoack":
        caida("autoack", auto_ack=True)
    elif a == "ack1":
        caida("ack1")
    elif a == "ack50":
        caida("ack50", ack_cada=50)
    elif a == "idempotente":
        caida("idempotente", ack_cada=50, idem=True)
    elif a.startswith("veneno-"):
        veneno(a.split("-", 1)[1])
    elif a.startswith("orden-"):
        orden(a.split("-", 1)[1])
