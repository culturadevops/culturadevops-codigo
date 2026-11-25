# -*- coding: utf-8 -*-
"""Banco extra del vídeo 411 (necesita el contenedor gcplab de correr.py, con los dos emuladores en marcha).
  · Pub/Sub, un mensaje a dos suscripciones: cada una recibe su copia (no es una cola).
  · Firestore: tres clientes y una consulta (pedidos > 2) con runQuery.
    python correr_extra.py   -> SALIDA-extra.md
"""
import base64
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
OUT = []
PS = "http://localhost:8085/v1/projects/demo"
FS = "http://localhost:8086/v1/projects/demo/databases/(default)/documents"
J = "-H 'Content-Type: application/json'"


def run(args):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (p.stdout + p.stderr).strip(), p.returncode


def ex(cmd):
    return run(["docker", "exec", "-w", "/work", "gcplab", "bash", "-c", cmd])


def texto(s):
    return [base64.b64decode(x["message"]["data"]).decode() for x in json.loads(s).get("receivedMessages", [])] or ["(nada)"]


def main():
    OUT.append(f"# SALIDA extra — Google Cloud en local (vídeo 411)\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr_extra.py`.\n")
    OUT.append("## 1 · Un mensaje, dos suscripciones\n")
    ex(f"curl -s -X PUT {PS}/topics/altas")
    for sub in ("facturacion-altas", "envios-altas"):
        ex(f"curl -s -X PUT {J} {PS}/subscriptions/{sub} -d '{{\"topic\":\"projects/demo/topics/altas\"}}'")
    OUT.append("### un tema, dos suscripciones\n\n`$ curl …/topics/altas/subscriptions`\n\n```\n"
               + ex(f"curl -s {PS}/topics/altas/subscriptions | grep projects/")[0] + "\n```\n")
    msg = base64.b64encode("pedido 2001".encode()).decode()
    s, _ = ex(f"curl -s -X POST {J} {PS}/topics/altas:publish -d '{{\"messages\":[{{\"data\":\"{msg}\"}}]}}'")
    OUT.append(f"### publicar UN mensaje\n\n`$ curl -X POST …/topics/altas:publish`\n\n```\n{s}\n```\n")
    for sub in ("facturacion-altas", "envios-altas"):
        s, _ = ex(f"curl -s -X POST {J} {PS}/subscriptions/{sub}:pull -d '{{\"maxMessages\":10}}'")
        OUT.append(f"### lo que recibe {sub}\n\n`$ curl -X POST …/subscriptions/{sub}:pull`\n\n```\n" + "\n".join(texto(s)) + "\n```\n")
    print("[0] fan-out")

    OUT.append("## 2 · Firestore: una consulta\n")
    for nombre, n in (("luis", 1), ("marta", 5), ("pedro", 2)):
        ex(f"curl -s -X POST {J} '{FS}/clientes?documentId={nombre}' "
           f"-d '{{\"fields\":{{\"nombre\":{{\"stringValue\":\"{nombre.capitalize()}\"}},\"pedidos\":{{\"integerValue\":\"{n}\"}}}}}}'")
    q = json.dumps({"structuredQuery": {"from": [{"collectionId": "clientes"}],
                    "where": {"fieldFilter": {"field": {"fieldPath": "pedidos"}, "op": "GREATER_THAN", "value": {"integerValue": "2"}}}}})
    s, _ = ex(f"curl -s -X POST {J} '{FS}:runQuery' -d '{q}'")
    filas = [f"{d['document']['fields']['nombre']['stringValue']}: {d['document']['fields']['pedidos']['integerValue']} pedidos"
             for d in json.loads(s) if "document" in d]
    s2, _ = ex(f"curl -s '{FS}/clientes?pageSize=50' | grep -c '\"nombre\"'")
    OUT.append(f"### cuántos clientes hay\n\n`$ curl …/documents/clientes | grep -c nombre`\n\n```\n{s2}\n```\n")
    OUT.append("### clientes con más de 2 pedidos\n\n`$ curl -X POST …/documents:runQuery  (where pedidos > 2)`\n\n```\n"
               + "\n".join(filas) + "\n```\n")
    print("[0] query")
    (AQUI / "SALIDA-extra.md").write_text("\n".join(OUT), encoding="utf-8")
    print("ok SALIDA-extra.md")


if __name__ == "__main__":
    main()
