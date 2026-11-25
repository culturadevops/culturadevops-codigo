# -*- coding: utf-8 -*-
"""app.py — la tienda del vídeo 396. Una sola aplicación; dónde guarda cada cosa lo dicen las variables:

    BD=sqlite|postgres      sqlite: un fichero dentro del contenedor · postgres: el servidor «pg»
    FICHEROS=local|s3       local: /datos/ficheros dentro del contenedor · s3: MinIO («minio», bucket «subidas»)
    CACHE=0|1               1: Valkey («cache») delante de la consulta de ventas
    REPLICA=nombre          va en la cabecera X-Replica de cada respuesta

    POST /pedido               crea un pedido
    GET  /pedidos              cuántos pedidos hay
    POST /subir/<nombre>       guarda un fichero
    GET  /archivo/<nombre>     lo devuelve (404 si no está aquí)
    GET  /ventas/<producto>    total vendido de un producto (consulta pesada, sin índice)
    GET  /salud
"""
import os
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BD, FICHEROS = os.environ.get("BD", "sqlite"), os.environ.get("FICHEROS", "local")
CACHE, REPLICA = os.environ.get("CACHE") == "1", os.environ.get("REPLICA", "app")
DIR = "/datos/ficheros"
os.makedirs(DIR, exist_ok=True)
_local = threading.local()


def bd():
    if not hasattr(_local, "c"):
        if BD == "postgres":
            import psycopg
            _local.c = psycopg.connect("host=pg user=postgres password=lab dbname=postgres", autocommit=True)
        else:
            _local.c = sqlite3.connect("/datos/tienda.db", isolation_level=None, check_same_thread=False)
            _local.c.execute("CREATE TABLE IF NOT EXISTS pedidos (id INTEGER PRIMARY KEY, creado TEXT)")
    return _local.c


def s3():
    if not hasattr(_local, "s3"):
        import boto3
        _local.s3 = boto3.client("s3", endpoint_url="http://minio:9000", aws_access_key_id="lab",
                                 aws_secret_access_key="lab12345", region_name="us-east-1")
    return _local.s3


def cache():
    if not hasattr(_local, "r"):
        import redis
        _local.r = redis.Redis(host="cache")
    return _local.r


def ventas(producto):
    if CACHE:
        v = cache().get(f"ventas:{producto}")
        if v is not None:
            return v.decode()
    cur = bd().execute("SELECT count(*), coalesce(sum(total), 0) FROM ventas WHERE producto_id = %s", (producto,))
    n, total = cur.fetchone()
    res = f"{n} ventas, {total}"
    if CACHE:
        cache().set(f"ventas:{producto}", res, ex=60)
    return res


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def responder(self, codigo, texto):
        b = (texto + "\n").encode()
        self.send_response(codigo)
        self.send_header("X-Replica", REPLICA)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_POST(self):
        cuerpo = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        if self.path == "/pedido":
            ph = "%s" if BD == "postgres" else "?"
            bd().execute(f"INSERT INTO pedidos (creado) VALUES ({ph})", ("ahora",))
            return self.responder(201, "pedido creado")
        if self.path.startswith("/subir/"):
            nombre = self.path.split("/", 2)[2]
            if FICHEROS == "s3":
                s3().put_object(Bucket="subidas", Key=nombre, Body=cuerpo)
            else:
                with open(os.path.join(DIR, nombre), "wb") as f:
                    f.write(cuerpo)
            return self.responder(201, f"guardado en {REPLICA}")
        self.responder(404, "no existe")

    def do_GET(self):
        if self.path == "/salud":
            return self.responder(200, "ok")
        if self.path == "/pedidos":
            return self.responder(200, str(bd().execute("SELECT count(*) FROM pedidos").fetchone()[0]))
        if self.path.startswith("/archivo/"):
            nombre = self.path.split("/", 2)[2]
            try:
                if FICHEROS == "s3":
                    datos = s3().get_object(Bucket="subidas", Key=nombre)["Body"].read()
                else:
                    datos = open(os.path.join(DIR, nombre), "rb").read()
                return self.responder(200, f"{len(datos)} bytes")
            except Exception:  # noqa: BLE001
                return self.responder(404, f"no está en {REPLICA}")
        if self.path.startswith("/ventas/"):
            return self.responder(200, ventas(int(self.path.rsplit("/", 1)[1])))
        self.responder(404, "no existe")


if __name__ == "__main__":
    ThreadingHTTPServer.request_queue_size = 128
    ThreadingHTTPServer(("", 8000), H).serve_forever()
