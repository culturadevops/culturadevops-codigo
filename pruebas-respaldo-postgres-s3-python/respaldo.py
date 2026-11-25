# -*- coding: utf-8 -*-
"""respaldo.py — respaldo de Postgres a S3 con Python (cultura-devops, vídeo 798).

pg_dump -Fc corre como subproceso y su salida va DIRECTA a S3 por partes con boto3 (upload_fileobj):
nada se escribe en disco y nada se carga entero en memoria. Las variables de entorno son las de libpq
(PGHOST, PGUSER, PGPASSWORD) y las del SDK (AWS_ENDPOINT_URL, AWS_REGION...).

    respaldo.py bucket
    respaldo.py respaldar  --base tienda --fecha 2026-11-05T0300 [--modo fc|z0+gzip|z0+gzip-corto]
    respaldo.py sin-wait   --base tienda --fecha ...     (el error: no mira el código de salida de pg_dump)
    respaldo.py ingenuo    --base tienda --fecha ...     (el error: todo a memoria y después put_object)
    respaldo.py listar     [--base tienda]
    respaldo.py retener    --base inventario --ultimos 3 --dias 7 [--borrar]
    respaldo.py restaurar  --clave respaldos/tienda/...  (a una base NUEVA en PGHOST_DESTINO)
    respaldo.py verificar  (cuenta filas y suma en origen y restaurada)
"""
import argparse
import os
import resource
import subprocess
import sys
import zlib
from datetime import datetime, timedelta

import boto3
from boto3.s3.transfer import TransferConfig

BUCKET = os.environ.get("BUCKET", "respaldos-demo")
PARTE = 8 * 1024 * 1024
CONFIG = TransferConfig(multipart_threshold=PARTE, multipart_chunksize=PARTE, max_concurrency=4)
s3 = boto3.client("s3")


def mb(n):
    return f"{n / 1e6:.1f} MB"


def pico():
    # ru_maxrss en Linux viene en KiB: memoria pico de ESTE proceso de Python (pg_dump es otro proceso)
    return f"{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024:.0f} MB"


def clave(base, fecha, modo):
    return f"respaldos/{base}/{fecha}.dump" + (".gz" if "gzip" in modo else "")


class Tubo:
    """Envuelve la salida de pg_dump como un archivo de solo lectura para upload_fileobj.
    Cuenta bytes, comprime si hace falta y, al llegar al final, ESPERA a pg_dump y mira su código:
    si falló, lanza una excepción y boto3 aborta la subida por partes."""

    def __init__(self, proc, gzip, corto=False):
        self.corto = corto
        self.proc, self.leidos, self.subidos = proc, 0, 0
        self.z = zlib.compressobj(6, zlib.DEFLATED, 31) if gzip else None
        self.fin = False
        self.pendiente = b""

    def read(self, n=-1):
        # ⚠️ boto3 (s3transfer) trata esto como un ARCHIVO: si read(n) devuelve menos de n bytes, da el
        # archivo por terminado. Con 8 MB de umbral, una primera lectura corta = un solo put_object con
        # lo que haya, y «ok». Hay que devolver SIEMPRE n bytes, salvo al final de verdad.
        n = n if n and n > 0 else PARTE
        if self.corto:  # EL ERROR (modo z0+gzip-corto): devuelve lo que zlib suelte, aunque sea menos de n
            salida = b""
            while not salida and not self.fin:
                salida = self._leer(PARTE)
            return salida
        while len(self.pendiente) < n and not self.fin:
            self.pendiente += self._leer(PARTE)
        salida, self.pendiente = self.pendiente[:n], self.pendiente[n:]
        return salida

    def _leer(self, n):
        trozo = self.proc.stdout.read(n if n and n > 0 else PARTE)
        self.leidos += len(trozo)
        if not trozo:
            self.fin = True
            codigo = self.proc.wait()
            if codigo != 0:
                err = self.proc.stderr.read().decode(errors="replace").strip()
                raise RuntimeError(f"pg_dump salió con código {codigo}: {err}")
            salida = self.z.flush() if self.z else b""
        else:
            salida = self.z.compress(trozo) if self.z else trozo
        self.subidos += len(salida)
        return salida


