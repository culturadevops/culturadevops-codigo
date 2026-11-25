# SALIDA — Respaldo de Postgres a S3 con Python (cultura-devops, vídeo 798)

> Corrida del 2026-11-05 con `bash correr.sh` (Git Bash). Postgres 18.6 (postgres:18.6-alpine, origen y destino), moto 5.2.6.dev
> como S3 (emulador: NO es AWS), Python 3.14.10 + boto3 1.43.124 (s3transfer 0.19.3). Todos los contenedores con `--rm --cpus 1`.
> Datos: semilla.sql (50.000 clientes, 2.000.000 de pedidos; en el paso 5, 4.000.000). Código: respaldo.py.
> «memoria pico» = ru_maxrss del proceso de Python (pg_dump es otro proceso y no cuenta).
> ⛔ SIN CRONÓMETRO a propósito: la máquina estaba ocupada con otro banco (candado _logs/banco.lock), así que no se dan tiempos.
> Tamaño del objeto de 3b (pg_dump cortado a los 2 s) depende del momento del corte: 35.8, 36.1 y 38.3 MB en tres corridas.
> La suma de pedidos del paso 5-6 cambia entre corridas (el INSERT del paso 5 usa random() sin semilla); dentro de una corrida, igual.
>
> Hallazgo de la 1.ª corrida (evidencia/corrida1-gzip-truncado.txt): el modo z0+gzip devolvía en read(n) lo que zlib soltara
> (menos de n bytes). s3transfer 0.19.3, con un flujo sin tamaño, lee el umbral (8 MB) y si recibe menos «da el archivo por
> terminado» (upload.py, líneas 405-407: `if len(self._initial_data) < threshold: return False`) → un solo put_object de 7,3 MB
> y «ok». Ese comportamiento se conserva como modo `z0+gzip-corto` para enseñarlo; el modo `z0+gzip` ya devuelve n bytes.

