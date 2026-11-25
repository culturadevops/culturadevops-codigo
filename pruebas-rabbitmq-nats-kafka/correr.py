# -*- coding: utf-8 -*-
"""RabbitMQ vs NATS vs Kafka — banco de pruebas del vídeo 342 (cultura-devops, serie versus).

La MISMA pregunta para los tres: si envío mensajes y el consumidor NO está, ¿qué pasa cuando
llega? Ahí está la diferencia de fondo. Además: rendimiento orientativo con la herramienta nativa
de cada uno, y memoria. Red Docker `mq`.

  · RabbitMQ 4 (cola clásica durable)      · NATS 2 (core y JetStream)      · Kafka 4 (KRaft)

    python correr.py
"""
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RABBIT = "rabbitmq:4-management"
NATS = "nats:latest"
NATSBOX = "natsio/nats-box:latest"
KAFKA = "apache/kafka:latest"
KBIN = "/opt/kafka/bin"
salida = []


def sh(cmd, timeout=900):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return (r.stdout + r.stderr).strip()


def anota(titulo, cmd_txt, texto):
    salida.extend(["", f"### {titulo}", "", f"`$ {cmd_txt}`", "", "```", texto.strip(), "```"])
    print(f"--- {titulo}\n{texto.strip()[:1400]}\n", flush=True)


def natsbox(script, timeout=300):
    return sh(["docker", "run", "--rm", "--network", "mq", NATSBOX, "sh", "-c", script], timeout=timeout)


def kafka(script, timeout=600):
    return sh(["docker", "exec", "kafka", "sh", "-c", script], timeout=timeout)


def pika(script, timeout=300):
    import base64
    b64 = base64.b64encode(script.encode()).decode()
    return sh(["docker", "run", "--rm", "--network", "mq", "-e", "PYTHONUNBUFFERED=1", "python:3.12-slim",
               "sh", "-c", f"pip install pika -q 2>/dev/null; echo {b64} | base64 -d | python"], timeout=timeout)


