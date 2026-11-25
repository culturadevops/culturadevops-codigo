# -*- coding: utf-8 -*-
"""lab.py — las mediciones del vídeo «SQL o NoSQL» (cultura-devops, 352). Corre DENTRO de la red de Docker
(imagen sd-sql-cliente:1 = python 3.13 + psycopg 3.2.3 + pymongo 4.10.1), contra «pg» y «mongo».

La misma tienda en las dos: 20.000 clientes, 1.000 productos (20 categorías), 100.000 pedidos de 1 a 5 líneas.
  · Postgres: normalizada (clientes, productos, pedidos, lineas).
  · MongoDB: un documento por pedido, con el cliente y las líneas dentro (nombre, categoría y precio copiados).

    python lab.py cargar | leer | esquema | cruzar | renombrar | transaccion | jsonb
"""
import random
import statistics
import sys
import time
from datetime import datetime, timedelta, timezone

import psycopg
from pymongo import MongoClient

PG = "host=pg user=postgres password=lab dbname=postgres"
rnd = random.Random(42)
CLIENTES, PRODUCTOS, PEDIDOS = 20_000, 1_000, 100_000


def mongo(rs=False):
    return MongoClient("mongodb://mongo:27017/?directConnection=true" + ("&replicaSet=rs0" if rs else ""))


def mediana(f, n=1000):
    for i in range(50):
        f(i)
    ts = []
    for i in range(n):
        t0 = time.perf_counter()
        f(i)
        ts.append((time.perf_counter() - t0) * 1000)
    return statistics.median(ts)


def cronometro(f):
    t0 = time.perf_counter()
    r = f()
    return r, time.perf_counter() - t0


def datos():
    base = datetime(2026, 10, 1, tzinfo=timezone.utc)
    productos = [(i, f"Producto {i}", f"cat{i % 20:02d}", round(rnd.uniform(5, 500), 2)) for i in range(1, PRODUCTOS + 1)]
    clientes = [(i, f"Cliente {i}", f"c{i}@correo.test") for i in range(1, CLIENTES + 1)]
    pedidos, lineas = [], []
    for p in range(1, PEDIDOS + 1):
        pedidos.append((p, rnd.randint(1, CLIENTES), base - timedelta(days=rnd.uniform(0, 365))))
        for _ in range(rnd.randint(1, 5)):
            lineas.append((p, rnd.randint(1, PRODUCTOS), rnd.randint(1, 4)))
    return productos, clientes, pedidos, lineas


def cargar():
    productos, clientes, pedidos, lineas = datos()
    with psycopg.connect(PG, autocommit=True) as c:
        c.execute("""DROP TABLE IF EXISTS lineas, pedidos, productos, clientes;
            CREATE TABLE clientes (id int PRIMARY KEY, nombre text NOT NULL, email text NOT NULL);
            CREATE TABLE productos (id int PRIMARY KEY, nombre text NOT NULL, categoria text NOT NULL,
                                    precio numeric(10,2) NOT NULL, stock int NOT NULL DEFAULT 1000);
            CREATE TABLE pedidos (id int PRIMARY KEY, cliente_id int NOT NULL REFERENCES clientes,
                                  creado timestamptz NOT NULL, pagado bool NOT NULL DEFAULT false);
            CREATE TABLE lineas (pedido_id int NOT NULL REFERENCES pedidos, producto_id int NOT NULL REFERENCES productos,
                                 cantidad int NOT NULL);
            CREATE INDEX ON lineas (pedido_id); CREATE INDEX ON pedidos (creado);""")
        t0 = time.perf_counter()
        with c.cursor() as cur:
            with cur.copy("COPY productos (id, nombre, categoria, precio) FROM STDIN") as cp:
                for r in productos:
                    cp.write_row(r)
            with cur.copy("COPY clientes FROM STDIN") as cp:
                for r in clientes:
                    cp.write_row(r)
            with cur.copy("COPY pedidos (id, cliente_id, creado) FROM STDIN") as cp:
                for r in pedidos:
                    cp.write_row(r)
            with cur.copy("COPY lineas FROM STDIN") as cp:
                for r in lineas:
                    cp.write_row(r)
        c.execute("VACUUM ANALYZE")
        tpg = time.perf_counter() - t0
    prod = {p[0]: p for p in productos}
    cli = {c[0]: c for c in clientes}
    por_pedido = {}
    for p, pr, q in lineas:
        por_pedido.setdefault(p, []).append((pr, q))
    docs = [{"_id": p, "creado": creado, "pagado": False,
             "cliente": {"id": cid, "nombre": cli[cid][1], "email": cli[cid][2]},
             "lineas": [{"producto_id": pr, "nombre": prod[pr][1], "categoria": prod[pr][2],
                         "precio": prod[pr][3], "cantidad": q} for pr, q in por_pedido[p]]}
            for p, cid, creado in pedidos]
    m = mongo().tienda
    m.pedidos.drop()
    m.productos.drop()
    t0 = time.perf_counter()
    m.productos.insert_many([{"_id": p[0], "nombre": p[1], "categoria": p[2], "precio": p[3], "stock": 1000}
                             for p in productos])
    m.pedidos.insert_many(docs, ordered=False)
    m.pedidos.create_index("creado")
    tmo = time.perf_counter() - t0
    print(f"  {PEDIDOS:,} pedidos · {len(lineas):,} líneas · {CLIENTES:,} clientes · {PRODUCTOS:,} productos".replace(",", "."))
    print(f"  carga: Postgres {tpg:.1f} s (COPY) · MongoDB {tmo:.1f} s (insert_many)")
    with psycopg.connect(PG) as c:
        tam = c.execute("SELECT pg_size_pretty(sum(pg_total_relation_size(c.oid))) FROM pg_class c "
                        "WHERE relname IN ('clientes','productos','pedidos','lineas')").fetchone()[0]
    mongo().admin.command("fsync")          # que WiredTiger escriba el checkpoint: si no, storageSize sale 0
    st = mongo().tienda.command("collStats", "pedidos")
    print(f"  tamaño: Postgres {tam} (4 tablas e índices) · MongoDB pedidos {st['storageSize'] / 2**20:.0f} MB "
          f"comprimidos + índices {st['totalIndexSize'] / 2**20:.0f} MB")


