# -*- coding: utf-8 -*-
"""dynamo_py.py — un DynamoDB escrito en Python, para el video 216 de cultura-devops.

LA PROMESA DEL VIDEO: que **boto3 oficial** haga CreateTable, PutItem, GetItem, Query y Scan
contra esto sin notar nada. Lo unico que cambia es `endpoint_url`.

QUE SE APRENDE ESCRIBIENDOLO, que es el angulo del video:

  1. **EL PROTOCOLO ES JSON SOBRE HTTP**, y la operacion NO va en la ruta: va en una cabecera,
     `X-Amz-Target: DynamoDB_20120810.PutItem`. Todo llega a `POST /`.

  2. **LOS NUMEROS VIAJAN COMO CADENA**: `{"N": "19.99"}`. Por eso boto3 se niega a mandar un
     float de Python y te obliga a usar Decimal — no es una manía de la biblioteca, es que el
     protocolo transporta texto y un float ya viene con el error de coma flotante metido.

  3. **QUERY Y SCAN NO SON LA MISMA OPERACION OPTIMIZADA.** Al implementarlas se ve: Query usa la
     clave de particion para ir DIRECTO a su grupo; Scan no tiene por donde agarrar y recorre
     todo. Con tres filas parecen iguales; con el codigo delante, no lo son.

LO QUE NO HACE: indices secundarios, transacciones, capacidad, replicas, paginacion real.

Sin dependencias: solo la biblioteca estandar.

    python dynamo_py.py --puerto 8000
"""
import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# tabla -> {"pk": nombre, "sk": nombre|None, "items": {valor_pk: {valor_sk: item}}}
#
# ⚠️ MIRALO BIEN: los items NO son una lista. Estan agrupados POR CLAVE DE PARTICION. Esa
# estructura es la respuesta a por que Query es rapido y Scan no: la eleccion de la clave decide
# el rendimiento antes de que escribas una sola consulta.
TABLAS = {}
CANDADO = threading.Lock()

# Contadores para ensenar en pantalla cuantos items TOCA cada operacion.
TOCADOS = {"Query": 0, "Scan": 0}


def esquema(defs, keys):
    tipos = {d["AttributeName"]: d["AttributeType"] for d in defs}
    pk = next(k["AttributeName"] for k in keys if k["KeyType"] == "HASH")
    sk = next((k["AttributeName"] for k in keys if k["KeyType"] == "RANGE"), None)
    return pk, sk, tipos


def val(v):
    """Saca el valor de un atributo con nombre de tipo: {"S": "x"} -> "x"."""
    (t, x), = v.items()
    return x


