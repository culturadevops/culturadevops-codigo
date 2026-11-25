# -*- coding: utf-8 -*-
"""Banco extra 2 del vídeo 409: Azure Queue Storage en local con Azurite (azurite-queue) y la misma CLI.
  · crear una cola, meter dos mensajes, leer uno (queda invisible un rato), borrarlo, y ver cuántos quedan.
    python correr_extra2.py   -> SALIDA-extra2.md   (necesita el contenedor azcli de correr_extra.py)
"""
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
OUT = []
NET = "lab-azure"
CONN = ("DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
        "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
        "QueueEndpoint=http://azuriteq:10001/devstoreaccount1;")


def run(args):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (p.stdout + p.stderr).strip(), p.returncode


def ex(cmd):
    return run(["docker", "exec", "-w", "/work", "azcli", "bash", "-c", cmd])


def bloque(titulo, mostrado, cmd):
    s, rc = ex(cmd)
    s = "\n".join(l for l in s.splitlines() if "update(s) available" not in l and "az upgrade" not in l)
    OUT.append(f"### {titulo}\n\n`$ {mostrado}`\n\n```\n{s}\n```\n(código de salida {rc})\n")
    print(f"[{rc}] {titulo}")
    return s, rc


def main():
    run(["docker", "rm", "-f", "azuriteq"])
    run(["docker", "run", "-d", "--name", "azuriteq", "--network", NET, "mcr.microsoft.com/azure-storage/azurite",
         "azurite-queue", "--queueHost", "0.0.0.0", "--skipApiVersionCheck"])
    time.sleep(4)
    c = f"--connection-string '{CONN}' --only-show-errors"
    OUT.append(f"# SALIDA extra 2 — colas en Azurite (vídeo 409)\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr_extra2.py`.\n")
    bloque("crear la cola", "az storage queue create -n pedidos …", f"az storage queue create -n pedidos {c} -o json")
    bloque("meter dos mensajes", "az storage message put -q pedidos --content … (x2)",
           f"az storage message put -q pedidos --content 'pedido 1001' {c} -o none && "
           f"az storage message put -q pedidos --content 'pedido 1002' {c} -o none && echo 'dos mensajes'")
    bloque("mirar sin sacar", "az storage message peek -q pedidos --num-messages 5 …",
           f"az storage message peek -q pedidos --num-messages 5 {c} --query '[].content' -o tsv")
    s, _ = ex(f"az storage message get -q pedidos --visibility-timeout 30 {c} -o json")
    m = json.loads(s[s.index("["):])[0]
    OUT.append(f"### un trabajador saca uno (invisible 30 s)\n\n`$ az storage message get -q pedidos --visibility-timeout 30 …`\n\n"
               f"```\ncontenido: {m['content']}\nveces sacado: {m['dequeueCount']}\n```\n")
    print("[0] get")
    bloque("lo que ven los demás mientras tanto", "az storage message peek -q pedidos --num-messages 5 …",
           f"az storage message peek -q pedidos --num-messages 5 {c} --query '[].content' -o tsv")
    bloque("terminado: lo borra", "az storage message delete --id … --pop-receipt …",
           f"az storage message delete -q pedidos --id '{m['id']}' --pop-receipt '{m['popReceipt']}' {c} -o none && echo borrado")
    bloque("cuántos quedan", "az storage queue metadata show / peek …",
           f"az storage message peek -q pedidos --num-messages 5 {c} --query '[].content' -o tsv")
    (AQUI / "SALIDA-extra2.md").write_text("\n".join(OUT), encoding="utf-8")
    print("ok SALIDA-extra2.md")


if __name__ == "__main__":
    main()