def leer():
    with psycopg.connect(PG) as c:
        q = ("SELECT p.id, p.creado, c.nombre, c.email, pr.nombre, pr.categoria, pr.precio, l.cantidad "
             "FROM pedidos p JOIN clientes c ON c.id = p.cliente_id JOIN lineas l ON l.pedido_id = p.id "
             "JOIN productos pr ON pr.id = l.producto_id WHERE p.id = %s")
        print("  Postgres, el pedido 4242 (JOIN de 4 tablas):")
        for r in c.execute(q, (4242,)).fetchall():
            print(f"    {r[0]} · {r[2]} · {r[4]} · {r[5]} · {r[6]} × {r[7]}")
        t = mediana(lambda i: c.execute(q, (rnd.randint(1, PEDIDOS),)).fetchall())
        print(f"  Postgres: leer un pedido entero, mediana de 1.000: {t:.3f} ms")
    m = mongo().tienda.pedidos
    d = m.find_one({"_id": 4242})
    print(f"  MongoDB, el pedido 4242 (un documento): cliente={d['cliente']['nombre']} · "
          f"{len(d['lineas'])} líneas dentro · primera: {d['lineas'][0]['nombre']} {d['lineas'][0]['precio']}")
    t = mediana(lambda i: m.find_one({"_id": rnd.randint(1, PEDIDOS)}))
    print(f"  MongoDB: leer un pedido entero, mediana de 1.000: {t:.3f} ms")


def esquema():
    with psycopg.connect(PG, autocommit=True) as c:
        _, t = cronometro(lambda: c.execute("ALTER TABLE pedidos ADD COLUMN moneda text NOT NULL DEFAULT 'MXN'"))
        print(f"  Postgres: ALTER TABLE pedidos ADD COLUMN moneda text NOT NULL DEFAULT 'MXN' → {t * 1000:.1f} ms")
        n = c.execute("SELECT count(*) FROM pedidos WHERE moneda = 'MXN'").fetchone()[0]
        print(f"  Postgres: pedidos con moneda = 'MXN': {n:,} de {PEDIDOS:,}".replace(",", "."))
        try:
            c.execute("INSERT INTO pedidos (id, cliente_id, creado, moneda) VALUES (999999, 1, now(), NULL)")
        except psycopg.Error as e:
            print(f"  Postgres: insertar un pedido sin moneda → {type(e).__name__}: {str(e).splitlines()[0]}")
    m = mongo().tienda.pedidos
    m.insert_one({"_id": 100001, "creado": datetime.now(timezone.utc), "pagado": False, "moneda": "MXN",
                  "cliente": {"id": 1}, "lineas": []})
    print("  MongoDB: no hay ALTER; el código nuevo empieza a escribir «moneda» en los pedidos nuevos")
    n = m.count_documents({"moneda": "MXN"})
    print(f"  MongoDB: pedidos con moneda = 'MXN': {n} de {m.count_documents({}):,}".replace(",", "."))
    m.insert_one({"_id": 100002, "creado": datetime.now(timezone.utc), "pagado": False, "cliente": {"id": 1}, "lineas": []})
    print("  MongoDB: insertar un pedido sin moneda → aceptado (sin esquema, nadie lo impide)")
    r, t = cronometro(lambda: m.update_many({"moneda": {"$exists": False}}, {"$set": {"moneda": "MXN"}}))
    print(f"  MongoDB: rellenar los viejos con update_many → {r.modified_count:,} documentos en {t:.1f} s".replace(",", "."))
    m.delete_many({"_id": {"$gt": PEDIDOS}})


