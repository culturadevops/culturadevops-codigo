# -*- coding: utf-8 -*-
"""lab.py — las mediciones del vídeo «Almacenamiento en bloque, en fichero o de objetos» (cultura-devops, 356).

Corre DENTRO de la red de Docker, en un contenedor privilegiado (imagen sd-alm-cliente:1 = python 3.13 + boto3
+ nfs-common + e2fsprogs), que monta él mismo:
  · bloque:   /mnt/bloque  ← un dispositivo loop con ext4 (el fichero del disco, en memoria)
  · fichero:  /mnt/nfs     ← NFSv4 exportado por el contenedor «nfs» (en memoria)
  · objetos:  bucket «datos» en MinIO (contenedor «minio», en memoria), por la API S3 con boto3

    python lab.py montar | pequenos | listar | renombrar | anadir | leer
"""
import os
import statistics
import subprocess
import sys
import time

import boto3
from botocore.config import Config

N = 2000
TAM = 4096
s3 = boto3.client("s3", endpoint_url="http://minio:9000", aws_access_key_id="lab", aws_secret_access_key="lab12345",
                  region_name="us-east-1", config=Config(retries={"max_attempts": 1}))
DIRS = {"bloque": "/mnt/bloque", "fichero (NFS)": "/mnt/nfs"}


def sh(c):
    r = subprocess.run(c, shell=True, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"[X] {c}: {r.stdout}{r.stderr}")
    return r.stdout.strip()


def montar():
    sh("mkdir -p /mnt/bloque /mnt/nfs /ram && mount -t tmpfs -o size=1g tmpfs /ram")
    sh("dd if=/dev/zero of=/ram/disco.img bs=1M count=512 status=none && mkfs.ext4 -q /ram/disco.img")
    sh("mount -o loop /ram/disco.img /mnt/bloque")
    sh("mount -t nfs4 nfs:/ /mnt/nfs")
    for d in DIRS.values():
        sh(f"rm -rf {d}/*")
    try:
        s3.create_bucket(Bucket="datos")
    except s3.exceptions.BucketAlreadyOwnedByYou:
        pass


def vaciar_bucket(prefijo=""):
    pag = s3.get_paginator("list_objects_v2")
    for pg in pag.paginate(Bucket="datos", Prefix=prefijo):
        objs = [{"Key": o["Key"]} for o in pg.get("Contents", [])]
        if objs:
            s3.delete_objects(Bucket="datos", Delete={"Objects": objs})


def fila(nombre, seg, n=None, extra=""):
    ops = f" → {n / seg:,.0f} op/s".replace(",", ".") if n else ""
    print(f"  {nombre:<15} {seg:8.3f} s{ops}{extra}")


def pequenos():
    datos = os.urandom(TAM)
    for nombre, d in DIRS.items():
        os.makedirs(f"{d}/fotos", exist_ok=True)
        t0 = time.perf_counter()
        for i in range(N):
            with open(f"{d}/fotos/f{i:05d}.bin", "wb") as f:
                f.write(datos)
                f.flush()
                os.fsync(f.fileno())     # guardado de verdad, como un PUT que ya contestó
        fila(nombre, time.perf_counter() - t0, N, " · con fsync de cada fichero")
    t0 = time.perf_counter()
    for i in range(N):
        s3.put_object(Bucket="datos", Key=f"fotos/f{i:05d}.bin", Body=datos)
    fila("objetos (S3)", time.perf_counter() - t0, N)


def listar():
    for vuelta in (1, 2, 3):
        print(f"  [vuelta {vuelta}]")
        for nombre, d in DIRS.items():
            t0 = time.perf_counter()
            n = len(os.listdir(f"{d}/fotos"))
            fila(nombre, time.perf_counter() - t0, extra=f" · {n} entradas · una llamada")
        t0 = time.perf_counter()
        n, llamadas = 0, 0
        for pg in s3.get_paginator("list_objects_v2").paginate(Bucket="datos", Prefix="fotos/"):
            n += len(pg.get("Contents", []))
            llamadas += 1
        fila("objetos (S3)", time.perf_counter() - t0, extra=f" · {n} objetos · {llamadas} llamadas (1.000 por página)")


def renombrar():
    for nombre, d in DIRS.items():
        t0 = time.perf_counter()
        os.rename(f"{d}/fotos", f"{d}/fotos-2026")
        fila(nombre, time.perf_counter() - t0, extra=" · os.rename de la carpeta: 1 operación")
    t0 = time.perf_counter()
    claves = [o["Key"] for pg in s3.get_paginator("list_objects_v2").paginate(Bucket="datos", Prefix="fotos/")
              for o in pg.get("Contents", [])]
    for k in claves:
        s3.copy_object(Bucket="datos", Key="fotos-2026/" + k.split("/", 1)[1], CopySource={"Bucket": "datos", "Key": k})
    for i in range(0, len(claves), 1000):
        s3.delete_objects(Bucket="datos", Delete={"Objects": [{"Key": k} for k in claves[i:i + 1000]]})
    fila("objetos (S3)", time.perf_counter() - t0,
         extra=f" · no hay rename: {len(claves)} copias + {len(claves)} borrados")


def anadir():
    linea = b"2026-10-11T12:00:00Z pedido pagado\n" * 1      # 35 bytes
    for nombre, d in DIRS.items():
        t0 = time.perf_counter()
        for _ in range(1000):
            with open(f"{d}/registro.log", "ab") as f:
                f.write(linea)
        seg = time.perf_counter() - t0
        fila(nombre, seg, 1000, f" · tamaño final {os.path.getsize(f'{d}/registro.log'):,} B".replace(",", "."))
    s3.put_object(Bucket="datos", Key="registro.log", Body=b"")
    t0 = time.perf_counter()
    for _ in range(1000):
        actual = s3.get_object(Bucket="datos", Key="registro.log")["Body"].read()
        s3.put_object(Bucket="datos", Key="registro.log", Body=actual + linea)
    seg = time.perf_counter() - t0
    tam = s3.head_object(Bucket="datos", Key="registro.log")["ContentLength"]
    fila("objetos (S3)", seg, 1000, f" · tamaño final {tam:,} B · no hay append: GET + PUT del objeto entero".replace(",", "."))
    print(f"  objetos (S3): bytes subidos para añadir 1.000 líneas de 35 B: {sum(35 * i for i in range(1, 1001)):,}".replace(",", "."))


def leer():
    import random
    rnd = random.Random(1)
    idx = [rnd.randrange(N) for _ in range(1000)]
    for nombre, d in DIRS.items():
        ts = []
        for i in idx:
            t0 = time.perf_counter()
            with open(f"{d}/fotos-2026/f{i:05d}.bin", "rb") as f:
                f.read()
            ts.append((time.perf_counter() - t0) * 1000)
        print(f"  {nombre:<15} leer un fichero de 4 KB: mediana {statistics.median(ts):.3f} ms")
    ts = []
    for i in idx:
        t0 = time.perf_counter()
        s3.get_object(Bucket="datos", Key=f"fotos-2026/f{i:05d}.bin")["Body"].read()
        ts.append((time.perf_counter() - t0) * 1000)
    print(f"  {'objetos (S3)':<15} leer un objeto de 4 KB: mediana {statistics.median(ts):.3f} ms")


if __name__ == "__main__":
    montar()
    for a in sys.argv[1:]:
        print(f"$ python lab.py {a}")
        {"pequenos": pequenos, "listar": listar, "renombrar": renombrar, "anadir": anadir, "leer": leer}[a]()
