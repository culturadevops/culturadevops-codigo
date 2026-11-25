# SALIDA — Valkey contra Redis

Generado por `python correr.py`. **No se edita a mano.**

- fecha: 2026-10-01 22:06 UTC
- Docker 29.6.2
- imágenes: valkey/valkey:latest · redis:latest · python:3.12-slim
- límites por contenedor: --cpus=2 --memory=1g

## 1 · Versiones

### INFO server · valkey

`$ redis-cli -h valkey INFO server`

```
redis_version:7.2.4
server_name:valkey
valkey_version:9.1.2
os:Linux 6.18.33.2-microsoft-standard-WSL2 x86_64
arch_bits:64
multiplexing_api:epoll
```

### HELLO 3 · valkey

`$ redis-cli -h valkey -3 HELLO 3`

```
server valkey
version 9.1.2
proto 3
id 5
mode standalone
role master
modules name lua
ver 1
path lua
args
```

### INFO server · redis

`$ redis-cli -h redis INFO server`

```
redis_version:8.10.2
redis_mode:standalone
os:Linux 6.18.33.2-microsoft-standard-WSL2 x86_64
arch_bits:64
multiplexing_api:epoll
```

### HELLO 3 · redis

`$ redis-cli -h redis -3 HELLO 3`

```
server redis
version 8.10.2
proto 3
id 13
mode standalone
role master
modules name timeseries
ver 81001
path /usr/local/lib/redis/modules//redistimeseries.so
args 
name vectorset
ver 1
path 
args 
name search
ver 81001
path /usr/local/lib/redis/modules//redisearch.so
args 
name bf
ver 81001
path /usr/local/lib/redis/modules//redisbloom.so
args 
name ReJSON
ver 81000
path /usr/local/lib/redis/modules//rejson.so
args
```

## 3 · Clientes de Redis contra Valkey

### redis-cli contra valkey

`$ redis-cli -h valkey SET/GET/INCR/EXPIRE/TTL`

```
OK
hola
1
1
60
```

### redis-py contra valkey

`$ pip install redis && python -c ...`

```
redis-py 8.1.0
GET k = b'v'
1000 INCR en pipeline = 1000
server: {'redis_version': '7.2.4', 'server_name': 'valkey', 'valkey_version': '9.1.2', 'gcc_version': '14.2.0'}
```

## 4 · Migrar datos (RDB y réplica)

### RDB de redis cargado en valkey

`$ SAVE en redis → arrancar valkey con el mismo /data → DBSIZE`

```
primeros 9 bytes del dump.rdb de redis: REDIS0015
DBSIZE en redis antes: 100000
DBSIZE en valkey después: Could not connect to Redis at destino:6379: No address associated with hostname

log de valkey:
6:M 01 Oct 2026 22:06:42.853 # Can't handle RDB format version 15
6:M 01 Oct 2026 22:06:42.853 # Fatal error loading the DB, check server logs. Exiting.
```

### RDB de valkey cargado en redis

`$ SAVE en valkey → arrancar redis con el mismo /data → DBSIZE`

```
primeros 9 bytes del dump.rdb de valkey: VALKEY080
DBSIZE en valkey antes: 100000
DBSIZE en redis después: Could not connect to Redis at destino:6379: No address associated with hostname

log de redis:
1:M 01 Oct 2026 22:06:58.293 # Wrong signature trying to load DB from file
1:M 01 Oct 2026 22:06:58.293 # Fatal error loading the DB, check server logs. Exiting.
```

### RDB de redis 7.2 cargado en valkey

`$ SAVE en redis:7.2 → arrancar valkey con el mismo /data`

```
redis_version:7.2.16
primeros 9 bytes del dump.rdb: REDIS0011
DBSIZE en redis 7.2: 100000
DBSIZE en valkey después: 100000
```

### redis 8 → valkey en caliente

`$ python _copia.py   (DUMP/RESTORE y copia lógica)`

```
DUMP/RESTORE: ResponseError DUMP payload version or checksum are wrong
copia lógica SCAN+MGET+SET: 100001 claves en 0.58 s
DBSIZE en valkey: 100001
```