def cruzar():
    desde = datetime(2026, 9, 1, tzinfo=timezone.utc)
    sql = ("SELECT pr.categoria, sum(pr.precio * l.cantidad) AS ventas FROM pedidos p "
           "JOIN lineas l ON l.pedido_id = p.id JOIN productos pr ON pr.id = l.producto_id "
           "WHERE p.creado >= %s GROUP BY pr.categoria ORDER BY ventas DESC LIMIT 3")
    with psycopg.connect(PG) as c:
        filas = c.execute(sql, (desde,)).fetchall()
        t = mediana(lambda i: c.execute(sql, (desde,)).fetchall(), n=20)
    print("  Postgres, ventas por categoría desde 2026-09-01 (top 3):")
    for f in filas:
        print(f"    {f[0]}: {f[1]:,.2f}".replace(",", "_").replace(".", ",").replace("_", "."))
    print(f"  Postgres: mediana de 20: {t:.1f} ms")
    m = mongo().tienda.pedidos
    pipe = [{"$match": {"creado": {"$gte": desde}}}, {"$unwind": "$lineas"},
            {"$group": {"_id": "$lineas.categoria", "ventas": {"$sum": {"$multiply": ["$lineas.precio", "$lineas.cantidad"]}}}},
            {"$sort": {"ventas": -1}}, {"$limit": 3}]
    filas = list(m.aggregate(pipe))
    t = mediana(lambda i: list(m.aggregate(pipe)), n=20)
    print("  MongoDB, lo mismo con aggregate ($match, $unwind, $group), con la categoría copiada en cada línea:")
    for f in filas:
        print(f"    {f['_id']}: {f['ventas']:,.2f}".replace(",", "_").replace(".", ",").replace("_", "."))
    print(f"  MongoDB: mediana de 20: {t:.1f} ms")
    pipe2 = [{"$match": {"creado": {"$gte": desde}}}, {"$unwind": "$lineas"},
             {"$lookup": {"from": "productos", "localField": "lineas.producto_id", "foreignField": "_id", "as": "p"}},
             {"$unwind": "$p"},
             {"$group": {"_id": "$p.categoria", "ventas": {"$sum": {"$multiply": ["$p.precio", "$lineas.cantidad"]}}}},
             {"$sort": {"ventas": -1}}, {"$limit": 3}]
    t = mediana(lambda i: list(m.aggregate(pipe2)), n=5)
    print(f"  MongoDB, si la categoría NO estuviera copiada ($lookup a productos): mediana de 5: {t:.1f} ms")


def renombrar():
    with psycopg.connect(PG, autocommit=True) as c:
        _, t = cronometro(lambda: c.execute("UPDATE productos SET nombre = 'Producto 7 (nuevo nombre)' WHERE id = 7"))
        n = c.execute("SELECT count(DISTINCT pedido_id) FROM lineas WHERE producto_id = 7").fetchone()[0]
        print(f"  Postgres: UPDATE productos ... WHERE id = 7 → 1 fila en {t * 1000:.1f} ms; los {n} pedidos que lo "
              "llevan ya lo ven con el nombre nuevo (JOIN)")
    m = mongo().tienda
    m.productos.update_one({"_id": 7}, {"$set": {"nombre": "Producto 7 (nuevo nombre)"}})
    viejos = m.pedidos.count_documents({"lineas": {"$elemMatch": {"producto_id": 7, "nombre": "Producto 7"}}})
    print(f"  MongoDB: update_one en productos → pedidos que siguen diciendo «Producto 7»: {viejos}")
    r, t = cronometro(lambda: m.pedidos.update_many({"lineas.producto_id": 7},
                                                     {"$set": {"lineas.$[l].nombre": "Producto 7 (nuevo nombre)"}},
                                                     array_filters=[{"l.producto_id": 7}]))
    print(f"  MongoDB: arreglarlos con update_many y array_filters → {r.modified_count} documentos en {t * 1000:.0f} ms "
          "(sin índice en lineas.producto_id: recorre todos)")


