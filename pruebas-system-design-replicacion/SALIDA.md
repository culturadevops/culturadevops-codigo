# SALIDA — «System design: replicación» (cultura-devops, vídeo 351)

> Generado por `correr.py`. **No se escribe a mano.**

- fecha: `2026-10-11 05:05:35Z`
- `postgres (PostgreSQL) 17.11` · Docker `29.6.2`
- la réplica r1 va limitada a 0,25 CPU (`--cpus=0.25`) para que su retraso se vea en una sola máquina

```

== 1 · Un primario y una réplica en streaming, asíncrona (lo que viene por defecto) ==
réplica r1: streaming · async
  5 s de carga en el primario: 1.165.000 filas
  retraso máximo de la réplica: 238,7 MB de WAL sin aplicar (a los 5.2 s)
  replay_lag máximo: 2.338 ms
  al parar la carga, la réplica tarda 27,6 s en ponerse al día

== 2 · Leer de la réplica justo después de escribir en el primario ==
sin carga: 500 pedidos escritos en el primario y leídos al momento de la réplica -> 500 no estaban
    control: 1 s después, de esos 500 ya están 500
  con carga de escritura: 500 pedidos escritos en el primario y leídos al momento de la réplica -> 500 no estaban
    control: 1 s después, de esos 500 ya están 154
  esperando al LSN del commit antes de leer (con carga): 0 no estaban · espera mediana 3 ms, máxima 52582 ms

== 3 · Failover con replicación asíncrona: se cae el primario y se promueve la réplica ==
$ docker pause sd-replica1   (asíncrona: con 100 commits confirmados, la réplica deja de recibir, como un corte de red)
$ docker kill sd-primario    (2 s después, con escrituras en marcha) · docker unpause sd-replica1
commits confirmados por el primario antes de caer: 313
$ SELECT pg_promote();   -> t
en la réplica promovida: 105 de 313 · confirmados y PERDIDOS: 208

== 4 · Failover con replicación síncrona (synchronous_standby_names = 'r1') ==
  synchronous_standby_names = 'r1' -> r1 sync
$ docker pause sd-replica1   (síncrona: con 100 commits confirmados, la réplica deja de recibir, como un corte de red)
$ docker kill sd-primario    (2 s después, con escrituras en marcha) · docker unpause sd-replica1
commits confirmados por el primario antes de caer: 103
$ SELECT pg_promote();   -> t
en la réplica promovida: 103 de 103 · confirmados y PERDIDOS: 0

== 5 · Lo que cuesta la síncrona: latencia de cada commit ==
  synchronous_standby_names = 'r1' -> r1 sync
asíncrona (local)          mediana 0,81 ms · p99 5,57 ms
  síncrona (on)              mediana 1,28 ms · p99 1,94 ms
  síncrona (remote_apply)    mediana 1,44 ms · p99 5,26 ms

== 6 · La otra cara: la réplica síncrona se cae ==
$ docker stop sd-replica1
a los 8 s el INSERT sigue esperando (statement_timeout = 2 s no lo corta)
  $ SELECT pg_cancel_backend(pid)   -- desde otra conexión
  el INSERT volvió en 8,3 s
  aviso de Postgres: canceling wait for synchronous replication due to user request
  aviso de Postgres: The transaction has already committed locally, but might not have been replicated to the standby.
  ¿quedó escrito en el primario?: True (pedidos antes: 900, ahora: 901)

== 7 · Lo correcto: dos réplicas y ANY 1 (basta con que confirme una) ==
  synchronous_standby_names = 'ANY 1 (r1, r2)' -> r1 quorum, r2 quorum
$ docker stop sd-replica1   (synchronous_standby_names = 'ANY 1 (r1, r2)')
el INSERT volvió en 0,0 s
  ¿quedó escrito en el primario?: True (pedidos antes: 0, ahora: 1)
```
