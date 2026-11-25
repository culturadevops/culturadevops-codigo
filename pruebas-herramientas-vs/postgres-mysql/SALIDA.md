# SALIDA — ¿Postgres o MySQL? (cultura-devops, serie «¿X o Y? Lo medí» de herramientas)

> Corrida del 2026-11-05 13:11, bajo el candado _logs/banco.lock. Regenerable con `python correr.py`. ⛔ Ninguna cifra de blog: todo salió de aquí.

- PostgreSQL: `postgres (PostgreSQL) 18.6 (Debian 18.6-1.pgdg13+2)` — imagen oficial `postgres:18.6`
- MySQL: `/usr/sbin/mysqld  Ver 9.7.4 for Linux on x86_64 (MySQL Community Server - GPL)` — imagen oficial `mysql:9.7.4`
- Carga: `sysbench 1.0.20` (Ubuntu 24.04) desde otro contenedor con 4 CPU.
- Docker `29.6.2` (Docker Desktop, Windows 11, 24 hilos); base con 2 CPU y 1g; datos en un volumen de Docker (disco de la VM de WSL2, el mismo para las dos).
- Config: PostgreSQL `shared_buffers=256MB effective_cache_size=512MB max_connections=100`; MySQL `innodb_buffer_pool_size=256M max_connections=100 tls-version=(vacío)`. Lo demás, de fábrica (commit con fsync en las dos; MySQL con binlog). Sin TLS en ninguna de las dos.
- Datos: 8 tablas × 100.000 filas generadas UNA vez por sysbench (--rand-seed=1) y exportadas a CSV (800.000 líneas, 147,9 MiB); las dos bases cargan ESE archivo.

## 1 · Lo que despliegas

| base | imagen | tamaño en disco |
|---|---|---|
| PostgreSQL | `postgres:18.6` | 155,0 MiB |
| MySQL | `mysql:9.7.4` | 257,8 MiB |

## 0 · ¿Tienen los mismos datos? (después de cargar, antes de medir)

Por tabla: filas · suma de k · largo total de c · largo total de pad · filas id=1 e id=100000 (id, k, c). Referencia = la misma cuenta hecha con awk sobre el CSV; cada base se comprobó contra ella justo después de cargar y ANTES de medir.

- sbtest1: CSV = PostgreSQL = MySQL → igual — `100000 5008374207 11900000 5900000 · 1 49768 79508438332-61656118404-79657002870-11740857577-5195848…`
- sbtest2: CSV = PostgreSQL = MySQL → igual — `100000 5009560370 11900000 5900000 · 1 46370 42484586481-60567556211-15269499673-65107817658-2885531…`
- sbtest3: CSV = PostgreSQL = MySQL → igual — `100000 5007951332 11900000 5900000 · 1 50140 44261238614-65888869614-76783298342-04101746556-7119538…`
- sbtest4: CSV = PostgreSQL = MySQL → igual — `100000 5009066902 11900000 5900000 · 1 50287 55019788973-00426798618-14003242882-67950824410-6802179…`
- sbtest5: CSV = PostgreSQL = MySQL → igual — `100000 5008575293 11900000 5900000 · 1 40763 43156988772-42136087076-03400233886-53058702483-6702130…`
- sbtest6: CSV = PostgreSQL = MySQL → igual — `100000 5012646810 11900000 5900000 · 1 50355 51509289794-66570425367-55109332262-46524541086-2461510…`
- sbtest7: CSV = PostgreSQL = MySQL → igual — `100000 5009669910 11900000 5900000 · 1 50019 40894602593-99824349040-79801582745-38495192856-2612244…`
- sbtest8: CSV = PostgreSQL = MySQL → igual — `100000 5009532749 11900000 5900000 · 1 50302 49055279098-70757710665-22621442355-91712538665-0256689…`

TLS: MySQL `Ssl_accepts` al terminar = 0; PostgreSQL, conexiones con TLS = 0 de 1. Las dos van en claro.

## 2 · Arranque, carga del CSV, disco y memoria en reposo

Arranque = `docker run` hasta que la base acepta conexiones TCP (sonda con `docker exec`, resolución ~0,1 s; mediana de 3). «Primera vez» incluye crear la base vacía (initdb / --initialize). Carga = las 8 tablas desde el CSV, una tras otra, con el índice en k ya creado.

| base | primera vez (volumen vacío) | reinicio con datos | parada limpia | cargar 800.000 filas | tablas + índices | carpeta de datos | memoria en reposo |
|---|---|---|---|---|---|---|---|
| PostgreSQL | 0,9 s | 0,3 s | 0,2 s | 4,2 s | 197,5 MiB | 500,0 MiB (WAL 272,0 MiB) | 44,9 MiB |
| MySQL | 5,8 s | 1,3 s | 1,6 s | 6,3 s | 192,5 MiB | 609,8 MiB (binlog 148,4 MiB) | 448,1 MiB |

## 3 · Carga OLTP (sysbench, 30 s tras 10 s de calentamiento)

Memoria = máximo de `docker stats` durante la carga (con 1 GiB de límite); CPU = media (200 % = las 2 CPU llenas). p50 sale del histograma de sysbench; p99, de su percentil. «Errores» = los que sysbench ignora y reintenta (choques entre transacciones).

### oltp_point_select · 16 hilos — Lecturas por clave (SELECT … WHERE id = ?)

| base | transacciones/s | consultas/s | p50 | p99 | memoria máx. | CPU media | errores |
|---|---|---|---|---|---|---|---|
| PostgreSQL | 50.069 | 50.069 | 0,07 ms | 0,46 ms | 319,9 MiB | 192 % | 0 |
| MySQL | 40.163 | 40.163 | 0,08 ms | 0,63 ms | 745,9 MiB | 188 % | 0 |

### oltp_read_only · 8 hilos — Solo lectura: 14 consultas por transacción (claves, rangos, SUM, ORDER BY, DISTINCT)

| base | transacciones/s | consultas/s | p50 | p99 | memoria máx. | CPU media | errores |
|---|---|---|---|---|---|---|---|
| PostgreSQL | 3.391 | 54.249 | 1,08 ms | 52,89 ms | 309,0 MiB | 190 % | 0 |
| MySQL | 3.173 | 50.762 | 1,14 ms | 52,89 ms | 756,9 MiB | 190 % | 0 |

### oltp_read_write · 8 hilos — Lectura y escritura: las de arriba + 2 UPDATE, 1 DELETE y 1 INSERT por transacción, con COMMIT

| base | transacciones/s | consultas/s | p50 | p99 | memoria máx. | CPU media | errores |
|---|---|---|---|---|---|---|---|
| PostgreSQL | 2.523 | 50.477 | 2,26 ms | 30,26 ms | 339,7 MiB | 189 % | 14 |
| MySQL | 1.707 | 34.133 | 4,49 ms | 8,28 ms | 770,3 MiB | 153 % | 0 |

