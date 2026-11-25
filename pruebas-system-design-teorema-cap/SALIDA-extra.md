# SALIDA-extra — «System design: el teorema CAP» (cultura-devops, vídeo 353)

> Generado por `correr_extra.py`. **No se escribe a mano.**

- fecha: `2026-10-11 17:48:36Z`
- etcd 3.6.5 (tres nodos) · Redis 7.2.16 (primario y réplica) · cliente Python 3.13 (requests 2.32.5, redis 6.4.0) dentro de la red de Docker
- una sola máquina, que además estaba renderizando vídeo: los tres nodos comparten disco y CPU. Los datos de etcd van en tmpfs (memoria) para que el disco ocupado no meta segundos de fsync.

```
== 1 · Sin partición: lo que cuesta el consenso (1.000 operaciones seguidas, una a una) ==
  [cliente contra el líder de etcd (etcd1) y contra el primario de Redis]
etcd put (consenso de 3 nodos)             mediana  0.861 ms · p99   1.883 ms
  etcd get lineal (por defecto)              mediana  0.822 ms · p99   1.901 ms
  etcd get serializable                      mediana  0.540 ms · p99   1.073 ms
  (etcd contestó 503 «cambiando de líder» 0 veces; se reintentó, y cuenta en el tiempo)
  redis SET (asíncrono a la réplica)         mediana  0.064 ms · p99   0.153 ms
  redis SET + WAIT 1 (espera a la réplica)   mediana  0.178 ms · p99   0.404 ms

== 2 · Redis WAIT con el primario aislado ==
$ docker network disconnect sd-cap r1
$ r1> SET pedido:1 pagado ; WAIT 1 2000   # misma conexión: ¿cuántas réplicas lo tienen?
  OK
  0
  (SET + WAIT tardaron 3783 ms)

== 3 · etcd: se aísla a un seguidor (etcd2), no al líder ==
$ docker network disconnect sd-cap etcd2
$ etcd1> etcdctl put saldo 80   # en la mayoría, el líder de siempre
  OK
  (contestó a los 0.29 s)
$ etcd2> etcdctl put saldo 90   # en el seguidor aislado
  {"level":"warn","ts":"2026-10-11T17:51:31.093888Z","logger":"etcd-client","caller":"v3@v3.6.5/retry_interceptor.go:65","msg":"retrying of unary invoker failed","target":"etcd-endpoints://0xc000584000/127.0.0.1:2379","method":"/etcdserverpb.KV/Put","attempt":0,"error":"rpc error: code = DeadlineExceeded desc = context deadline exceeded"}
  Error: context deadline exceeded
  líder antes: etcd1 · después: etcd1 · término de Raft: 3 → 3 (no hubo elección)
```
