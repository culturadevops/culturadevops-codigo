# SALIDA-extra — «System design: índices» (cultura-devops, vídeo 348)

> Generado por `correr_extra.py`. **No se escribe a mano.**

- fecha: `2026-10-11 18:08:00Z`
- PostgreSQL 17.11 · la misma tabla de correr.py (2.000.000 de pedidos) · datos en tmpfs
- una sola máquina, renderizando vídeo a la vez. Cada consulta: mediana de 5 ejecuciones.

```
== 1 · La fecha convertida frente al rango, con un índice sobre creado ==
$ CREATE INDEX pedidos_creado ON pedidos (creado);
$ EXPLAIN ANALYZE SELECT id FROM pedidos WHERE creado::date = date '2026-01-15'
  Seq Scan on pedidos (actual time=0.117..131.806 rows=1775 loops=1)
    Filter: ((creado)::date = '2026-01-15'::date)
    Rows Removed by Filter: 1998225
    Buffers: shared hit=24588
  mediana de 5: 189.632 ms
$ EXPLAIN ANALYZE SELECT id FROM pedidos WHERE creado >= '2026-01-15' AND creado < '2026-01-16'
  Bitmap Heap Scan on pedidos (actual time=0.426..5.557 rows=1775 loops=1)
    Recheck Cond: ((creado >= '2026-01-15 00:00:00+00'::timestamp with time zone) AND (creado < '2026-01-16 00:00:00+00'::timestamp with time zone))
    Heap Blocks: exact=1709
    Buffers: shared hit=1717
    ->  Bitmap Index Scan on pedidos_creado (actual time=0.294..0.294 rows=1775 loops=1)
          Index Cond: ((creado >= '2026-01-15 00:00:00+00'::timestamp with time zone) AND (creado < '2026-01-16 00:00:00+00'::timestamp with time zone))
          Buffers: shared hit=8
  mediana de 5: 5.750 ms

== 2 · Los 10 pedidos más recientes ==
$ EXPLAIN ANALYZE SELECT id, creado FROM pedidos ORDER BY creado DESC LIMIT 10
  Limit (actual time=0.020..0.080 rows=10 loops=1)
    Buffers: shared hit=13
    ->  Index Scan Backward using pedidos_creado on pedidos (actual time=0.020..0.079 rows=10 loops=1)
          Buffers: shared hit=13
  mediana de 5: 0.096 ms
$ DROP INDEX pedidos_creado;
$ EXPLAIN ANALYZE SELECT id, creado FROM pedidos ORDER BY creado DESC LIMIT 10
  Limit (actual time=233.925..233.927 rows=10 loops=1)
    Buffers: shared hit=24591
    ->  Sort (actual time=233.923..233.924 rows=10 loops=1)
          Sort Key: creado DESC
          Sort Method: top-N heapsort  Memory: 25kB
          Buffers: shared hit=24591
          ->  Seq Scan on pedidos (actual time=0.012..121.333 rows=2000000 loops=1)
                Buffers: shared hit=24588
  mediana de 5: 177.408 ms

== 3 · Índice parcial: solo los pendientes (5 %) ==
$ CREATE INDEX pedidos_creado_todos ON pedidos (creado);
$ CREATE INDEX pedidos_pendientes ON pedidos (creado) WHERE estado = 'pendiente';
  pedidos_creado_todos: 43 MB · pedidos_pendientes: 2208 kB
$ EXPLAIN ANALYZE SELECT id FROM pedidos WHERE estado = 'pendiente' ORDER BY creado LIMIT 20
  Limit (actual time=0.018..0.140 rows=20 loops=1)
    Buffers: shared hit=22
    ->  Index Scan using pedidos_pendientes on pedidos (actual time=0.017..0.139 rows=20 loops=1)
          Buffers: shared hit=22
  mediana de 5: 0.219 ms

== 4 · Índice que cubre la consulta: el total de los pedidos de un cliente ==
$ CREATE INDEX pedidos_cliente ON pedidos (cliente_id);
$ EXPLAIN ANALYZE SELECT sum(total) FROM pedidos WHERE cliente_id BETWEEN 4000 AND 4999
    Buffers: shared hit=13604
    ->  Bitmap Heap Scan on pedidos (actual time=10.134..51.222 rows=19771 loops=1)
          Recheck Cond: ((cliente_id >= 4000) AND (cliente_id <= 4999))
          Heap Blocks: exact=13582
          Buffers: shared hit=13604
          ->  Bitmap Index Scan on pedidos_cliente (actual time=7.780..7.780 rows=19771 loops=1)
                Index Cond: ((cliente_id >= 4000) AND (cliente_id <= 4999))
                Buffers: shared hit=22
  mediana de 5: 55.724 ms
$ CREATE INDEX pedidos_cliente_total ON pedidos (cliente_id) INCLUDE (total);
$ EXPLAIN ANALYZE SELECT sum(total) FROM pedidos WHERE cliente_id BETWEEN 4000 AND 4999
    Buffers: shared hit=79
    ->  Index Only Scan using pedidos_cliente_total on pedidos (actual time=0.058..1.764 rows=19771 loops=1)
          Index Cond: ((cliente_id >= 4000) AND (cliente_id <= 4999))
          Heap Fetches: 0
          Buffers: shared hit=79
  mediana de 5: 3.161 ms
```
