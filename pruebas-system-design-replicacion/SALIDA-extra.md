# SALIDA — replicación, segunda parte (cultura-devops, vídeo 351)

> Generado por `correr_extra.py`. **No se escribe a mano.**

- fecha: `2026-10-11 14:06:41Z` · mismo laboratorio que SALIDA.md

```
== 8 · Escribir en la réplica ==
$ psql -h sd-replica1 -c "INSERT INTO pedidos (total) VALUES (100)"
  ERROR:  cannot execute INSERT in a read-only transaction

== 9 · La réplica se cae y el primario sigue escribiendo: el slot guarda el WAL ==
  slot: r1 · physical · activo: true
  pg_wal antes: 32.0M
$ docker stop sd-replica1   y 10 s de carga de escritura en el primario
  slot: r1 · activo: false · WAL retenido: 490 MB
  pg_wal después: 512.0M
  max_slot_wal_keep_size: -1
```
