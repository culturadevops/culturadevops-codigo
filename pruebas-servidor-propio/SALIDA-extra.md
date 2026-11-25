# SALIDA extra — lo que se pierde entre copias (vídeo 414)

Generado 2026-10-13 22:15 UTC con `python correr_extra.py`. `postgres:17-alpine` en Docker.

### antes de la copia

`$ psql -c 'select count(*), max(id) from pedidos'`

```
10000|10000
```
(código de salida 0)

### la copia de las 03:00

`$ pg_dump -Fc -f copia.dump`

```
copia hecha
```
(código de salida 0)

### durante la mañana entran 25 pedidos más

`$ psql -c 'insert … generate_series(10001,10025)'`

```
INSERT 0 25
10025|10025
```
(código de salida 0)

### el disco se muere

`$ docker rm -f -v pg-a`

```
pg-a
```
(código de salida 0)

### restaurar la copia de las 03:00

`$ pg_restore -d postgres copia.dump; select count(*), max(id)`

```
10000|10000
```
(código de salida 0)

> Los 25 pedidos posteriores a la copia (10001-10025) no están.
