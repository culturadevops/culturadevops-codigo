# SALIDA — Valkey contra Redis

Generado por `python correr.py`. **No se edita a mano.**

- fecha: 2026-10-01 17:14 UTC
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
name bf
ver 81001
path /usr/local/lib/redis/modules//redisbloom.so
args 
name search
ver 81001
path /usr/local/lib/redis/modules//redisearch.so
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
7:M 01 Oct 2026 17:14:40.750 # Can't handle RDB format version 15
7:M 01 Oct 2026 17:14:40.750 # Fatal error loading the DB, check server logs. Exiting.
```

### RDB de valkey cargado en redis

`$ SAVE en valkey → arrancar redis con el mismo /data → DBSIZE`

```
primeros 9 bytes del dump.rdb de valkey: VALKEY080
DBSIZE en valkey antes: 100000
DBSIZE en redis después: Could not connect to Redis at destino:6379: No address associated with hostname

log de redis:
1:M 01 Oct 2026 17:14:57.931 # Wrong signature trying to load DB from file
1:M 01 Oct 2026 17:14:57.931 # Fatal error loading the DB, check server logs. Exiting.
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
copia lógica SCAN+MGET+SET: 100001 claves en 0.68 s
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
7:S 01 Oct 2026 17:15:32.891 # Can't handle RDB format version 15
7:S 01 Oct 2026 17:15:32.891 # Failed trying to load the PRIMARY synchronization DB from disk, check server logs.
7:S 01 Oct 2026 17:15:32.891 * PRIMARY <-> REPLICA sync: Skipping flush, no new data was loaded.
7:S 01 Oct 2026 17:15:32.891 # Failed to load RDB
7:S 01 Oct 2026 17:15:32.891 * Reconnecting to PRIMARY redis:6379 after failure
7:S 01 Oct 2026 17:15:32.892 * PRIMARY <-> REPLICA sync started
7:S 01 Oct 2026 17:15:32.892 * Non blocking connect for SYNC fired the event.
7:S 01 Oct 2026 17:15:32.892 * Primary replied to PING, replication can continue...
7:S 01 Oct 2026 17:15:32.892 * (Non critical) Primary does not understand REPLCONF VERSION: -ERR Unrecognized REPLCONF option: version
7:S 01 Oct 2026 17:15:32.892 * Partial resynchronization not possible (no cached primary)
```

## 5 · Memoria con los mismos datos (100.000 claves de 50 bytes)

### used_memory

`$ INFO memory antes y después de 100.000 SET`

```
valkey  vacío    969,632 B   con datos  10,455,296 B   por clave   94.9 B   (9.97M)
redis   vacío  1,445,504 B   con datos  11,901,088 B   por clave  104.6 B   (11.35M)
```
