# -*- coding: utf-8 -*-
"""prueba_boto3.py — la prueba del video 216: BOTO3 OFICIAL contra el DynamoDB escrito en Python.

    python prueba_boto3.py http://mi-dynamo-py:8000
"""
import sys
import time
from decimal import Decimal

import boto3
from botocore.config import Config

destino = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
comun = dict(endpoint_url=destino, aws_access_key_id="x", aws_secret_access_key="x",
             region_name="us-east-1", config=Config(retries={"max_attempts": 1}))
cli = boto3.client("dynamodb", **comun)
res = boto3.resource("dynamodb", **comun)

print("=== boto3 OFICIAL contra un DynamoDB escrito en Python ===")
print("  boto3", boto3.__version__)
print()

cli.create_table(
    TableName="pedidos",
    AttributeDefinitions=[{"AttributeName": "cliente", "AttributeType": "S"},
                          {"AttributeName": "pedido", "AttributeType": "S"}],
    KeySchema=[{"AttributeName": "cliente", "KeyType": "HASH"},
               {"AttributeName": "pedido", "KeyType": "RANGE"}],
    BillingMode="PAY_PER_REQUEST")
print("--- create_table -> ok (cliente = partición, pedido = ordenación)")

t = res.Table("pedidos")
t.put_item(Item={"cliente": "ana", "pedido": "p1", "total": Decimal("19.99")})
print("  put_item        -> ok")
print("  get_item        ->", t.get_item(Key={"cliente": "ana", "pedido": "p1"})["Item"])

print()
print("--- 1 · POR QUÉ RECHAZA 19,99 SI LO MANDAS COMO FLOAT ---")
try:
    t.put_item(Item={"cliente": "ana", "pedido": "p2", "total": 19.99})
    print("  lo aceptó (no debería)")
except TypeError as e:
    print("  boto3 se niega ANTES de salir a la red:")
    print("   ", str(e)[:120])
print("  y por el cable los números viajan como CADENA. Míralo en crudo:")
crudo = cli.get_item(TableName="pedidos",
                     Key={"cliente": {"S": "ana"}, "pedido": {"S": "p1"}})["Item"]
print("   ", crudo)
print("    ^ {'N': '19.99'} — texto. Un float ya trae el error de coma flotante metido,")
print("      así que el protocolo transporta la cifra tal cual la escribiste.")

print()
print("--- 2 · QUERY Y SCAN NO SON LA MISMA OPERACIÓN ---")
for c in range(200):                      # 200 clientes...
    for p in range(5):                    # ...con 5 pedidos cada uno = 1.000 items
        t.put_item(Item={"cliente": f"c{c:03d}", "pedido": f"p{p}",
                         "total": Decimal("10.00")})
print("  metidos 1.000 items (200 clientes x 5 pedidos)")
print()

t0 = time.perf_counter()
q = t.query(KeyConditionExpression=boto3.dynamodb.conditions.Key("cliente").eq("c042"))
tq = (time.perf_counter() - t0) * 1000
t0 = time.perf_counter()
s = t.scan(FilterExpression=boto3.dynamodb.conditions.Attr("cliente").eq("c042"))
ts = (time.perf_counter() - t0) * 1000

print(f"  query('c042') -> {q['Count']} items · {tq:.1f} ms")
print(f"  scan (mismo)  -> {s['Count']} items · {ts:.1f} ms")
print()
toc = cli.meta.events  # solo para no romper linters
import urllib.request, json as _j
req = urllib.request.Request(destino, data=b"{}",
                             headers={"X-Amz-Target": "DynamoDB_20120810.Tocados",
                                      "Content-Type": "application/x-amz-json-1.0"})
tocados = _j.loads(urllib.request.urlopen(req).read())
print("  ITEMS QUE TOCÓ EL SERVIDOR POR DENTRO:")
print(f"     Query -> {tocados['Query']}   (solo su partición)")
print(f"     Scan  -> {tocados['Scan']}   (la tabla entera)")
print("     ^ mismo resultado, mismo filtro, y uno leyó 5 y el otro 1.000.")
print("       Con 3 filas parecen iguales. Ese es el vídeo.")

print()
print("--- 3 · el FilterExpression NO ahorra lectura ---")
print(f"  scan devolvió Count={s['Count']} pero ScannedCount={s['ScannedCount']}")
print("  ^ te cobran por lo escaneado, no por lo devuelto.")