class Dynamo(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _ok(self, obj):
        cuerpo = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/x-amz-json-1.0")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def _err(self, codigo_http, tipo, mensaje):
        cuerpo = json.dumps({"__type": f"com.amazonaws.dynamodb.v20120810#{tipo}",
                             "message": mensaje}).encode()
        self.send_response(codigo_http)
        self.send_header("Content-Type", "application/x-amz-json-1.0")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        cuerpo = json.loads(self.rfile.read(n) or b"{}")
        # LA OPERACION VA EN UNA CABECERA, no en la ruta. Esto es lo primero que sorprende.
        objetivo = (self.headers.get("X-Amz-Target") or "").split(".")[-1]
        try:
            return getattr(self, f"op_{objetivo}")(cuerpo)
        except AttributeError:
            return self._err(400, "UnknownOperationException", f"no implemento {objetivo}")

    # ── operaciones ─────────────────────────────────────────────────────
    def op_CreateTable(self, c):
        pk, sk, _ = esquema(c["AttributeDefinitions"], c["KeySchema"])
        with CANDADO:
            TABLAS[c["TableName"]] = {"pk": pk, "sk": sk, "items": {}}
        return self._ok({"TableDescription": {"TableName": c["TableName"],
                                              "TableStatus": "ACTIVE"}})

    def op_DescribeTable(self, c):
        with CANDADO:
            t = TABLAS.get(c["TableName"])
        if not t:
            return self._err(400, "ResourceNotFoundException", "no existe esa tabla")
        return self._ok({"Table": {"TableName": c["TableName"], "TableStatus": "ACTIVE",
                                   "ItemCount": sum(len(g) for g in t["items"].values())}})

    def op_PutItem(self, c):
        with CANDADO:
            t = TABLAS.get(c["TableName"])
            if not t:
                return self._err(400, "ResourceNotFoundException", "no existe esa tabla")
            it = c["Item"]
            kp = val(it[t["pk"]])
            ks = val(it[t["sk"]]) if t["sk"] else ""
            t["items"].setdefault(kp, {})[ks] = it
        return self._ok({})

    def op_GetItem(self, c):
        with CANDADO:
            t = TABLAS.get(c["TableName"])
            if not t:
                return self._err(400, "ResourceNotFoundException", "no existe esa tabla")
            kp = val(c["Key"][t["pk"]])
            ks = val(c["Key"][t["sk"]]) if t["sk"] else ""
            it = t["items"].get(kp, {}).get(ks)
        return self._ok({"Item": it} if it else {})

    def op_Query(self, c):
        """Va DIRECTO al grupo de la clave de particion. Solo toca ese grupo."""
        with CANDADO:
            t = TABLAS.get(c["TableName"])
            if not t:
                return self._err(400, "ResourceNotFoundException", "no existe esa tabla")
            # Se acepta la forma simple `pk = :v`, que es la que manda boto3 en el video.
            valores = c.get("ExpressionAttributeValues", {})
            kp = val(next(iter(valores.values())))
            grupo = t["items"].get(kp, {})
            TOCADOS["Query"] = len(grupo)                 # <- SOLO su grupo
            items = [grupo[k] for k in sorted(grupo)]
        return self._ok({"Items": items, "Count": len(items), "ScannedCount": len(items)})

    def op_Scan(self, c):
        """No tiene por donde agarrar: recorre TODO."""
        with CANDADO:
            t = TABLAS.get(c["TableName"])
            if not t:
                return self._err(400, "ResourceNotFoundException", "no existe esa tabla")
            todos = [it for g in t["items"].values() for it in g.values()]
            TOCADOS["Scan"] = len(todos)                  # <- la tabla ENTERA
            items = todos
            # Filtro despues de leerlo todo, que es exactamente lo que hace DynamoDB: el
            # FilterExpression NO ahorra lectura, solo reduce lo que te devuelve.
            #
            # ⚠️ boto3 NO manda `cliente = :v0`. Manda `#n0 = :v0` y aparte un diccionario
            # `ExpressionAttributeNames` con `{"#n0": "cliente"}`. Lo hace para que los nombres
            # de campo no choquen con las ~570 palabras reservadas de DynamoDB. Si no resuelves
            # el alias, el filtro no encuentra nada y el Scan devuelve 0 sin dar ningun error.
            expr = c.get("FilterExpression")
            valores = c.get("ExpressionAttributeValues") or {}
            nombres = c.get("ExpressionAttributeNames") or {}
            if expr and valores:
                campo = expr.split("=")[0].strip()
                campo = nombres.get(campo, campo)         # <- resolver el alias
                buscado = val(next(iter(valores.values())))
                items = [it for it in todos if campo in it and val(it[campo]) == buscado]
        return self._ok({"Items": items, "Count": len(items), "ScannedCount": len(todos)})

    def op_Tocados(self, c):
        """No es de DynamoDB: es para que el video pueda ensenar cuantos items toco cada una."""
        return self._ok(dict(TOCADOS))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--puerto", type=int, default=8000)
    ap.add_argument("--bind", default="127.0.0.1")
    a = ap.parse_args()
    s = ThreadingHTTPServer((a.bind, a.puerto), Dynamo)
    print(f"escuchando en {a.bind}:{a.puerto}", flush=True)
    s.serve_forever()


if __name__ == "__main__":
    main()