def transaccion():
    print("  Pagar el pedido 4242 y descontar su stock, todo o nada:")
    with psycopg.connect(PG) as c:
        def pagar(i):
            with c.transaction():
                c.execute("UPDATE pedidos SET pagado = true WHERE id = %s", (i % PEDIDOS + 1,))
                c.execute("UPDATE productos p SET stock = stock - l.cantidad FROM lineas l "
                          "WHERE l.pedido_id = %s AND p.id = l.producto_id", (i % PEDIDOS + 1,))
        t = mediana(pagar)
        print(f"  Postgres: BEGIN; UPDATE pedidos; UPDATE productos; COMMIT → mediana de 1.000: {t:.3f} ms")
    rs = len(sys.argv) > 2 and sys.argv[2] == "rs"
    cli = mongo(rs)
    m = cli.tienda

    def pagar_m(i):
        pid = i % PEDIDOS + 1
        with cli.start_session() as s:
            with s.start_transaction():
                d = m.pedidos.find_one_and_update({"_id": pid}, {"$set": {"pagado": True}}, session=s)
                for l in d["lineas"]:
                    m.productos.update_one({"_id": l["producto_id"]}, {"$inc": {"stock": -l["cantidad"]}}, session=s)
    try:
        t = mediana(pagar_m)
        print(f"  MongoDB{' (replica set de 1 nodo)' if rs else ''}: start_transaction; find_one_and_update; "
              f"update_one × líneas; commit → mediana de 1.000: {t:.3f} ms")
    except Exception as e:  # noqa: BLE001
        print(f"  MongoDB{' (replica set de 1 nodo)' if rs else ' (un nodo suelto)'}: {type(e).__name__}: "
              f"{str(e).split(', full error')[0]}")


def jsonb():
    with psycopg.connect(PG, autocommit=True) as c:
        c.execute("DROP TABLE IF EXISTS pedidos_json")
        _, t = cronometro(lambda: c.execute("""CREATE TABLE pedidos_json AS
            SELECT p.id, jsonb_build_object('cliente', jsonb_build_object('id', cl.id, 'nombre', cl.nombre),
                   'lineas', jsonb_agg(jsonb_build_object('producto_id', l.producto_id, 'categoria', pr.categoria,
                                                          'cantidad', l.cantidad))) AS datos
            FROM pedidos p JOIN clientes cl ON cl.id = p.cliente_id JOIN lineas l ON l.pedido_id = p.id
            JOIN productos pr ON pr.id = l.producto_id GROUP BY p.id, cl.id"""))
        c.execute("ALTER TABLE pedidos_json ADD PRIMARY KEY (id)")
        print(f"  Postgres: CREATE TABLE pedidos_json (id, datos jsonb) con el mismo documento → {t:.1f} s")
        q = "SELECT count(*) FROM pedidos_json WHERE datos @> '{\"cliente\": {\"id\": 4242}}'"
        n = c.execute(q).fetchone()[0]
        t1 = mediana(lambda i: c.execute(q).fetchone(), n=20)
        c.execute("CREATE INDEX ON pedidos_json USING gin (datos jsonb_path_ops)")
        c.execute("ANALYZE pedidos_json")
        t2 = mediana(lambda i: c.execute(q).fetchone(), n=200)
        print(f"  Postgres: pedidos del cliente 4242 dentro del jsonb (@>): {n} · sin índice {t1:.1f} ms · "
              f"con índice GIN {t2:.3f} ms")
    m = mongo().tienda.pedidos
    m.create_index("cliente.id")
    t3 = mediana(lambda i: m.count_documents({"cliente.id": 4242}), n=200)
    print(f"  MongoDB: count_documents({{'cliente.id': 4242}}) con índice → {t3:.3f} ms")


if __name__ == "__main__":
    {"cargar": cargar, "leer": leer, "esquema": esquema, "cruzar": cruzar, "renombrar": renombrar,
     "transaccion": transaccion, "jsonb": jsonb}[sys.argv[1]]()
