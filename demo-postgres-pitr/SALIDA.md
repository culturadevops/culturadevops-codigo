# SALIDA — Postgres: vuelve al segundo antes del desastre (cultura-devops)

> Corrida del 2026-10-20 12:37 en postgres:18 (un solo contenedor: servidor, archivo de WAL y copia base).

```
postgres (PostgreSQL) 18.6 (Debian 18.6-1.pgdg13+2)
### 1 · Un Postgres que guarda su WAL
$ psql -c 'SHOW archive_command'
cp %p /tmp/archivo/%f
$ psql -c 'SELECT count(*) FROM pedidos'
1000

### 2 · La copia base
$ pg_basebackup -D /tmp/base -X stream            # por defecto: espera un checkpoint «suave»
real 98.13
$ pg_basebackup -D /tmp/base -X stream -c fast    # pide el checkpoint ya
real 1.16
$ du -sh /tmp/base
47M

### 3 · Se sigue trabajando después de la copia
$ psql -c 'SELECT count(*) FROM pedidos'
1500
$ psql -c 'SELECT now()'   # la hora buena, la que vamos a recuperar
2026-10-20 17:39:10+00

### 4 · El desastre
$ psql -c 'DELETE FROM pedidos'   # sin WHERE
DELETE 1500
$ psql -c 'SELECT count(*) FROM pedidos'
0
$ ls /tmp/archivo | wc -l   # segmentos de WAL archivados
6

### 5 · Volver al segundo antes del DELETE
$ cat recovery (lo que añado a postgresql.conf)
restore_command = 'cp /tmp/archivo/%f %p'
recovery_target_time = '2026-10-20 17:39:10+00'
recovery_target_action = 'promote'
$ touch recovery.signal && pg_ctl start
$ grep -E 'starting point-in-time|recovery stopping|archive recovery complete' postgresql.log
LOG:  starting point-in-time recovery to 2026-10-20 17:39:10+00
LOG:  recovery stopping before commit of transaction 768, time 2026-10-20 17:39:11.550129+00
LOG:  archive recovery complete
$ psql -c 'SELECT count(*), max(creado) FROM pedidos'
1500|2026-10-20 17:39:08+00
```