### valkey como réplica de redis

`$ redis-cli -h valkey REPLICAOF redis 6379 ; INFO replication ; DBSIZE`

```
role:slave
master_host:redis
master_link_status:down
master_sync_in_progress:0
DBSIZE en valkey: 0

log de valkey:
7:S 01 Oct 2026 22:07:27.771 # Can't handle RDB format version 15
7:S 01 Oct 2026 22:07:27.771 # Failed trying to load the PRIMARY synchronization DB from disk, check server logs.
7:S 01 Oct 2026 22:07:27.771 * PRIMARY <-> REPLICA sync: Skipping flush, no new data was loaded.
7:S 01 Oct 2026 22:07:27.771 # Failed to load RDB
7:S 01 Oct 2026 22:07:27.771 * Reconnecting to PRIMARY redis:6379 after failure
7:S 01 Oct 2026 22:07:27.772 * PRIMARY <-> REPLICA sync started
7:S 01 Oct 2026 22:07:27.772 * Non blocking connect for SYNC fired the event.
7:S 01 Oct 2026 22:07:27.772 * Primary replied to PING, replication can continue...
7:S 01 Oct 2026 22:07:27.772 * (Non critical) Primary does not understand REPLCONF VERSION: -ERR Unrecognized REPLCONF option: version
7:S 01 Oct 2026 22:07:27.772 * Partial resynchronization not possible (no cached primary)
```

## 5 · Memoria con los mismos datos (100.000 claves de 50 bytes)

### used_memory

`$ INFO memory antes y después de 100.000 SET`

```
valkey  vacío    968,928 B   con datos  10,451,520 B   por clave   94.8 B   (9.97M)
redis   vacío  1,445,504 B   con datos  11,895,536 B   por clave  104.5 B   (11.34M)
```

## 2 · Benchmark (mismo cliente, mismos límites, 3 pasadas, mediana)

### valkey · pipeline 16 · pasada 1

`$ redis-benchmark -h valkey --csv -t set,get -n 10000000 -c 50 -P 16 --threads 2`

```
"test","rps","avg_latency_ms","min_latency_ms","p50_latency_ms","p95_latency_ms","p99_latency_ms","max_latency_ms"
"SET","2104820.00","0.347","0.056","0.359","0.463","0.527","2.119"
"GET","2500000.00","0.285","0.048","0.295","0.383","0.447","1.551"
```

### valkey · pipeline 16 · pasada 2

`$ redis-benchmark -h valkey --csv -t set,get -n 10000000 -c 50 -P 16 --threads 2`

```
"test","rps","avg_latency_ms","min_latency_ms","p50_latency_ms","p95_latency_ms","p99_latency_ms","max_latency_ms"
"SET","2104820.00","0.352","0.048","0.359","0.471","0.543","2.431"
"GET","2500625.00","0.285","0.048","0.287","0.383","0.447","2.591"
```

### valkey · pipeline 16 · pasada 3

`$ redis-benchmark -h valkey --csv -t set,get -n 10000000 -c 50 -P 16 --threads 2`

```
"test","rps","avg_latency_ms","min_latency_ms","p50_latency_ms","p95_latency_ms","p99_latency_ms","max_latency_ms"
"SET","2104820.00","0.352","0.056","0.359","0.471","0.559","1.695"
"GET","2498750.75","0.287","0.048","0.287","0.391","0.471","2.247"
```

### valkey · sin pipeline · pasada 1

`$ redis-benchmark -h valkey --csv -t set,get -n 1000000 -c 50 --threads 2`

```
"test","rps","avg_latency_ms","min_latency_ms","p50_latency_ms","p95_latency_ms","p99_latency_ms","max_latency_ms"
"SET","307597.66","0.141","0.016","0.135","0.207","0.271","1.903"
"GET","307597.66","0.137","0.024","0.135","0.207","0.263","1.855"
```

### valkey · sin pipeline · pasada 2

`$ redis-benchmark -h valkey --csv -t set,get -n 1000000 -c 50 --threads 2`

