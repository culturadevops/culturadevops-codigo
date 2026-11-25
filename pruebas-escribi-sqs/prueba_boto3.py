# -*- coding: utf-8 -*-
"""prueba_boto3.py — la prueba del video 217: BOTO3 OFICIAL contra el SQS escrito en Python.

    python prueba_boto3.py http://mi-sqs-py:9324
"""
import sys
import time

import boto3
from botocore.config import Config

destino = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:9324"
sqs = boto3.client("sqs", endpoint_url=destino, aws_access_key_id="x",
                   aws_secret_access_key="x", region_name="us-east-1",
                   config=Config(retries={"max_attempts": 1}))

print("=== boto3 OFICIAL contra un SQS escrito en Python ===")
print("  boto3", boto3.__version__)
print()

url = sqs.create_queue(QueueName="pedidos")["QueueUrl"]
print("  create_queue ->", url)


def cuantos():
    a = sqs.get_queue_attributes(QueueUrl=url, AttributeNames=[
        "ApproximateNumberOfMessages", "ApproximateNumberOfMessagesNotVisible"])["Attributes"]
    return a["ApproximateNumberOfMessages"], a["ApproximateNumberOfMessagesNotVisible"]


print()
print("--- 1 · RECIBIR NO LO SACA DE LA COLA: LO ESCONDE ---")
sqs.send_message(QueueUrl=url, MessageBody="pedido-42")
print("  send_message  -> ok")
print("  en la cola    -> visibles=%s  ocultos=%s" % cuantos())

r = sqs.receive_message(QueueUrl=url, MaxNumberOfMessages=1)
m = r["Messages"][0]
print("  receive       ->", m["Body"], "· entrega nº",
      m["Attributes"]["ApproximateReceiveCount"])
print("  en la cola    -> visibles=%s  ocultos=%s" % cuantos())
print("     ^ NO se ha borrado. Sigue ahí, escondido.")

print()
print("  otro consumidor pide ahora mismo:")
r2 = sqs.receive_message(QueueUrl=url, MaxNumberOfMessages=1)
print("     recibe ->", len(r2.get("Messages", [])), "mensajes (no lo ve: está invisible)")

print()
print("--- 2 · SI NO LO BORRAS, VUELVE ---")
print("  el consumidor se muere sin borrar. Esperamos a que pase la invisibilidad...")
time.sleep(6)
r3 = sqs.receive_message(QueueUrl=url, MaxNumberOfMessages=1)
m3 = r3["Messages"][0]
print("  receive       ->", m3["Body"], "· entrega nº",
      m3["Attributes"]["ApproximateReceiveCount"])
print("     ^ EL MISMO MENSAJE, otra vez. Eso es «al menos una vez».")
print("       Tu consumidor tiene que aguantar duplicados. No es opcional.")

print()
print("--- 3 · EL RECIBO CAMBIA EN CADA ENTREGA ---")
print("  recibo de la 1ª entrega:", m["ReceiptHandle"][:8], "...")
print("  recibo de la 2ª entrega:", m3["ReceiptHandle"][:8], "...")
print("  ^ por eso no se borra con el MessageId: el recibo demuestra que TÚ")
print("    lo recibiste en ESTA vuelta. Con el id no se sabría de qué entrega hablas.")

print()
print("--- 4 · ahora sí, borrando ---")
sqs.delete_message(QueueUrl=url, ReceiptHandle=m3["ReceiptHandle"])
print("  delete_message -> ok")
print("  en la cola     -> visibles=%s  ocultos=%s" % cuantos())
time.sleep(6)
print("  y 6 s después  -> visibles=%s  ocultos=%s" % cuantos())
print("     ^ ahora sí desapareció. Borrar es lo único que lo saca.")
