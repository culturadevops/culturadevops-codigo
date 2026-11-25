# SALIDA — «System design: sharding» (cultura-devops, vídeo 347)

> Generado por `correr.py`. **No se escribe a mano.**

- fecha: `2026-10-11 05:05:36Z`
- `postgres (PostgreSQL) 17.11` × 5 (4 shards + 1 monolito)
- 1.000.000 de pedidos, 10.000 clientes; el cliente 777 hace el 20 %. Una sola máquina.

```
== 0 · Cargar los mismos pedidos de tres formas ==
$ lab cargar
1000000 pedidos de 10000 clientes (el 777 hace el 20 %) · 3 formas × 4 shards + 1 monolito · 48s

== 1 · Cómo se reparten las filas entre los 4 shards ==
$ lab reparto
hash_cliente   s0 399692 (40 %) · s1 200535 (20 %) · s2 199692 (20 %) · s3 200081 (20 %)
  rango_cliente  s0 399705 (40 %) · s1 200246 (20 %) · s2 199694 (20 %) · s3 200355 (20 %)
  hash_pedido    s0 250002 (25 %) · s1 249999 (25 %) · s2 249999 (25 %) · s3 250000 (25 %)

== 2 · Una consulta que va a un shard, y una que va a todos ==
$ lab consultas
pedidos del cliente 42 · hash_cliente: 1 shard (s3) · 78 pedidos · 2.437ms
  pedidos del cliente 42 · hash_pedido:  4 shards · 78 pedidos · 1.352ms
  ventas del día 7 · 4 shards en paralelo: 353357451 · 12ms  |  monolito: 353357451 · 20ms

== 3 · Los 5 clientes que más gastan: ¿sale bien sumando shard a shard? ==
$ lab top
top 5 clientes · monolito (la respuesta correcta): 777, 4978, 921, 7433, 3321
  top 5 clientes · hash_cliente top 5 de cada shard y mezclar: 777, 4978, 921, 7433, 3321  (¿correcto?: true)
  top 5 clientes · hash_pedido  top 5 de cada shard y mezclar: 777, 8445, 3321, 9036, 9725  (¿correcto?: false)

== 3b · El cliente grande, un pedido por su número y un email repetido ==
$ lab extra
gasto del cliente   42 · shard s3 ·     78 pedidos · 500µs
  gasto del cliente  777 · shard s0 · 199738 pedidos · 18.8ms
  el pedido 123456 · repartido por cliente: pregunto a los 4 shards · está en s1 (cliente 3816) · 6.4ms
  usuario 1 con ana@ejemplo.com en s0: <nil> · usuario 2 con el MISMO email en s1: <nil>

== 4 · Añadir un quinto shard: cuántas filas cambian de sitio ==
$ lab mover
hash_cliente   de 4 a 5 shards: hay que mover  838926 de 1000000 filas (84 %)
  rango_cliente  de 4 a 5 shards: hay que mover  401485 de 1000000 filas (40 %)
  hash_pedido    de 4 a 5 shards: hay que mover  799685 de 1000000 filas (80 %)
  rango_cliente  partir solo s0 (1251-2500 → s4): hay que mover  100350 de 1000000 filas (10 %)
```