```
"test","rps","avg_latency_ms","min_latency_ms","p50_latency_ms","p95_latency_ms","p99_latency_ms","max_latency_ms"
"SET","307597.66","0.141","0.024","0.135","0.207","0.279","2.927"
"GET","307597.66","0.138","0.024","0.135","0.207","0.279","1.991"
```

### valkey · sin pipeline · pasada 3

`$ redis-benchmark -h valkey --csv -t set,get -n 1000000 -c 50 --threads 2`

```
"test","rps","avg_latency_ms","min_latency_ms","p50_latency_ms","p95_latency_ms","p99_latency_ms","max_latency_ms"
"SET","307597.66","0.142","0.024","0.135","0.215","0.295","1.711"
"GET","307881.78","0.137","0.024","0.135","0.199","0.271","0.959"
```

### redis · pipeline 16 · pasada 1

`$ redis-benchmark -h redis --csv -t set,get -n 10000000 -c 50 -P 16 --threads 2`

```
"test","rps","avg_latency_ms","min_latency_ms","p50_latency_ms","p95_latency_ms","p99_latency_ms","max_latency_ms"
"SET","2351834.50","0.308","0.048","0.311","0.415","0.487","1.855"
"GET","2856326.75","0.240","0.048","0.239","0.327","0.399","1.455"
```

### redis · pipeline 16 · pasada 2

`$ redis-benchmark -h redis --csv -t set,get -n 10000000 -c 50 -P 16 --threads 2`

```
"test","rps","avg_latency_ms","min_latency_ms","p50_latency_ms","p95_latency_ms","p99_latency_ms","max_latency_ms"
"SET","2352387.75","0.307","0.056","0.311","0.415","0.503","2.607"
"GET","2856326.75","0.242","0.040","0.239","0.335","0.399","1.639"
```

### redis · pipeline 16 · pasada 3

`$ redis-benchmark -h redis --csv -t set,get -n 10000000 -c 50 -P 16 --threads 2`

```
"test","rps","avg_latency_ms","min_latency_ms","p50_latency_ms","p95_latency_ms","p99_latency_ms","max_latency_ms"
"SET","2351834.50","0.308","0.048","0.311","0.423","0.511","1.759"
"GET","2856326.75","0.246","0.040","0.247","0.343","0.415","2.391"
```

### redis · sin pipeline · pasada 1

`$ redis-benchmark -h redis --csv -t set,get -n 1000000 -c 50 --threads 2`

```
"test","rps","avg_latency_ms","min_latency_ms","p50_latency_ms","p95_latency_ms","p99_latency_ms","max_latency_ms"
"SET","307597.66","0.139","0.016","0.135","0.207","0.279","2.527"
"GET","333333.34","0.134","0.024","0.135","0.207","0.287","2.247"
```

### redis · sin pipeline · pasada 2

`$ redis-benchmark -h redis --csv -t set,get -n 1000000 -c 50 --threads 2`

```
"test","rps","avg_latency_ms","min_latency_ms","p50_latency_ms","p95_latency_ms","p99_latency_ms","max_latency_ms"
"SET","307597.66","0.138","0.024","0.135","0.207","0.271","2.431"
"GET","333333.34","0.136","0.024","0.135","0.199","0.263","1.271"
```

### redis · sin pipeline · pasada 3

`$ redis-benchmark -h redis --csv -t set,get -n 1000000 -c 50 --threads 2`

```
"test","rps","avg_latency_ms","min_latency_ms","p50_latency_ms","p95_latency_ms","p99_latency_ms","max_latency_ms"
"SET","307692.31","0.138","0.016","0.135","0.207","0.279","1.183"
"GET","307597.66","0.136","0.024","0.135","0.199","0.279","1.447"
```

### resumen (medianas)

`$ calculado de las pasadas de arriba`

```
prueba          op    valkey (req/s)   redis (req/s)   valkey/redis
pipeline 16     SET        2,104,820       2,351,834         0.89x
pipeline 16     GET        2,500,000       2,856,327         0.88x
sin pipeline    SET          307,598         307,598         1.00x
sin pipeline    GET          307,598         333,333         0.92x
```
