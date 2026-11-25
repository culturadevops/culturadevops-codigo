# SALIDA — «System design: el teorema CAP» (cultura-devops, vídeo 353)

> Generado por `correr.py`. **No se escribe a mano.**

- fecha: `2026-10-11 17:23:04Z`
- etcd 3.6.5 (tres nodos) · Redis server v=7.2.16 (primario, réplica y tres sentinels, down-after 3 s)
- la partición: `docker network disconnect`; los clientes escriben con `docker exec` dentro de cada lado.
- una sola máquina.

```
[etcd v3.6.5: tres nodos · líder: etcd1]
$ etcd1> etcdctl put saldo 100
  OK

== 1 · Se corta la red del líder (etcd1) ==
$ docker network disconnect sd-cap etcd1
$ etcd1> etcdctl put saldo 50   # en la minoría (1 de 3)
  {"level":"warn","ts":"2026-10-11T17:24:14.230348Z","logger":"etcd-client","caller":"v3@v3.6.5/retry_interceptor.go:65","msg":"retrying of unary invoker failed","target":"etcd-endpoints://0xc00033a5a0/127.0.0.1:2379","method":"/etcdserverpb.KV/Put","attempt":0,"error":"rpc error: code = DeadlineExceeded desc = context deadline exceeded"}
  Error: context deadline exceeded
  (contestó a los 3.1 s)
$ etcd2> etcdctl put saldo 70   # en la mayoría (2 de 3)
  {"level":"warn","ts":"2026-10-11T17:24:17.596447Z","logger":"etcd-client","caller":"v3@v3.6.5/retry_interceptor.go:65","msg":"retrying of unary invoker failed","target":"etcd-endpoints://0xc0003c65a0/127.0.0.1:2379","method":"/etcdserverpb.KV/Put","attempt":0,"error":"rpc error: code = DeadlineExceeded desc = context deadline exceeded"}
  Error: context deadline exceeded
$ etcd3> etcdctl get saldo   # mayoría
  70
$ etcd1> etcdctl get saldo   # minoría, lectura lineal (por defecto)
  {"level":"warn","ts":"2026-10-11T17:24:22.913529Z","logger":"etcd-client","caller":"v3@v3.6.5/retry_interceptor.go:65","msg":"retrying of unary invoker failed","target":"etcd-endpoints://0xc0003385a0/127.0.0.1:2379","method":"/etcdserverpb.KV/Range","attempt":0,"error":"rpc error: code = DeadlineExceeded desc = context deadline exceeded"}
  Error: context deadline exceeded
$ etcd1> etcdctl get saldo --consistency=s   # minoría, lectura serializable
  100
  nuevo líder en la mayoría: etcd2

== 2 · Vuelve la red ==
$ docker network connect sd-cap etcd1
$ etcd1> etcdctl get saldo   # el que estuvo aislado
  70
  escrituras perdidas: ninguna (la de la minoría nunca se aceptó)

== 3 · Redis: primario, réplica y tres sentinels. Se corta la red del primario ==
$ docker network disconnect sd-cap r1   # el primario, aislado con sus clientes
  los sentinels promueven a r2 a los 4.6 s (role:master)
  5 s escribiendo en r2 (mayoría, el nuevo primario): aceptadas 45 · rechazadas 0
  30 s escribiendo en r1 (minoría), que sigue creyéndose primario: aceptadas 282 · rechazadas 0
  claves minoria:* en r1 antes de reconectar: 282
$ docker network connect sd-cap r1
  r1 después: role:slave (los sentinels lo degradan a réplica de r2)
  claves minoria:* que quedan: 0 · perdidas: 282 de 282 aceptadas
  claves mayoria:* que quedan: 45 de 45

== 4 · Lo mismo con min-replicas-to-write 1 y min-replicas-max-lag 10 ==
$ docker network disconnect sd-cap r1   # el primario, aislado con sus clientes
  los sentinels promueven a r2 a los 34.2 s (role:master)
  5 s escribiendo en r2 (mayoría, el nuevo primario): aceptadas 0 · rechazadas 46
  30 s escribiendo en r1 (minoría), que sigue creyéndose primario: aceptadas 81 · rechazadas 201 · último error: NOREPLICAS Not enough good replicas to write.
  claves minoria:* en r1 antes de reconectar: 81
$ docker network connect sd-cap r1
  r1 después: role:slave (los sentinels lo degradan a réplica de r2)
  claves minoria:* que quedan: 0 · perdidas: 81 de 81 aceptadas
  claves mayoria:* que quedan: 0 de 0
```
