# -*- coding: utf-8 -*-
"""s3_py.py — un S3 escrito en Python, para el video 215 de cultura-devops.

LA PROMESA DEL VIDEO: que **boto3 oficial** —el mismo que usas en produccion— hable con esto sin
notar nada. Sin parches, sin `moto`, sin "modo local". Lo unico que cambia es `endpoint_url`.

QUE SE APRENDE ESCRIBIENDOLO, que es el angulo del video:
  1. S3 es HTTP y poco mas: PUT sube, GET baja, DELETE borra.
  2. **LAS CARPETAS NO EXISTEN.** Las claves son cadenas planas; lo que parece un arbol lo dibuja
     el LISTADO con `prefix` y `delimiter`. Por eso "renombrar una carpeta" no es una operacion:
     hay que copiar y borrar objeto a objeto.
  3. El ETag: boto3 lo lee, y si se lo devuelves mal se entera.
  4. La firma: boto3 la manda SIEMPRE, aunque el servidor no la mire.

LO QUE NO HACE, y en el video se dice claro: no hay durabilidad, ni versiones, ni subida
multiparte, ni permisos, ni cifrado. Eso es lo que hace que S3 sea S3.

Sin dependencias: solo la biblioteca estandar.

    python s3_py.py --puerto 9000
"""
import argparse
import hashlib
import threading
import xml.sax.saxutils as sx
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

# bucket -> {clave: (datos, etag, fecha)}
#
# ⚠️ MIRALO BIEN: es un diccionario PLANO. No hay arbol, no hay carpetas, no hay nodos. Todo lo
# que parece una jerarquia en la consola de AWS sale del listado, no del almacen.
CUBOS = {}
CANDADO = threading.Lock()


def ahora():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def xml_error(codigo, mensaje):
    return (f'<?xml version="1.0" encoding="UTF-8"?><Error><Code>{codigo}</Code>'
            f"<Message>{sx.escape(mensaje)}</Message></Error>").encode()


