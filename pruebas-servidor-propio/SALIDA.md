# SALIDA — servidor propio: copia y restauración (vídeo 414)

Generado 2026-10-13 22:04 UTC con `python correr.py`. `postgres:17-alpine` en Docker.

## 1 · La base de datos

### versión

`$ psql -c 'select version()'`

```
PostgreSQL 17.11 on x86_64-pc-linux-musl
```
(código de salida 0)

### 10.000 pedidos

`$ psql -c 'create table pedidos …; insert … generate_series(1,10000)'`

```
CREATE TABLE
INSERT 0 10000
```
(código de salida 0)

### contarlos y sumarlos

`$ psql -c 'select count(*), sum(total) from pedidos'`

```
10000|500400.03
```
(código de salida 0)

## 2 · La copia

### pg_dump

`$ pg_dump -Fc -f copia.dump`

```
58801 bytes
0.2 s
```
(código de salida 0)

### sacarla del servidor

`$ docker cp pg-prod:/tmp/copia.dump copias/`

```
58801 bytes en copias/
```

## 3 · El disco se muere

### borrar el servidor y su disco

`$ docker rm -f -v pg-prod; docker volume rm datos-prod`

```
datos-prod
```
(código de salida 0)

### ¿queda algo?

`$ docker volume ls | grep datos-prod`

```
(nada)
```
(código de salida 0)

## 4 · Restaurar

### servidor nuevo + pg_restore + contar y sumar

`$ docker run postgres; pg_restore -d postgres copia.dump; select count(*), sum(total)`

```
10000|500400.03
1.5 s desde cero
```
(código de salida 0)

> Mismos pedidos y misma suma que antes de borrar el disco.