def pg_dump(base, modo):
    args = ["pg_dump", "-Fc", "-d", base]
    if modo.startswith("z0"):
        args.insert(2, "-Z0")
    return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def respaldar(a):
    k = clave(a.base, a.fecha, a.modo)
    proc = pg_dump(a.base, a.modo)
    tubo = Tubo(proc, "gzip" in a.modo, corto=a.modo.endswith("-corto"))
    try:
        s3.upload_fileobj(tubo, BUCKET, k, Config=CONFIG)
    except Exception as e:  # noqa: BLE001
        proc.kill()
        print(f"ERROR: subida abortada: {e}")
        return 1
    partes = -(-tubo.subidos // PARTE)
    print(f"ok  {k}")
    print(f"    pg_dump {mb(tubo.leidos)} · subido {mb(tubo.subidos)} · partes {partes} · memoria pico {pico()}")
    return 0


def sin_wait(a):
    # EL ERROR: se sube lo que salga por la tubería y nadie pregunta cómo terminó pg_dump
    k = clave(a.base, a.fecha, "fc")
    proc = pg_dump(a.base, "fc")
    s3.upload_fileobj(proc.stdout, BUCKET, k, Config=CONFIG)
    print(f"ok  {k}  (el script terminó con código 0)")
    return 0


def ingenuo(a):
    k = clave(a.base, a.fecha, "fc")
    datos = subprocess.run(["pg_dump", "-Fc", "-d", a.base], capture_output=True, check=True).stdout
    s3.put_object(Bucket=BUCKET, Key=k, Body=datos)
    print(f"ok  {k}")
    print(f"    pg_dump {mb(len(datos))} · subido de una vez · memoria pico {pico()}")
    return 0


def objetos(base):
    res = []
    for pag in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=f"respaldos/{base}/" if base else "respaldos/"):
        for o in pag.get("Contents", []):
            nombre = o["Key"].rsplit("/", 1)[1].split(".")[0]
            res.append((o["Key"], datetime.strptime(nombre, "%Y-%m-%dT%H%M"), o["Size"]))
    return sorted(res, key=lambda x: x[1], reverse=True)


def listar(a):
    lista = objetos(a.base)
    for k, _, t in lista:
        tam = f"{t / 1e3:.0f} KB" if t < 1e6 else mb(t)
        print(f"    {k:<45}{tam:>10}")
    print(f"    {len(lista)} respaldos")
    a_medias = s3.list_multipart_uploads(Bucket=BUCKET).get("Uploads", [])
    print(f"    subidas por partes a medias: {len(a_medias)}")
    return 0


def retener(a):
    lista = objetos(a.base)
    if not lista:
        print("no hay respaldos")
        return 1
    motivo = {k: f"entre los {a.ultimos} más nuevos" for k, _, _ in lista[: a.ultimos]}
    # los días se cuentan desde el respaldo MÁS NUEVO, no desde el reloj: si el job lleva días
    # caído, contar desde «hoy» borraría justo los últimos respaldos buenos.
    limite = lista[0][1].replace(hour=0, minute=0) - timedelta(days=a.dias - 1)
    vistos = set()
    for k, f, _ in lista:
        dia = f.strftime("%Y-%m-%d")
        if f < limite or dia in vistos:
            continue
        vistos.add(dia)
        motivo.setdefault(k, f"el último del {dia}")
    fuera = []
    for k, _, _ in lista:
        corto = k.removeprefix("respaldos/")
        if k in motivo:
            print(f"    queda   {corto:<36} ({motivo[k]})")
        else:
            print(f"    BORRA   {corto}")
            fuera.append({"Key": k})
    print(f"    quedan {len(lista) - len(fuera)} · se borran {len(fuera)}")
    if not a.borrar:
        print("    (ensayo: no se borró nada; usa --borrar)")
        return 0
    if fuera:
        r = s3.delete_objects(Bucket=BUCKET, Delete={"Objects": fuera})
        print(f"    borrados {len(r.get('Deleted', []))} · errores {len(r.get('Errors', []))}")
    return 0


