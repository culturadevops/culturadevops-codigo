# SALIDA — ¿Redis o Valkey? (cultura-devops, serie «¿X o Y? Lo medí» de herramientas)

> Corrida del 2026-11-05 13:22, bajo el candado _logs/banco.lock. Regenerable con `python correr.py`. ⛔ Ninguna cifra de blog: todo salió de aquí.

- Redis: `Starting Redis Server
Redis server v=8.8.4 sha=00000000:1 malloc=jemalloc-5.3.0 bits=64 build=458be34a08d26d6a` — imagen oficial `redis:8.8.4`
- Valkey: `Valkey server v=9.1.3 sha=00000000:0 malloc=jemalloc-5.3.0 bits=64 build=c6bf8b7f8673e9eb` — imagen oficial `valkey/valkey:9.1.3`
- Carga: `memtier_benchmark v=2.5.2 sha=00000000:0 bits=64 libevent=2.1.12-stable openssl=OpenSSL 3.0.2 15 Mar 2022 prometheus=yes` (`redislabs/memtier_benchmark:2.5.2`) desde otro contenedor con 6 CPU: 4 hilos × 50 conexiones = 200 conexiones.
- Docker `29.6.2` (Docker Desktop, Windows 11, 24 hilos); servidor con 2 CPU y 1g. Config igual en los dos: `--maxmemory 768mb --maxmemory-policy allkeys-lru --io-threads 1|2`; lo demás de fábrica (instantáneas RDB, sin AOF).
- Datos: 1.000.000 claves (memtier-1 … memtier-1000000) de 100 bytes, escritas por memtier.

## 0 · ¿Llegaron los dos al mismo estado? (antes de medir)

- Redis: DBSIZE 1000000, sha256 de memtier-1 / -500000 / -1000000: ec29dd83f08a… / ec29dd83f08a… / ec29dd83f08a…
- Valkey: DBSIZE 1000000, sha256 de memtier-1 / -500000 / -1000000: ec29dd83f08a… / ec29dd83f08a… / ec29dd83f08a…
- → igual en los dos.

## 1 · Lo que despliegas

| servidor | imagen | tamaño en disco |
|---|---|---|
| Redis | `redis:8.8.4` | 52,1 MiB |
| Valkey | `valkey/valkey:9.1.3` | 43,4 MiB |

## 2 · Arranque, memoria y 1.000.000 claves

Arranque en vacío = `docker run` → primer +PONG (mediana de 5). Recarga = reinicio con el RDB del millón de claves en un volumen → primer +PONG (mientras carga responde -LOADING; mediana de 3). used_memory = lo que dice el propio servidor (INFO memory); contenedor = docker stats.

| servidor | arranque en vacío | reposo (contenedor) | cargar 1 M claves | used_memory con 1 M | por clave | contenedor con 1 M | RDB en disco | recarga del RDB |
|---|---|---|---|---|---|---|---|---|
| Redis | 237 ms | 9,8 MiB | 5,4 s | 159,0 MiB | 165 bytes | 173,7 MiB | 29,5 MiB | 912 ms |
| Valkey | 252 ms | 5,5 MiB | 4,4 s | 160,3 MiB | 167 bytes | 169,8 MiB | 29,5 MiB | 747 ms |

## 3 · A tope: 1 SET por cada 10 GET, sin pipeline — memtier 4×50 conexiones, 30 s tras 5 s de calentamiento, claves al azar entre el millón

| servidor | operaciones/s | p50 | p99 | p99,9 | memoria máx. | CPU media |
|---|---|---|---|---|---|---|
| Redis | 305.213 | 0,615 ms | 1,287 ms | 1,599 ms | 169,7 MiB | 93 % |
| Redis · io-threads 2 | 283.657 | 0,591 ms | 1,471 ms | 2,159 ms | 171,7 MiB | 110 % |
| Valkey | 283.055 | 0,639 ms | 1,503 ms | 2,207 ms | 172,0 MiB | 87 % |
| Valkey · io-threads 2 | 280.596 | 0,687 ms | 1,223 ms | 1,727 ms | 172,7 MiB | 193 % |

## 4 · A tope con pipeline de 16 (1:10) — memtier 4×50 conexiones, 30 s tras 5 s de calentamiento, claves al azar entre el millón

| servidor | operaciones/s | p50 | p99 | p99,9 | memoria máx. | CPU media |
|---|---|---|---|---|---|---|
| Redis | 1.809.856 | 1,655 ms | 3,343 ms | 4,031 ms | 174,7 MiB | 93 % |
| Redis · io-threads 2 | 2.232.632 | 1,487 ms | 2,271 ms | 3,215 ms | 176,3 MiB | 140 % |
| Valkey | 1.766.107 | 1,703 ms | 3,439 ms | 4,031 ms | 171,7 MiB | 87 % |
| Valkey · io-threads 2 | 2.282.617 | 1,359 ms | 2,047 ms | 2,975 ms | 173,1 MiB | 193 % |

## 5 · El mismo tráfico para los dos: 140.200 operaciones/s fijas (la mitad del más lento a tope), 1:10, sin pipeline

| servidor | operaciones/s servidas | p50 | p99 | p99,9 | CPU media |
|---|---|---|---|---|---|
| Redis | 137.967 | 0,615 ms | 1,319 ms | 1,655 ms | 42 % |
| Redis · io-threads 2 | 137.991 | 0,567 ms | 1,351 ms | 1,671 ms | 52 % |
| Valkey | 138.021 | 0,623 ms | 1,343 ms | 1,743 ms | 43 % |
| Valkey · io-threads 2 | 138.007 | 0,663 ms | 1,287 ms | 1,847 ms | 146 % |