def main():
    sh(["docker", "rm", "-f", "rabbit", "nats", "kafka"])
    sh(["docker", "network", "rm", "mq"])
    sh(["docker", "network", "create", "mq"])
    sh(["docker", "run", "-d", "--name", "rabbit", "--network", "mq", RABBIT])
    sh(["docker", "run", "-d", "--name", "nats", "--network", "mq", NATS, "-js"])
    sh(["docker", "run", "-d", "--name", "kafka", "--network", "mq",
        "-e", "KAFKA_NODE_ID=1", "-e", "KAFKA_PROCESS_ROLES=broker,controller",
        "-e", "KAFKA_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093",
        "-e", "KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092",
        "-e", "KAFKA_CONTROLLER_QUORUM_VOTERS=1@kafka:9093",
        "-e", "KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER",
        "-e", "KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT",
        "-e", "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1",
        "-e", "KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS=0", KAFKA])
    # esperar
    for _ in range(60):
        if "running" in sh(["docker", "exec", "rabbit", "rabbitmqctl", "await_startup", "&&", "echo", "running"]) \
           or sh(["docker", "exec", "rabbit", "rabbitmq-diagnostics", "-q", "ping"]).startswith("Ping"):
            break
        time.sleep(2)
    for _ in range(40):
        if "9092" in kafka(f"{KBIN}/kafka-topics.sh --bootstrap-server kafka:9092 --list 2>&1 || echo no"):
            break
        if kafka(f"{KBIN}/kafka-broker-api-versions.sh --bootstrap-server kafka:9092 >/dev/null 2>&1 && echo ok") == "ok":
            break
        time.sleep(2)
    time.sleep(5)

    salida.append("\n## 1 · Versiones")
    anota("versiones", "rabbitmqctl / nats-server / kafka",
          "RabbitMQ " + sh(["docker", "exec", "rabbit", "rabbitmqctl", "version"]).splitlines()[-1]
          + "\nNATS " + sh(["docker", "run", "--rm", NATS, "--version"]).split()[-1]
          + "\nKafka " + kafka(f"{KBIN}/kafka-topics.sh --version"))

    salida.append("\n## 2 · La prueba clave: envío SIN consumidor, y luego llego")
    # RabbitMQ: cola durable, publico 10, luego consumo
    pub = ("import pika,sys\n"
           "c=pika.BlockingConnection(pika.ConnectionParameters('rabbit'))\n"
           "ch=c.channel(); ch.queue_declare(queue='pedidos',durable=True)\n"
           "[ch.basic_publish('', 'pedidos', f'pedido-{i}'.encode(),"
           "pika.BasicProperties(delivery_mode=2)) for i in range(10)]\n"
           "print('publicados 10'); c.close()")
    con = ("import pika\n"
           "c=pika.BlockingConnection(pika.ConnectionParameters('rabbit'))\n"
           "ch=c.channel(); ch.queue_declare(queue='pedidos',durable=True)\n"
           "n=0\n"
           "while True:\n"
           "  m,p,b=ch.basic_get('pedidos',auto_ack=True)\n"
           "  if b is None: break\n"
           "  n+=1\n"
           "print('el consumidor recibió',n,'mensajes'); c.close()")
    anota("RabbitMQ: publico 10 sin consumidor, luego consumo", "pika publish ×10 → basic_get",
          pika(pub) + "\n" + pika(con))
    # NATS core: pub 10 sin sub, luego sub con timeout de shell
    anota("NATS (core): publico 10 sin suscriptor, luego me suscribo", "nats pub ×10 → timeout 6 nats sub",
          natsbox("for i in $(seq 1 10); do nats -s nats://nats:4222 pub pedidos \"pedido-$i\" >/dev/null; done; "
                  "echo 'publicados 10'; "
                  "N=$(timeout 6 nats -s nats://nats:4222 sub pedidos --count=10 2>&1 | grep -c Received); "
                  "echo \"el consumidor recibió $N mensajes\""))
    # NATS JetStream: stream con persistencia, pub 10, ver que quedan guardados
    anota("NATS (JetStream): con persistencia", "nats stream add; pub ×10; stream info",
          natsbox("nats -s nats://nats:4222 stream add PEDIDOS --subjects 'js.pedidos' --defaults >/dev/null 2>&1; "
                  "for i in $(seq 1 10); do nats -s nats://nats:4222 pub js.pedidos \"pedido-$i\" >/dev/null; done; "
                  "echo 'publicados 10 en el stream'; "
                  "nats -s nats://nats:4222 stream info PEDIDOS 2>&1 | grep -iE '^ *Messages:' | head -1 | sed 's/^ */guardados → /'"))
    # Kafka: topic, produce 10 sin consumer, luego consume --from-beginning
    kafka(f"{KBIN}/kafka-topics.sh --bootstrap-server kafka:9092 --create --topic pedidos --partitions 1 --replication-factor 1 2>/dev/null")
    anota("Kafka: produzco 10 sin consumidor, luego leo desde el principio", "kafka-console-producer → consumer --from-beginning",
          kafka("for i in $(seq 1 10); do echo pedido-$i; done | "
                f"{KBIN}/kafka-console-producer.sh --bootstrap-server kafka:9092 --topic pedidos 2>/dev/null; echo 'publicados 10'; "
                f"timeout 10 {KBIN}/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic pedidos "
                "--from-beginning --timeout-ms 5000 2>/dev/null | grep -c pedido- | sed 's/^/el consumidor recibió /'"))

    salida.append("\n## 3 · Kafka: otro consumidor vuelve a leerlo todo")
    anota("un segundo grupo lee desde el principio", "kafka-console-consumer --group otro --from-beginning",
          kafka(f"timeout 10 {KBIN}/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic pedidos "
                "--from-beginning --timeout-ms 5000 2>/dev/null | grep -c pedido- | sed 's/^/el 2.º consumidor recibió /'"))
    anota("RabbitMQ: la cola ya está vacía", "basic_get otra vez",
          pika(con))

    salida.append("\n## 4 · Rendimiento orientativo (herramienta nativa de cada uno)")
    nb = natsbox("nats -s nats://nats:4222 bench pub bench.test --msgs 100000 --size 128 2>&1")
    anota("NATS: nats bench pub", "nats bench pub (100k mensajes de 128 B)",
          "\n".join(l.strip() for l in nb.splitlines() if "msgs/sec" in l or "Pub stats" in l)[:400] or nb[-400:])
    anota("Kafka: kafka-producer-perf-test", "100k mensajes de 128 B",
          "\n".join(l for l in kafka(
              f"{KBIN}/kafka-producer-perf-test.sh --topic perf --num-records 100000 --record-size 128 "
              "--throughput -1 --producer-props bootstrap.servers=kafka:9092 2>&1").splitlines() if "records/sec" in l)[-400:])
    anota("memoria de cada broker (en reposo)", "docker stats --no-stream",
          sh(["docker", "stats", "--no-stream", "--format", "{{.Name}} {{.MemUsage}}", "rabbit", "nats", "kafka"]))

    sh(["docker", "rm", "-f", "rabbit", "nats", "kafka"])
    sh(["docker", "network", "rm", "mq"])
    cab = ["# SALIDA — RabbitMQ vs NATS vs Kafka (vídeo 342)", "",
           f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. "
           "RabbitMQ 4, NATS 2.15 (core + JetStream), Kafka 4 (KRaft)."]
    (AQUI / "SALIDA.md").write_text("\n".join(cab + salida) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
