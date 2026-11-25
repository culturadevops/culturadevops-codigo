# SALIDA — «System design: índices» (cultura-devops, vídeo 348)

> Generado por `correr.py`. **No se escribe a mano.**

- fecha: `2026-10-11 17:31:23Z`
- PostgreSQL 17.11 (y 18 en la sección 5b) · shared_buffers 512MB · sin paralelismo · 2.000.000 filas
- una sola máquina; los tiempos son de esta. Cada consulta: mediana de 5 ejecuciones.
- los datos de Postgres van en tmpfs (memoria): la máquina renderiza vídeo a la vez y el disco metía ruido en las inserciones.

```
[tabla pedidos: 2.000.000 filas generadas en 147.0 s]
  tabla: 192 MB

== 1 · Buscar los pedidos de un cliente ==
  filas que devuelve: 19
$ EXPLAIN ANALYZE SELECT * FROM pedidos WHERE cliente_id = 4242
  Seq Scan on pedidos (actual time=0.281..53.046 rows=19 loops=1)
    Filter: (cliente_id = 4242)
    Rows Removed by Filter: 1999981
    Buffers: shared hit=24588
  mediana de 5: 65.994 ms
$ CREATE INDEX pedidos_cliente ON pedidos (cliente_id);   -- 28.8 s
  índice: 15 MB
$ EXPLAIN ANALYZE SELECT * FROM pedidos WHERE cliente_id = 4242
  Bitmap Heap Scan on pedidos (actual time=0.036..0.218 rows=19 loops=1)
    Recheck Cond: (cliente_id = 4242)
    Heap Blocks: exact=19
    Buffers: shared hit=22
    ->  Bitmap Index Scan on pedidos_cliente (actual time=0.021..0.021 rows=19 loops=1)
          Index Cond: (cliente_id = 4242)
          Buffers: shared hit=3
  mediana de 5: 0.421 ms
  → 157 veces más rápido

== 2 · Poca selectividad: el 80 % de los pedidos está 'entregado' ==
$ CREATE INDEX pedidos_estado ON pedidos (estado);
  entregado 80.0 % · enviado 15.0 % · pendiente 5.0 %
$ EXPLAIN ANALYZE SELECT sum(total) FROM pedidos WHERE estado = 'entregado'
    Buffers: shared hit=24588
    ->  Seq Scan on pedidos (actual time=0.016..122.372 rows=1599070 loops=1)
          Filter: (estado = 'entregado'::text)
          Rows Removed by Filter: 400930
          Buffers: shared hit=24588
  mediana de 5: 266.036 ms
$ EXPLAIN ANALYZE SELECT sum(total) FROM pedidos WHERE estado = 'pendiente'
    Buffers: shared hit=24294
    ->  Bitmap Heap Scan on pedidos (actual time=5.023..37.937 rows=100051 loops=1)
          Recheck Cond: (estado = 'pendiente'::text)
          Heap Blocks: exact=24206
          Buffers: shared hit=24294
          ->  Bitmap Index Scan on pedidos_estado (actual time=3.024..3.025 rows=100051 loops=1)
                Index Cond: (estado = 'pendiente'::text)
                Buffers: shared hit=88
  mediana de 5: 44.081 ms

== 3 · Función sobre la columna ==
$ CREATE INDEX pedidos_email ON pedidos (email);
$ EXPLAIN ANALYZE SELECT id FROM pedidos WHERE email = 'Cliente777777@correo.test'
  Index Scan using pedidos_email on pedidos (actual time=0.076..0.078 rows=1 loops=1)
    Index Cond: (email = 'Cliente777777@correo.test'::text)
    Buffers: shared hit=4
  mediana de 5: 0.098 ms
$ EXPLAIN ANALYZE SELECT id FROM pedidos WHERE lower(email) = 'cliente777777@correo.test'
  Seq Scan on pedidos (actual time=110.540..293.816 rows=1 loops=1)
    Filter: (lower(email) = 'cliente777777@correo.test'::text)
    Rows Removed by Filter: 1999999
    Buffers: shared hit=24588
  mediana de 5: 301.532 ms
$ CREATE INDEX pedidos_email_lower ON pedidos (lower(email));
$ EXPLAIN ANALYZE SELECT id FROM pedidos WHERE lower(email) = 'cliente777777@correo.test'
  Index Scan using pedidos_email_lower on pedidos (actual time=0.033..0.034 rows=1 loops=1)
    Index Cond: (lower(email) = 'cliente777777@correo.test'::text)
    Buffers: shared hit=4
  mediana de 5: 0.113 ms
$ EXPLAIN ANALYZE SELECT id FROM pedidos WHERE creado::date = date '2026-01-15'
  Seq Scan on pedidos (actual time=0.110..129.732 rows=1775 loops=1)
    Filter: ((creado)::date = '2026-01-15'::date)
    Rows Removed by Filter: 1998225
    Buffers: shared hit=24588
  mediana de 5: 168.509 ms
$ EXPLAIN ANALYZE SELECT id FROM pedidos WHERE creado >= '2026-01-15' AND creado < '2026-01-16'
  Seq Scan on pedidos (actual time=0.051..57.249 rows=1775 loops=1)
    Filter: ((creado >= '2026-01-15 00:00:00+00'::timestamp with time zone) AND (creado < '2026-01-16 00:00:00+00'::timestamp with time zone))
    Rows Removed by Filter: 1998225
    Buffers: shared hit=24588
  mediana de 5: 59.050 ms

== 4 · LIKE con el comodín delante y detrás ==
  collation de la base: en_US.utf8
$ EXPLAIN ANALYZE SELECT id FROM pedidos WHERE email LIKE 'Cliente77777%'
  Seq Scan on pedidos (actual time=3.797..115.461 rows=11 loops=1)
    Filter: (email ~~ 'Cliente77777%'::text)
    Rows Removed by Filter: 1999989
    Buffers: shared hit=24588
  mediana de 5: 120.976 ms
$ CREATE INDEX pedidos_email_patron ON pedidos (email text_pattern_ops);
$ EXPLAIN ANALYZE SELECT id FROM pedidos WHERE email LIKE 'Cliente77777%'
  Index Scan using pedidos_email_patron on pedidos (actual time=0.027..0.039 rows=11 loops=1)
    Index Cond: ((email ~>=~ 'Cliente77777'::text) AND (email ~<~ 'Cliente77778'::text))
    Filter: (email ~~ 'Cliente77777%'::text)
    Buffers: shared hit=5
  mediana de 5: 0.134 ms
$ EXPLAIN ANALYZE SELECT id FROM pedidos WHERE email LIKE '%77777@correo.test'
  Seq Scan on pedidos (actual time=5.919..141.014 rows=20 loops=1)
    Filter: (email ~~ '%77777@correo.test'::text)
    Rows Removed by Filter: 1999980
    Buffers: shared hit=24588
  mediana de 5: 168.905 ms

== 5 · Índice compuesto (estado, creado) y una consulta solo por creado ==
$ CREATE INDEX pedidos_estado_creado ON pedidos (estado, creado);
$ EXPLAIN ANALYZE SELECT id FROM pedidos WHERE estado = 'pendiente' AND creado >= '2026-09-01' AND creado < '2026-09-02'
  Index Scan using pedidos_estado_creado on pedidos (actual time=0.052..1.141 rows=91 loops=1)
    Index Cond: ((estado = 'pendiente'::text) AND (creado >= '2026-09-01 00:00:00+00'::timestamp with time zone) AND (creado < '2026-09-02 00:00:00+00'::timestamp with time zone))
    Buffers: shared hit=95
  mediana de 5: 0.846 ms
$ EXPLAIN ANALYZE SELECT id FROM pedidos WHERE creado >= '2026-09-01' AND creado < '2026-09-02'
  Seq Scan on pedidos (actual time=0.009..66.915 rows=1792 loops=1)
    Filter: ((creado >= '2026-09-01 00:00:00+00'::timestamp with time zone) AND (creado < '2026-09-02 00:00:00+00'::timestamp with time zone))
    Rows Removed by Filter: 1998208
    Buffers: shared hit=24588
  mediana de 5: 103.400 ms
$ CREATE INDEX pedidos_creado_estado ON pedidos (creado, estado);   -- el orden al revés
$ EXPLAIN ANALYZE SELECT id FROM pedidos WHERE creado >= '2026-09-01' AND creado < '2026-09-02'
  Bitmap Heap Scan on pedidos (actual time=0.476..9.342 rows=1792 loops=1)
    Recheck Cond: ((creado >= '2026-09-01 00:00:00+00'::timestamp with time zone) AND (creado < '2026-09-02 00:00:00+00'::timestamp with time zone))
    Heap Blocks: exact=1728
    Buffers: shared hit=1740
    ->  Bitmap Index Scan on pedidos_creado_estado (actual time=0.317..0.320 rows=1792 loops=1)
          Index Cond: ((creado >= '2026-09-01 00:00:00+00'::timestamp with time zone) AND (creado < '2026-09-02 00:00:00+00'::timestamp with time zone))
          Buffers: shared hit=12
  mediana de 5: 9.926 ms

== 5b · Lo mismo en PostgreSQL 18 (skip scan) ==
  [PostgreSQL 18.6]
$ CREATE INDEX pedidos_estado_creado ON pedidos (estado, creado);
$ EXPLAIN ANALYZE SELECT id FROM pedidos WHERE creado >= '2026-09-01' AND creado < '2026-09-02'
  Index Scan using pedidos_estado_creado on pedidos (actual time=0.059..4.820 rows=1792.00 loops=1)
    Index Cond: ((creado >= '2026-09-01 00:00:00+00'::timestamp with time zone) AND (creado < '2026-09-02 00:00:00+00'::timestamp with time zone))
    Buffers: shared hit=1833
  mediana de 5: 4.858 ms

== 6 · Lo que cuesta escribir: 200.000 inserciones con 0, 1, 3 y 6 índices ==
  0 índices: 6.48 s (mediana de 5) → 30.886 filas/s · índices ocupan 0 bytes
  1 índice: 6.67 s (mediana de 5) → 29.995 filas/s · índices ocupan 4424 kB
  3 índices: 10.75 s (mediana de 5) → 18.605 filas/s · índices ocupan 23 MB
  6 índices: 20.68 s (mediana de 5) → 9.670 filas/s · índices ocupan 38 MB
```