def restaurar(a):
    destino = os.environ["PGHOST_DESTINO"]
    base = "tienda_restaurada"
    env = dict(os.environ, PGHOST=destino, PGOPTIONS="-c client_min_messages=warning")
    subprocess.run(["dropdb", "--if-exists", base], env=env, check=True)
    subprocess.run(["createdb", base], env=env, check=True)
    cuerpo = s3.get_object(Bucket=BUCKET, Key=a.clave)["Body"]
    z = zlib.decompressobj(31) if a.clave.endswith(".gz") else None
    proc = subprocess.Popen(["pg_restore", "--single-transaction", "--no-owner", "-d", base],
                            stdin=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    try:
        for trozo in cuerpo.iter_chunks(PARTE):
            proc.stdin.write(z.decompress(trozo) if z else trozo)
        if z:
            proc.stdin.write(z.flush())
    except BrokenPipeError:
        pass
    proc.stdin.close()
    err = proc.stderr.read().decode(errors="replace").strip()
    if proc.wait() != 0:
        print(f"ERROR: pg_restore salió con código {proc.returncode}: {err}")
        return 1
    print(f"ok  restaurado {a.clave} en {destino}/{base} · memoria pico {pico()}")
    return 0


SQL = {"clientes": "SELECT count(*) || ' · ' || sum(id) FROM clientes",
       "pedidos": "SELECT count(*) || ' · ' || sum(monto) FROM pedidos"}


def psql(host, base, sql):
    env = dict(os.environ, PGHOST=host)
    return subprocess.run(["psql", "-qAt", "-d", base, "-c", sql], env=env, capture_output=True, text=True,
                          check=True).stdout.strip()


def verificar(a):
    origen, destino = os.environ["PGHOST"], os.environ["PGHOST_DESTINO"]
    print(f"    {'tabla':<10}{'origen (filas · suma)':<32}{'restaurada':<32}")
    iguales = True
    for t, sql in SQL.items():
        o, d = psql(origen, "tienda", sql), psql(destino, "tienda_restaurada", sql)
        iguales &= o == d
        print(f"    {t:<10}{o:<32}{d:<32}{'igual' if o == d else 'DISTINTO'}")
    print("ok  el respaldo restaura y coincide" if iguales else "ERROR: la restaurada no coincide")
    return 0 if iguales else 1


def bucket(a):
    s3.create_bucket(Bucket=BUCKET)
    print(f"ok  bucket {BUCKET}")
    return 0


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="orden", required=True)
    sub.add_parser("bucket")
    for n in ("respaldar", "sin-wait", "ingenuo"):
        s = sub.add_parser(n)
        s.add_argument("--base", default="tienda")
        s.add_argument("--fecha", required=True)
        s.add_argument("--modo", default="fc", choices=["fc", "z0+gzip", "z0+gzip-corto"])
    s = sub.add_parser("listar")
    s.add_argument("--base", default="tienda")
    s = sub.add_parser("retener")
    s.add_argument("--base", required=True)
    s.add_argument("--ultimos", type=int, default=3)
    s.add_argument("--dias", type=int, default=7)
    s.add_argument("--borrar", action="store_true")
    s = sub.add_parser("restaurar")
    s.add_argument("--clave", required=True)
    sub.add_parser("verificar")
    a = p.parse_args()
    f = {"bucket": bucket, "respaldar": respaldar, "sin-wait": sin_wait, "ingenuo": ingenuo, "listar": listar,
         "retener": retener, "restaurar": restaurar, "verificar": verificar}[a.orden]
    sys.exit(f(a))


if __name__ == "__main__":
    main()