```
== versiones
pg_dump (PostgreSQL) 18.6
psql (PostgreSQL) 18.6
Python 3.14.10
boto3 1.43.124
moto 5.2.6.dev
contenedores con --cpus 1

== datos de origen (semilla.sql)
clientes 50000 · pedidos 2000000 · tamaño de la base tienda: 311 MB

$ respaldo bucket
ok  bucket respaldos-demo
(código de salida: 0)

== 1. streaming: pg_dump -Fc directo a S3 por partes (y la variante sin compresión de pg_dump + gzip en Python)

$ respaldo respaldar --fecha 2026-11-05T0300 --modo fc
ok  respaldos/tienda/2026-11-05T0300.dump
    pg_dump 105.1 MB · subido 105.1 MB · partes 13 · memoria pico 59 MB
(código de salida: 0)

$ respaldo respaldar --fecha 2026-11-05T0301 --modo z0+gzip
ok  respaldos/tienda/2026-11-05T0301.dump.gz
    pg_dump 228.2 MB · subido 106.2 MB · partes 13 · memoria pico 72 MB
(código de salida: 0)

$ respaldo respaldar --fecha 2026-11-05T0304 --modo z0+gzip-corto
ok  respaldos/tienda/2026-11-05T0304.dump.gz
    pg_dump 16.8 MB · subido 7.3 MB · partes 1 · memoria pico 67 MB
(código de salida: 0)

$ respaldo restaurar --clave respaldos/tienda/2026-11-05T0304.dump.gz
ERROR: pg_restore salió con código 1: pg_restore: error: could not read from input file: end of file
(código de salida: 1)

== 2. el ingenuo: todo el pg_dump a memoria y después put_object

$ respaldo ingenuo --fecha 2026-11-05T0302
ok  respaldos/tienda/2026-11-05T0302.dump
    pg_dump 105.1 MB · subido de una vez · memoria pico 255 MB
(código de salida: 0)

== 3a. pg_dump falla al empezar (la base no existe)

$ respaldo sin-wait --base no_existe --fecha 2026-11-05T0400
ok  respaldos/no_existe/2026-11-05T0400.dump  (el script terminó con código 0)
(código de salida: 0)

$ respaldo respaldar --base no_existe --fecha 2026-11-05T0401
ERROR: subida abortada: pg_dump salió con código 1: pg_dump: error: connection to server at "cd798-origen" (192.168.208.2), port 5432 failed: FATAL:  database "no_existe" does not exist
(código de salida: 1)

$ respaldo listar --base no_existe
    respaldos/no_existe/2026-11-05T0400.dump           0 KB
    1 respaldos
    subidas por partes a medias: 0
(código de salida: 0)

== 3b. pg_dump muere a la mitad (se corta su conexión a los 2 s)

$ (sleep 2; psql -qAt -d tienda -c "SELECT count(pg_terminate_backend(pid)) || ' conexión de pg_dump cortada' FROM pg_stat_activity WHERE application_name = 'pg_dump'") & respaldo sin-wait --fecha 2026-11-05T0402; rc=$?; wait; exit $rc
1 conexión de pg_dump cortada
ok  respaldos/tienda/2026-11-05T0402.dump  (el script terminó con código 0)
(código de salida: 0)

$ (sleep 2; psql -qAt -d tienda -c "SELECT count(pg_terminate_backend(pid)) || ' conexión de pg_dump cortada' FROM pg_stat_activity WHERE application_name = 'pg_dump'") & respaldo respaldar --fecha 2026-11-05T0403; rc=$?; wait; exit $rc
1 conexión de pg_dump cortada
ERROR: subida abortada: pg_dump salió con código 1: pg_dump: error: Dumping the contents of table "pedidos" failed: PQgetCopyData() failed.
pg_dump: detail: Error message from server: server closed the connection unexpectedly
	This probably means the server terminated abnormally
	before or while processing the request.
pg_dump: detail: Command was: COPY public.pedidos (id, cliente_id, monto, creado, nota) TO stdout;
(código de salida: 1)

$ respaldo listar
    respaldos/tienda/2026-11-05T0402.dump           38.3 MB
    respaldos/tienda/2026-11-05T0304.dump.gz         7.3 MB
    respaldos/tienda/2026-11-05T0302.dump          105.1 MB
    respaldos/tienda/2026-11-05T0301.dump.gz       106.2 MB
    respaldos/tienda/2026-11-05T0300.dump          105.1 MB
    5 respaldos
    subidas por partes a medias: 0
(código de salida: 0)

$ respaldo restaurar --clave respaldos/tienda/2026-11-05T0402.dump
ERROR: pg_restore salió con código 1: pg_restore: error: could not read from input file: end of file
(código de salida: 1)

== 4. retención: 12 respaldos de inventario repartidos en 10 días

$ respaldo listar --base inventario
    respaldos/inventario/2026-11-05T1500.dump         27 KB
    respaldos/inventario/2026-11-05T0300.dump         27 KB
    respaldos/inventario/2026-11-04T0300.dump         27 KB
    respaldos/inventario/2026-11-03T0300.dump         27 KB
    respaldos/inventario/2026-11-02T1500.dump         27 KB
    respaldos/inventario/2026-11-02T0300.dump         27 KB
    respaldos/inventario/2026-11-01T0300.dump         27 KB
    respaldos/inventario/2026-10-31T0300.dump         27 KB
    respaldos/inventario/2026-10-30T0300.dump         27 KB
    respaldos/inventario/2026-10-29T0300.dump         27 KB
    respaldos/inventario/2026-10-28T0300.dump         27 KB
    respaldos/inventario/2026-10-27T0300.dump         27 KB
    12 respaldos
    subidas por partes a medias: 0
(código de salida: 0)

$ respaldo retener --base inventario --ultimos 3 --dias 7
    queda   inventario/2026-11-05T1500.dump      (entre los 3 más nuevos)
    queda   inventario/2026-11-05T0300.dump      (entre los 3 más nuevos)
    queda   inventario/2026-11-04T0300.dump      (entre los 3 más nuevos)
    queda   inventario/2026-11-03T0300.dump      (el último del 2026-11-03)
    queda   inventario/2026-11-02T1500.dump      (el último del 2026-11-02)
    BORRA   inventario/2026-11-02T0300.dump
    queda   inventario/2026-11-01T0300.dump      (el último del 2026-11-01)
    queda   inventario/2026-10-31T0300.dump      (el último del 2026-10-31)
    queda   inventario/2026-10-30T0300.dump      (el último del 2026-10-30)
    BORRA   inventario/2026-10-29T0300.dump
    BORRA   inventario/2026-10-28T0300.dump
    BORRA   inventario/2026-10-27T0300.dump
    quedan 8 · se borran 4
    (ensayo: no se borró nada; usa --borrar)
(código de salida: 0)

$ respaldo retener --base inventario --ultimos 3 --dias 7 --borrar
    queda   inventario/2026-11-05T1500.dump      (entre los 3 más nuevos)
    queda   inventario/2026-11-05T0300.dump      (entre los 3 más nuevos)
    queda   inventario/2026-11-04T0300.dump      (entre los 3 más nuevos)
    queda   inventario/2026-11-03T0300.dump      (el último del 2026-11-03)
    queda   inventario/2026-11-02T1500.dump      (el último del 2026-11-02)
    BORRA   inventario/2026-11-02T0300.dump
    queda   inventario/2026-11-01T0300.dump      (el último del 2026-11-01)
    queda   inventario/2026-10-31T0300.dump      (el último del 2026-10-31)
    queda   inventario/2026-10-30T0300.dump      (el último del 2026-10-30)
    BORRA   inventario/2026-10-29T0300.dump
    BORRA   inventario/2026-10-28T0300.dump
    BORRA   inventario/2026-10-27T0300.dump
    quedan 8 · se borran 4
    borrados 4 · errores 0
(código de salida: 0)

$ respaldo listar --base inventario
    respaldos/inventario/2026-11-05T1500.dump         27 KB
    respaldos/inventario/2026-11-05T0300.dump         27 KB
    respaldos/inventario/2026-11-04T0300.dump         27 KB
    respaldos/inventario/2026-11-03T0300.dump         27 KB
    respaldos/inventario/2026-11-02T1500.dump         27 KB
    respaldos/inventario/2026-11-01T0300.dump         27 KB
    respaldos/inventario/2026-10-31T0300.dump         27 KB
    respaldos/inventario/2026-10-30T0300.dump         27 KB
    8 respaldos
    subidas por partes a medias: 0
(código de salida: 0)

== 5. el doble de datos: memoria con streaming y con el ingenuo
pedidos: 4000000 · tamaño de la base: 610 MB

$ respaldo respaldar --fecha 2026-11-05T0500 --modo fc
ok  respaldos/tienda/2026-11-05T0500.dump
    pg_dump 210.0 MB · subido 210.0 MB · partes 26 · memoria pico 59 MB
(código de salida: 0)

$ respaldo respaldar --fecha 2026-11-05T0501 --modo z0+gzip
ok  respaldos/tienda/2026-11-05T0501.dump.gz
    pg_dump 455.3 MB · subido 212.1 MB · partes 26 · memoria pico 72 MB
(código de salida: 0)

$ respaldo ingenuo --fecha 2026-11-05T0502
ok  respaldos/tienda/2026-11-05T0502.dump
    pg_dump 210.0 MB · subido de una vez · memoria pico 464 MB
(código de salida: 0)

== 6. el respaldo solo vale si restaura: a una base nueva, y se compara

$ respaldo restaurar --clave respaldos/tienda/2026-11-05T0500.dump
ok  restaurado respaldos/tienda/2026-11-05T0500.dump en cd798-destino/tienda_restaurada · memoria pico 64 MB
(código de salida: 0)

$ respaldo verificar
    tabla     origen (filas · suma)           restaurada                      
    clientes  50000 · 1250025000              50000 · 1250025000              igual
    pedidos   4000000 · 999981882.24          4000000 · 999981882.24          igual
ok  el respaldo restaura y coincide
(código de salida: 0)

$ respaldo restaurar --clave respaldos/tienda/2026-11-05T0501.dump.gz
ok  restaurado respaldos/tienda/2026-11-05T0501.dump.gz en cd798-destino/tienda_restaurada · memoria pico 93 MB
(código de salida: 0)

$ respaldo verificar
    tabla     origen (filas · suma)           restaurada                      
    clientes  50000 · 1250025000              50000 · 1250025000              igual
    pedidos   4000000 · 999981882.24          4000000 · 999981882.24          igual
ok  el respaldo restaura y coincide
(código de salida: 0)

== limpieza: contenedores y red cd798-* borrados
```

## Anexo · versión de pg_dump (corrida aparte, 2026-11-05: postgres:16-alpine contra el servidor postgres:18.6-alpine, --rm --cpus 1)

```
$ pg_dump --version; pg_dump -Fc -d postgres > /dev/null   # pg_dump 16 contra Postgres 18
pg_dump (PostgreSQL) 16.15
pg_dump: error: aborting because of server version mismatch
pg_dump: detail: server version: 18.6; pg_dump version: 16.15
(código de salida: 1)
```
