# SALIDA — «System design: SQL o NoSQL» (cultura-devops, vídeo 352)

> Generado por `correr.py`. **No se escribe a mano.**

- fecha: `2026-10-12 00:16:56Z`
- PostgreSQL 17.11 · MongoDB 8.0.15 · cliente Python 3.13 (psycopg 3.2.3, pymongo 4.10.1) dentro de la red
- datos de las dos en tmpfs (memoria); una sola máquina, sin renders a la vez; los contenedores del banco van con prioridad de CPU (--cpu-shares 8192 frente a 1024).

```
== 1 · La misma tienda en las dos ==
$ python lab.py cargar
  100.000 pedidos · 300.535 líneas · 20.000 clientes · 1.000 productos
  carga: Postgres 8.1 s (COPY) · MongoDB 0.7 s (insert_many)
  tamaño: Postgres 29 MB (4 tablas e índices) · MongoDB pedidos 12 MB comprimidos + índices 2 MB

== 2 · Leer un pedido entero ==
$ python lab.py leer
  Postgres, el pedido 4242 (JOIN de 4 tablas):
    4242 · Cliente 3695 · Producto 43 · cat03 · 117.81 × 4
    4242 · Cliente 3695 · Producto 564 · cat04 · 173.91 × 4
    4242 · Cliente 3695 · Producto 926 · cat06 · 157.92 × 4
  Postgres: leer un pedido entero, mediana de 1.000: 0.195 ms
  MongoDB, el pedido 4242 (un documento): cliente=Cliente 3695 · 3 líneas dentro · primera: Producto 926 157.92
  MongoDB: leer un pedido entero, mediana de 1.000: 0.171 ms

== 3 · Cambiar el esquema: los pedidos ahora llevan moneda ==
$ python lab.py esquema
  Postgres: ALTER TABLE pedidos ADD COLUMN moneda text NOT NULL DEFAULT 'MXN' → 3.5 ms
  Postgres: pedidos con moneda = 'MXN': 100.000 de 100.000
  Postgres: insertar un pedido sin moneda → NotNullViolation: null value in column "moneda" of relation "pedidos" violates not-null constraint
  MongoDB: no hay ALTER; el código nuevo empieza a escribir «moneda» en los pedidos nuevos
  MongoDB: pedidos con moneda = 'MXN': 1 de 100.001
  MongoDB: insertar un pedido sin moneda → aceptado (sin esquema, nadie lo impide)
  MongoDB: rellenar los viejos con update_many → 100.001 documentos en 0.7 s

== 4 · Una consulta que cruza datos: ventas por categoría ==
$ python lab.py cruzar
  Postgres, ventas por categoría desde 2026-09-01 (top 3):
    cat11: 887.050,02
    cat01: 872.730,35
    cat03: 860.615,07
  Postgres: mediana de 20: 13.8 ms
  MongoDB, lo mismo con aggregate ($match, $unwind, $group), con la categoría copiada en cada línea:
    cat11: 887.050,02
    cat01: 872.730,35
    cat03: 860.615,07
  MongoDB: mediana de 20: 30.6 ms
  MongoDB, si la categoría NO estuviera copiada ($lookup a productos): mediana de 5: 335.0 ms

== 5 · Cambiar el nombre de un producto ==
$ python lab.py renombrar
  Postgres: UPDATE productos ... WHERE id = 7 → 1 fila en 2.4 ms; los 285 pedidos que lo llevan ya lo ven con el nombre nuevo (JOIN)
  MongoDB: update_one en productos → pedidos que siguen diciendo «Producto 7»: 285
  MongoDB: arreglarlos con update_many y array_filters → 285 documentos en 55 ms (sin índice en lineas.producto_id: recorre todos)

== 6 · Una transacción entre dos documentos ==
$ python lab.py transaccion
  Pagar el pedido 4242 y descontar su stock, todo o nada:
  Postgres: BEGIN; UPDATE pedidos; UPDATE productos; COMMIT → mediana de 1.000: 1.062 ms
  MongoDB (un nodo suelto): OperationFailure: Transaction numbers are only allowed on a replica set member or mongos
  [MongoDB se reinicia como replica set de un nodo, se vuelve a cargar]
$ python lab.py transaccion rs
  Pagar el pedido 4242 y descontar su stock, todo o nada:
  Postgres: BEGIN; UPDATE pedidos; UPDATE productos; COMMIT → mediana de 1.000: 1.070 ms
  MongoDB (replica set de 1 nodo): start_transaction; find_one_and_update; update_one × líneas; commit → mediana de 1.000: 1.459 ms

== 7 · El término medio: JSONB en Postgres ==
$ python lab.py jsonb
  Postgres: CREATE TABLE pedidos_json (id, datos jsonb) con el mismo documento → 0.8 s
  Postgres: pedidos del cliente 4242 dentro del jsonb (@>): 4 · sin índice 19.9 ms · con índice GIN 0.077 ms
  MongoDB: count_documents({'cliente.id': 4242}) con índice → 0.370 ms
```
