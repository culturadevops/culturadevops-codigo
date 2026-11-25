# -*- coding: utf-8 -*-
"""prueba_boto3.py — la prueba del video 215: BOTO3 OFICIAL contra el S3 escrito en Python.

Esto NO importa nada de `s3_py.py`. Habla por la red, como boto3 hablaria con Amazon. Lo unico
que cambia respecto a produccion es `endpoint_url`.

⚠️ `addressing_style='path'` porque boto3 usa por defecto el estilo de host virtual
(`micubo.s3.amazonaws.com`), que contra un servidor local no resuelve. Es exactamente el ajuste
que documenta LocalStack, y en el video se dice por que hace falta.

    python prueba_boto3.py http://mi-s3-py:9000
"""
import sys

import boto3
from botocore.config import Config

destino = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:9000"

s3 = boto3.client(
    "s3",
    endpoint_url=destino,                     # <- LO UNICO que cambia respecto a produccion
    aws_access_key_id="lo-que-sea",
    aws_secret_access_key="lo-que-sea",
    region_name="us-east-1",
    config=Config(s3={"addressing_style": "path"}, retries={"max_attempts": 1}),
)

print("=== boto3 OFICIAL contra un S3 escrito en Python ===")
print("  boto3", boto3.__version__)
print()

print("--- lo basico ---")
s3.create_bucket(Bucket="facturas")
print("  create_bucket  -> ok")
r = s3.put_object(Bucket="facturas", Key="hola.txt", Body=b"hola mundo")
print("  put_object     -> ETag", r["ETag"])
r = s3.get_object(Bucket="facturas", Key="hola.txt")
print("  get_object     ->", r["Body"].read().decode())
print("  head_object    -> ContentLength",
      s3.head_object(Bucket="facturas", Key="hola.txt")["ContentLength"])
print("  list_buckets   ->", [b["Name"] for b in s3.list_buckets()["Buckets"]])

print()
print("--- el ETag es el MD5, y boto3 lo lee ---")
import hashlib
esperado = hashlib.md5(b"hola mundo").hexdigest()
print("  md5 local      =", esperado)
print("  ETag del server=", r["ETag"] if False else
      s3.head_object(Bucket="facturas", Key="hola.txt")["ETag"].strip('"'))

print()
print("--- LAS CARPETAS NO EXISTEN: son claves planas ---")
for k in ["2026/01/f1.pdf", "2026/01/f2.pdf", "2026/02/f3.pdf", "raiz.txt"]:
    s3.put_object(Bucket="facturas", Key=k, Body=b"x")
todo = s3.list_objects_v2(Bucket="facturas")
print("  todas las claves, planas:")
for o in todo["Contents"]:
    print("     ", o["Key"])

print()
print("  y ahora el MISMO almacen, listado con delimiter='/':")
r = s3.list_objects_v2(Bucket="facturas", Delimiter="/")
print("     ficheros :", [o["Key"] for o in r.get("Contents", [])])
print("     'carpetas':", [p["Prefix"] for p in r.get("CommonPrefixes", [])])
print("     ^ eso lo calcula el LISTADO. No hay ninguna carpeta guardada.")

print()
r = s3.list_objects_v2(Bucket="facturas", Prefix="2026/", Delimiter="/")
print("  con Prefix='2026/' y delimiter='/':")
print("     'carpetas':", [p["Prefix"] for p in r.get("CommonPrefixes", [])])

print()
print("--- por eso RENOMBRAR UNA CARPETA no existe ---")
print("  para renombrar 2026/01/ hay que copiar y borrar objeto a objeto:")
origen = [o["Key"] for o in s3.list_objects_v2(Bucket="facturas", Prefix="2026/01/")["Contents"]]
for k in origen:
    cuerpo = s3.get_object(Bucket="facturas", Key=k)["Body"].read()
    s3.put_object(Bucket="facturas", Key=k.replace("2026/01/", "2026/enero/"), Body=cuerpo)
    s3.delete_object(Bucket="facturas", Key=k)
    print(f"     {k}  ->  {k.replace('2026/01/', '2026/enero/')}")
r = s3.list_objects_v2(Bucket="facturas", Prefix="2026/", Delimiter="/")
print("     'carpetas' despues:", [p["Prefix"] for p in r.get("CommonPrefixes", [])])
print("     ^ 4 llamadas por fichero. Con 10.000 ficheros, 40.000 llamadas.")

print()
print("--- lo que pasa cuando la clave no existe ---")
try:
    s3.get_object(Bucket="facturas", Key="no-existe")
except s3.exceptions.NoSuchKey as e:
    print("  boto3 levanta su excepcion tipada:", type(e).__name__)
