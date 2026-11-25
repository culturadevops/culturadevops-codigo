# -*- coding: utf-8 -*-
"""Banco del vídeo 411 «¿Vale la pena Google Cloud en 2027?». Sin cuenta: la imagen oficial
gcr.io/google.com/cloudsdktool/google-cloud-cli:emulators trae gcloud y los emuladores.
  · Pub/Sub: tema, suscripción, publicar, sacar, confirmar; y lo que pasa si no confirmas.
  · Firestore: guardar un documento y leerlo por la API REST del emulador.
    python correr.py   -> SALIDA.md
"""
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
OUT = []
IMG = "gcr.io/google.com/cloudsdktool/google-cloud-cli:emulators"
PS = "http://localhost:8085/v1/projects/demo"
FS = "http://localhost:8086/v1/projects/demo/databases/(default)/documents"


def run(args, timeout=None):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return (p.stdout + p.stderr).strip(), p.returncode


def ex(cmd, timeout=None):
    return run(["docker", "exec", "-w", "/work", "gcplab", "bash", "-c", cmd], timeout)


def bloque(titulo, mostrado, cmd, nota=None):
    s, rc = ex(cmd)
    OUT.append(f"### {titulo}\n\n`$ {mostrado}`\n\n```\n{s}\n```\n(código de salida {rc})\n" + (f"\n> {nota}\n" if nota else ""))
    print(f"[{rc}] {titulo}")
    return s, rc


def espera(url):
    for _ in range(60):
        s, _ = ex(f"curl -s -o /dev/null -w '%{{http_code}}' {url}")
        if s not in ("000", ""):
            return
        time.sleep(2)


def main():
    run(["docker", "rm", "-f", "gcplab"])
    run(["docker", "run", "-d", "--name", "gcplab", IMG, "bash", "-c", "mkdir -p /work && sleep infinity"])
    ex("nohup gcloud beta emulators pubsub start --host-port=0.0.0.0:8085 --project=demo > ps.log 2>&1 &")
    ex("nohup gcloud emulators firestore start --host-port=0.0.0.0:8086 > fs.log 2>&1 &")
    espera("http://localhost:8085/")
    espera("http://localhost:8086/")
    OUT.append(f"# SALIDA — Google Cloud en local (vídeo 411)\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con "
               f"`python correr.py`. Sin cuenta: imagen oficial `{IMG}`.\n")

    OUT.append("## 1 · La herramienta\n")
    bloque("versión de gcloud", "gcloud version", "gcloud version 2>/dev/null | head -3")
    s, _ = run(["docker", "image", "inspect", "-f", "{{.Size}}", IMG])
    OUT.append(f"### tamaño de la imagen\n\n`$ docker image inspect -f {{{{.Size}}}} {IMG}`\n\n```\n{s}\n```\n")

    OUT.append("## 2 · Pub/Sub en local\n")
    bloque("arranca el emulador", "gcloud beta emulators pubsub start --project=demo",
           "grep -E 'Server started|listening' ps.log | sed 's/^.*\\] //' | head -2")
    bloque("crear un tema y una suscripción", "curl -X PUT …/topics/pedidos; curl -X PUT …/subscriptions/facturacion",
           f"curl -s -X PUT {PS}/topics/pedidos; echo; "
           f"curl -s -X PUT -H 'Content-Type: application/json' {PS}/subscriptions/facturacion "
           f"-d '{{\"topic\":\"projects/demo/topics/pedidos\",\"ackDeadlineSeconds\":10}}'")
    m1 = "cGVkaWRvIDEwMDE="  # «pedido 1001» en base64
    m2 = "cGVkaWRvIDEwMDI="  # «pedido 1002»
    bloque("publicar dos mensajes", "curl -X POST …/topics/pedidos:publish",
           f"curl -s -X POST -H 'Content-Type: application/json' {PS}/topics/pedidos:publish "
           f"-d '{{\"messages\":[{{\"data\":\"{m1}\"}},{{\"data\":\"{m2}\"}}]}}'")
    s, _ = ex(f"curl -s -X POST -H 'Content-Type: application/json' {PS}/subscriptions/facturacion:pull -d '{{\"maxMessages\":10}}'")
    r = json.loads(s)["receivedMessages"]
    import base64
    lineas = [base64.b64decode(x["message"]["data"]).decode() for x in r]
    OUT.append("### sacarlos (sin confirmar todavía)\n\n`$ curl -X POST …/subscriptions/facturacion:pull`\n\n```\n"
               + "\n".join(lineas) + "\n```\n")
    print("[0] pull")
    ack = r[0]["ackId"]
    bloque("confirmar solo el primero", "curl -X POST …/subscriptions/facturacion:acknowledge",
           f"curl -s -X POST -H 'Content-Type: application/json' {PS}/subscriptions/facturacion:acknowledge "
           f"-d '{{\"ackIds\":[\"{ack}\"]}}'; echo confirmado")
    time.sleep(13)
    s, _ = ex(f"curl -s -X POST -H 'Content-Type: application/json' {PS}/subscriptions/facturacion:pull -d '{{\"maxMessages\":10}}'")
    r2 = json.loads(s).get("receivedMessages", [])
    lineas = [base64.b64decode(x["message"]["data"]).decode() for x in r2] or ["(nada)"]
    OUT.append("### 13 segundos después, volver a sacar\n\n`$ sleep 13; curl -X POST …/subscriptions/facturacion:pull`\n\n```\n"
               + "\n".join(lineas) + "\n```\n\n> El plazo de confirmación era de 10 s: el que no se confirmó vuelve a entregarse.\n")
    print("[0] pull 2")

    OUT.append("## 3 · Firestore en local\n")
    bloque("guardar un documento", "curl -X POST …/documents/clientes?documentId=ana",
           f"curl -s -X POST -H 'Content-Type: application/json' '{FS}/clientes?documentId=ana' "
           "-d '{\"fields\":{\"nombre\":{\"stringValue\":\"Ana\"},\"pedidos\":{\"integerValue\":\"3\"}}}' "
           "| grep -E '\"name\"|stringValue|integerValue'")
    bloque("leerlo", "curl …/documents/clientes/ana",
           f"curl -s '{FS}/clientes/ana' | grep -E 'stringValue|integerValue'")

    (AQUI / "SALIDA.md").write_text("\n".join(OUT), encoding="utf-8")
    print("ok SALIDA.md")


if __name__ == "__main__":
    main()
