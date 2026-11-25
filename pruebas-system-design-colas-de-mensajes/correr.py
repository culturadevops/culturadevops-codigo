# -*- coding: utf-8 -*-
"""correr.py — banco del vídeo «System design: colas de mensajes, lo que garantizan y lo que no» (cd, 350).

RabbitMQ 4 en Docker; las mediciones las hace lab.py dentro de la red (imagen sd-colas-cliente:1).

  1 auto-ack y un consumidor que se cae · 2 ack manual: uno a uno y en lotes de 50 · 3 consumidor idempotente
  4 el mensaje veneno: cola clásica, cola quorum, quorum con límite y cola de mensajes muertos
  5 el orden con dos consumidores, con consumidor único y con una cola por partición

    python correr.py      -> SALIDA.md
"""
import datetime
import os
import shutil
import subprocess
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ENV = dict(os.environ, MSYS_NO_PATHCONV="1")
RED, SUBRED = "sd-colas", "10.77.26.0/24"
RABBIT, CLIENTE = "rabbitmq:4.1.4-alpine", "sd-colas-cliente:1"
salida = []


def p(t=""):
    print(t, flush=True)
    salida.append(t)


def docker(*a, check=False):
    r = subprocess.run(["docker", *a], capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    if check and r.returncode:
        raise SystemExit(f"[X] docker {' '.join(a[:3])}: {r.stdout}{r.stderr}")
    return (r.stdout + r.stderr).strip()


def lab(modo, mostrar):
    p(f"$ python lab.py {modo}   # {mostrar}")
    for l in docker("run", "--rm", "--network", RED, "-v", f"{AQUI.as_posix()}:/lab", "-w", "/lab", CLIENTE,
                    "python", "lab.py", modo).splitlines():
        p("  " + l.strip())


def limpiar():
    docker("rm", "-f", "rabbit")
    docker("network", "rm", RED)


def main():
    if not docker("images", "-q", CLIENTE):
        (AQUI / "_cliente").mkdir(exist_ok=True)
        (AQUI / "_cliente" / "Dockerfile").write_text("FROM python:3.13-slim\nRUN pip install --no-cache-dir pika==1.3.2\n",
                                                      encoding="utf-8")
        docker("build", "-t", CLIENTE, str(AQUI / "_cliente"), check=True)
    limpiar()
    shutil.rmtree(AQUI / "datos", ignore_errors=True)
    docker("network", "create", "--subnet", SUBRED, RED, check=True)
    try:
        # el entrypoint de la imagen falla en este Docker (eacces al leer .erlang.cookie): se arranca el servidor directo
        docker("run", "-d", "--name", "rabbit", "--hostname", "rabbit", "--network", RED, "--user", "0",
               "--entrypoint", "rabbitmq-server", RABBIT, check=True)
        for _ in range(120):
            if "Ping succeeded" in docker("exec", "rabbit", "rabbitmq-diagnostics", "ping"):
                break
            time.sleep(1)
        time.sleep(3)
        cab = ["# SALIDA — «System design: colas de mensajes» (cultura-devops, vídeo 350)", "",
               "> Generado por `correr.py`. **No se escribe a mano.**", "",
               f"- fecha: `{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%SZ}`",
               f"- RabbitMQ {docker('exec', 'rabbit', 'rabbitmqctl', 'version')} · cliente Python 3.13 + pika 1.3.2",
               "- 1.000 mensajes por prueba; el consumidor «se cae» con os._exit justo después de procesar el 300 "
               "y antes de confirmarlo.", "- una sola máquina."]
        salida.append("\n```")
        p("== 1 · Confirmación automática (auto-ack) y un consumidor que se cae ==")
        lab("autoack", "auto_ack=True")
        p("")
        p("== 2 · Confirmación manual (ack después de procesar) ==")
        lab("ack1", "un ack por mensaje")
        lab("ack50", "un ack cada 50 mensajes")
        p("")
        p("== 3 · Consumidor idempotente (recuerda lo que ya hizo) ==")
        lab("idempotente", "un ack cada 50, y salta lo que ya está hecho")
        p("")
        p("== 4 · El mensaje veneno: falla siempre y se devuelve a la cola ==")
        lab("veneno-clasica", "cola clásica, nack con requeue")
        lab("veneno-quorum", "cola quorum, sin configurar nada")
        lab("veneno-quorum-dlq", "cola quorum, x-delivery-limit 3 y cola de mensajes muertos")
        p("")
        p("== 5 · El orden: 200 pedidos × (creado, pagado, enviado) ==")
        lab("orden-dos", "una cola, dos consumidores")
        lab("orden-unico", "una cola con x-single-active-consumer")
        lab("orden-particion", "dos colas, el pedido va siempre a la misma")
        salida.append("```")
    finally:
        limpiar()
    (AQUI / "SALIDA.md").write_bytes(("\n".join(cab) + "\n" + "\n".join(salida) + "\n").encode("utf-8"))
    print("\n[ok] SALIDA.md")


if __name__ == "__main__":
    main()