class S3(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass                                  # sin ruido: el video ensena la salida de boto3

    # ── utilidades ──────────────────────────────────────────────────────
    def _partes(self):
        """Direccionamiento por RUTA: /cubo/clave. boto3 lo usa con `addressing_style='path'`."""
        u = urlparse(self.path)
        p = unquote(u.path).lstrip("/")
        cubo, _, clave = p.partition("/")
        return cubo, clave, parse_qs(u.query)

    def _responde(self, codigo, cuerpo=b"", cabeceras=None, largo=None):
        """`largo` existe por HEAD.

        ⚠️ Un HEAD no manda cuerpo, pero tiene que declarar el tamano del cuerpo que MANDARIA. Si
        pones `Content-Length: 0` el servidor responde y nadie se queja... salvo el cliente, que
        te cree: `head_object` de boto3 devolvia `ContentLength 0` para un objeto de 10 bytes.
        Encontrado el 2026-09-07 con boto3 1.43.89.
        """
        self.send_response(codigo)
        for k, v in (cabeceras or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(cuerpo) if largo is None else largo))
        self.end_headers()
        if cuerpo:
            self.wfile.write(cuerpo)

    def _error(self, codigo_http, codigo, mensaje):
        self._responde(codigo_http, xml_error(codigo, mensaje),
                       {"Content-Type": "application/xml"})

    # ── GET ─────────────────────────────────────────────────────────────
    def do_GET(self):
        cubo, clave, q = self._partes()

        if not cubo:                                   # ListBuckets
            with CANDADO:
                filas = "".join(
                    f"<Bucket><Name>{sx.escape(b)}</Name>"
                    f"<CreationDate>{ahora()}</CreationDate></Bucket>" for b in CUBOS)
            cuerpo = ('<?xml version="1.0" encoding="UTF-8"?>'
                      '<ListAllMyBucketsResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">'
                      "<Owner><ID>quien</ID><DisplayName>quien</DisplayName></Owner>"
                      f"<Buckets>{filas}</Buckets></ListAllMyBucketsResult>").encode()
            return self._responde(200, cuerpo, {"Content-Type": "application/xml"})

        if not clave:                                  # ListObjectsV2
            return self._listar(cubo, q)

        with CANDADO:
            obj = CUBOS.get(cubo, {}).get(clave)
        if obj is None:
            return self._error(404, "NoSuchKey", "The specified key does not exist.")
        datos, etag, fecha = obj
        return self._responde(200, datos, {"Content-Type": "application/octet-stream",
                                           "ETag": f'"{etag}"', "Last-Modified": fecha})

    def _listar(self, cubo, q):
        """EL CORAZON DEL VIDEO: aqui es donde se INVENTAN las carpetas.

        `prefix` filtra por el principio de la clave. `delimiter` (normalmente "/") corta: todo lo
        que tenga mas separadores despues del prefijo se agrupa en un CommonPrefix, que es lo que
        la consola de AWS te pinta como una carpeta. No hay ninguna carpeta guardada en ningun
        sitio: se calcula en cada listado.
        """
        with CANDADO:
            if cubo not in CUBOS:
                return self._error(404, "NoSuchBucket", "The specified bucket does not exist.")
            claves = sorted(CUBOS[cubo])
            objetos = dict(CUBOS[cubo])
        pref = (q.get("prefix") or [""])[0]
        deli = (q.get("delimiter") or [""])[0]

        contents, prefijos = [], set()
        for k in claves:
            if not k.startswith(pref):
                continue
            if deli:
                resto = k[len(pref):]
                i = resto.find(deli)
                if i >= 0:
                    prefijos.add(pref + resto[: i + len(deli)])   # <- la "carpeta", inventada aqui
                    continue
            datos, etag, fecha = objetos[k]
            contents.append(f"<Contents><Key>{sx.escape(k)}</Key><LastModified>{fecha}</LastModified>"
                            f'<ETag>&quot;{etag}&quot;</ETag><Size>{len(datos)}</Size>'
                            f"<StorageClass>STANDARD</StorageClass></Contents>")
        cp = "".join(f"<CommonPrefixes><Prefix>{sx.escape(p)}</Prefix></CommonPrefixes>"
                     for p in sorted(prefijos))
        cuerpo = ('<?xml version="1.0" encoding="UTF-8"?>'
                  '<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">'
                  f"<Name>{sx.escape(cubo)}</Name><Prefix>{sx.escape(pref)}</Prefix>"
                  f"<Delimiter>{sx.escape(deli)}</Delimiter><KeyCount>{len(contents)+len(prefijos)}</KeyCount>"
                  f"<MaxKeys>1000</MaxKeys><IsTruncated>false</IsTruncated>"
                  f"{''.join(contents)}{cp}</ListBucketResult>").encode()
        return self._responde(200, cuerpo, {"Content-Type": "application/xml"})

    # ── HEAD ────────────────────────────────────────────────────────────
    def do_HEAD(self):
        cubo, clave, _ = self._partes()
        with CANDADO:
            if not clave:
                return self._responde(200 if cubo in CUBOS else 404)
            obj = CUBOS.get(cubo, {}).get(clave)
        if obj is None:
            return self._responde(404)
        datos, etag, fecha = obj
        return self._responde(200, b"", {"ETag": f'"{etag}"', "Last-Modified": fecha,
                                         "Content-Type": "application/octet-stream"},
                              largo=len(datos))

    # ── PUT ─────────────────────────────────────────────────────────────
    def do_PUT(self):
        cubo, clave, _ = self._partes()
        n = int(self.headers.get("Content-Length") or 0)
        datos = self.rfile.read(n) if n else b""
        with CANDADO:
            if not clave:                              # CreateBucket
                CUBOS.setdefault(cubo, {})
                return self._responde(200, b"", {"Location": f"/{cubo}"})
            if cubo not in CUBOS:
                return self._error(404, "NoSuchBucket", "The specified bucket does not exist.")
            # El ETag de un objeto simple es el MD5 del contenido. boto3 lo lee y lo compara.
            etag = hashlib.md5(datos).hexdigest()
            CUBOS[cubo][clave] = (datos, etag, ahora())
        return self._responde(200, b"", {"ETag": f'"{etag}"'})

    # ── DELETE ──────────────────────────────────────────────────────────
    def do_DELETE(self):
        cubo, clave, _ = self._partes()
        with CANDADO:
            if not clave:
                CUBOS.pop(cubo, None)
            else:
                CUBOS.get(cubo, {}).pop(clave, None)
        return self._responde(204)

    # ── POST ────────────────────────────────────────────────────────────
    def do_POST(self):
        # DeleteObjects va por POST con ?delete. No hace falta para el video: se responde 501
        # a proposito y en el guion se dice que no esta hecho.
        return self._error(501, "NotImplemented", "Solo PUT/GET/DELETE/List en este juguete.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=9000)
    ap.add_argument("--bind", default="127.0.0.1")
    a = ap.parse_args()
    s = ThreadingHTTPServer((a.bind, a.puerto), S3)
    print(f"escuchando en {a.bind}:{a.puerto}", flush=True)
    s.serve_forever()


if __name__ == "__main__":
    main()
