# SALIDA — Docker Compose con PostgreSQL (cultura-devops)

> Corrida del 2026-10-20 16:41. Docker 29.6.2, Docker Compose version v5.3.1, imagen postgres:18.

```
### 1 · El compose de los tutoriales viejos, con postgres:18
$ cat compose-tutorial-viejo.yaml
services:
  db:
    image: postgres:18
    environment:
      POSTGRES_PASSWORD: clave1
    volumes:
      - datos:/var/lib/postgresql/data
volumes:
  datos:
$ docker compose -f compose-tutorial-viejo.yaml up -d
$ docker compose -f compose-tutorial-viejo.yaml ps -a
SERVICE   STATUS
db        Exited (1) 8 seconds ago
$ docker compose -f compose-tutorial-viejo.yaml logs db
Error: in 18+, these Docker images are configured to store database data in a
       format which is compatible with "pg_ctlcluster" (specifically, using
       major-version-specific directory names).  This better reflects how
       PostgreSQL itself works, and how upgrades are to be performed.
       See also https://github.com/docker-library/postgres/pull/1259
       Counter to that, there appears to be PostgreSQL data in:
         /var/lib/postgresql/data (unused mount/volume)
       This is usually the result of upgrading the Docker image without
       upgrading the underlying database using "pg_upgrade" (which requires both
       versions).
       The suggested container configuration for 18+ is to place a single mount
       at /var/lib/postgresql which will then place PostgreSQL data in a
       subdirectory, allowing usage of "pg_upgrade --link" without mount point
       boundary issues.

### 2 · El compose bueno
$ cat compose.yaml
services:
  db:
    image: postgres:18
    environment:
      POSTGRES_USER: tienda
      POSTGRES_PASSWORD: ${CLAVE_DB:-clave1}
      POSTGRES_DB: tienda
    volumes:
      - datos:/var/lib/postgresql
      - ./initdb:/docker-entrypoint-initdb.d:ro
    ports:
      - "127.0.0.1:5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U tienda -d tienda"]
      interval: 2s
      timeout: 3s
      retries: 15
  app:
    image: postgres:18
    depends_on:
      db:
        condition: service_healthy
    environment:
      PGPASSWORD: ${CLAVE_DB:-clave1}
    command: ["psql", "-h", "db", "-U", "tienda", "-d", "tienda", "-c", "SELECT count(*) AS productos FROM productos;"]
volumes:
  datos:
$ cat initdb/01-tablas.sql
CREATE TABLE productos (id serial PRIMARY KEY, nombre text NOT NULL, precio numeric(10,2));
INSERT INTO productos (nombre, precio) VALUES ('teclado', 25.00), ('mouse', 12.50), ('monitor', 180.00);

### 3 · Levantar: la app espera a que la base esté sana
$ docker compose up -d --wait db
$ docker compose ps
SERVICE   STATUS                   PORTS
db        Up 2 seconds (healthy)   127.0.0.1:5433->5432/tcp
$ docker compose run --rm app
 productos 
-----------
         3
(1 row)


### 4 · ¿Los datos sobreviven a down?
$ docker compose exec db psql -U tienda -c "INSERT INTO productos (nombre, precio) VALUES ('audifonos', 40.00);"
INSERT 0 1
$ docker compose down
$ docker compose up -d --wait db && docker compose run --rm app
 productos 
-----------
         4
(1 row)

$ docker volume ls --filter name=demopg
DRIVER    VOLUME NAME
local     demopg_datos

### 5 · Cambiar la clave en el compose NO cambia la clave de la base
$ CLAVE_DB=clave2 docker compose up -d --wait db
$ CLAVE_DB=clave2 docker compose run --rm app
psql: error: connection to server at "db" (192.168.208.2), port 5432 failed: FATAL:  password authentication failed for user "tienda"

$ docker compose exec db psql -U tienda -c "ALTER USER tienda PASSWORD 'clave2';"
ALTER ROLE
$ CLAVE_DB=clave2 docker compose run --rm app
 productos 
-----------
         4
(1 row)


### 6 · Respaldo con pg_dump
$ docker compose exec db pg_dump -U tienda tienda > respaldo.sql
$ grep -A5 'COPY public.productos' respaldo.sql
COPY public.productos (id, nombre, precio) FROM stdin;
1	teclado	25.00
2	mouse	12.50
3	monitor	180.00
4	audifonos	40.00
\.

### 7 · down -v borra el volumen: los datos se van
$ docker compose down -v
$ docker compose up -d --wait db && docker compose run --rm app
 productos 
-----------
         3
(1 row)

$ docker compose exec db psql -U tienda -c "SELECT nombre FROM productos ORDER BY id;"
 nombre  
---------
 teclado
 mouse
 monitor
(3 rows)

```
