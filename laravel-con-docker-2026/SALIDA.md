# SALIDA — Laravel con Docker en 2026 (cultura-devops 697)

Generado por `python ejecutar_todo.py` el 2026-10-29 08:20 (hora local) · 424 s en total · 2 repeticiones por medida. Cada bloque es el comando tal cual y su salida real (las líneas largas, recortadas con «…»).

## Resumen medido

| medida | multietapa | gorda |
|---|---|---|
| tamaño en disco (`docker image ls`) | 207MB | 1.8GB |
| tamaño comprimido (lo que se sube/baja) | 44.1 MB | 415.4 MB |
| build sin caché | 14.9 s / 13.9 s | 72.2 s / 72.8 s |
| build con caché, sin cambios | 1.3 s | 0.7 s |
| build con caché, 1 línea cambiada | 4.0 s / 3.9 s | 10.2 s / 10.0 s |

- nginx (v697-web:multi): 92.5MB en disco, 26.0 MB comprimido.
- Primera respuesta 200 en frío (volumen nuevo): 7.5 s / 9.5 s / 7.5 s; en tibio: 3.3 s / 3.4 s / 3.3 s.
- Trampa del healthcheck: {'app_murio_s': 0.7594947000034153, 'db_sana_s': 8.629010900040157}.


## 0 · Versiones

- laravel/laravel (esqueleto) 13.11.0 · laravel/framework **v13.39.0** (de app/composer.lock)

```
$ docker version --format 'Docker {{.Server.Version}}'
Docker 29.6.2
# exit=0 · 0.1 s
```

```
$ docker compose version
Docker Compose version v5.3.1
# exit=0 · 0.1 s
```

```
$ docker run --rm php:8.5-fpm-alpine php -r 'echo PHP_VERSION, PHP_EOL;'
8.5.12
# exit=0 · 0.4 s
```

```
$ docker run --rm composer:2 composer --version
Composer version 2.10.3 2026-08-27 13:34:23
PHP version 8.5.12 (/usr/local/bin/php)
# exit=0 · 0.4 s
```

```
$ docker run --rm mysql:8.4 mysqld --version
/usr/sbin/mysqld  Ver 8.4.13 for Linux on x86_64 (MySQL Community Server - GPL)
# exit=0 · 0.3 s
```

```
$ docker run --rm --entrypoint sh mysql:8.4 -c "grep -n 'skip-networking' /usr/local/bin/docker-entrypoint.sh"
124:	if ! "$@" --daemonize --skip-networking --default-time-zone=SYSTEM --socket="${SOCKET}"; then
# exit=0 · 0.3 s
```

```
$ docker run --rm nginx:1.28-alpine nginx -v
nginx version: nginx/1.28.3
# exit=0 · 0.3 s
```

```
$ docker info --format 'CPUs {{.NCPU}} · RAM {{.MemTotal}} B · {{.OperatingSystem}}'
CPUs 24 · RAM 16487473152 B · Docker Desktop
# exit=0 · 0.5 s
```


## 1 · Builds: sin caché y con caché

Las imágenes base ya estaban descargadas: `--no-cache` mide construir las capas, no bajar las bases. composer sí descarga paquetes de Internet en cada build sin caché, así que esos tiempos dependen de la red.

```
$ docker build --no-cache -f docker/Dockerfile --target runtime -t v697-app:multi .
#22 unpacking to docker.io/library/v697-app:multi 0.4s done
#22 DONE 1.1s
# exit=0 · 14.9 s
```

```
$ docker build --no-cache -f docker/Dockerfile --target runtime -t v697-app:multi .
#22 unpacking to docker.io/library/v697-app:multi 0.4s done
#22 DONE 1.1s
# exit=0 · 13.9 s
```

```
$ docker build --no-cache -f docker/Dockerfile.gorda --target runtime -t v697-app:gorda .
#16 unpacking to docker.io/library/v697-app:gorda 3.4s done
#16 DONE 15.2s
# exit=0 · 72.2 s
```

```
$ docker build --no-cache -f docker/Dockerfile.gorda --target runtime -t v697-app:gorda .
#16 unpacking to docker.io/library/v697-app:gorda 3.4s done
#16 DONE 15.4s
# exit=0 · 72.8 s
```

```
$ docker build -f docker/Dockerfile --target web -t v697-web:multi .
#17 unpacking to docker.io/library/v697-web:multi 0.0s done
#17 DONE 0.1s
# exit=0 · 2.6 s
```

```
$ docker build -f docker/Dockerfile --target sin-permisos -t v697-app:sin-permisos .
#21 unpacking to docker.io/library/v697-app:sin-permisos 0.0s done
#21 DONE 0.1s
# exit=0 · 1.5 s
```


### Con caché y sin tocar nada


```
$ docker build -f docker/Dockerfile --target runtime -t v697-app:multi .
#22 unpacking to docker.io/library/v697-app:multi 0.0s done
#22 DONE 0.1s
# exit=0 · 1.3 s
```

```
$ docker build -f docker/Dockerfile.gorda --target runtime -t v697-app:gorda .
#16 unpacking to docker.io/library/v697-app:gorda 0.0s done
#16 DONE 0.1s
# exit=0 · 0.7 s
```


### Con caché, tras cambiar UNA línea de routes/web.php


```
$ docker build -f docker/Dockerfile --target runtime -t v697-app:multi .
#22 unpacking to docker.io/library/v697-app:multi 0.4s done
#22 DONE 1.1s
# exit=0 · 4.0 s
```

```
$ docker build -f docker/Dockerfile --target runtime -t v697-app:multi .
#22 unpacking to docker.io/library/v697-app:multi 0.4s done
#22 DONE 1.0s
# exit=0 · 3.9 s
```

```
$ docker build -f docker/Dockerfile.gorda --target runtime -t v697-app:gorda .
#16 unpacking to docker.io/library/v697-app:gorda 0.6s done
#16 DONE 2.0s
# exit=0 · 10.2 s
```

```
$ docker build -f docker/Dockerfile.gorda --target runtime -t v697-app:gorda .
#16 unpacking to docker.io/library/v697-app:gorda 0.6s done
#16 DONE 2.0s
# exit=0 · 10.0 s
```

```
$ docker build -f docker/Dockerfile --target web -t v697-web:multi .
#17 unpacking to docker.io/library/v697-web:multi done
#17 DONE 0.1s
# exit=0 · 2.2 s
```

```
$ docker build -f docker/Dockerfile --target sin-permisos -t v697-app:sin-permisos .
#21 unpacking to docker.io/library/v697-app:sin-permisos 0.4s done
#21 DONE 1.0s
# exit=0 · 2.8 s
```

En la gorda, `COPY . .` va ANTES de `composer install`: cambiar una línea de código invalida la capa de composer y reinstala todo. En la multietapa, composer.json y composer.lock se copian primero y `composer install` sale de la caché.


## 2 · Tamaños

```
$ docker image ls v697-*
REPOSITORY:TAG          SIZE
v697-app:sin-permisos   206MB
v697-app:gorda          1.8GB
v697-app:multi          207MB
v697-web:multi          92.5MB
# exit=0 · 0.1 s
```

```
$ docker image ls (bases)
REPOSITORY:TAG                         SIZE
php:8.5-fpm                            731MB
mysql:8.4                              1.12GB
composer:2                             316MB
php:8.5-fpm-alpine                     151MB
nginx:1.28-alpine                      93.4MB
# exit=0 · 0.1 s
```

`docker image ls` (almacén containerd de Docker Desktop) da el tamaño en disco y el comprimido (lo que se sube y se baja). Abajo, el comprimido exacto en bytes:

```
$ docker image inspect --format '{{.Size}}' v697-app:multi
44121743
# exit=0 · 0.1 s
```

```
$ docker image inspect --format '{{.Size}}' v697-app:gorda
415403831
# exit=0 · 0.1 s
```

```
$ docker image inspect --format '{{.Size}}' v697-web:multi
25968052
# exit=0 · 0.1 s
```

```
$ docker image inspect --format '{{.Size}}' php:8.5-fpm-alpine
38893314
# exit=0 · 0.1 s
```

```
$ docker image inspect --format '{{.Size}}' php:8.5-fpm
177760167
# exit=0 · 0.1 s
```


### Qué hay dentro de cada una


```
$ docker run --rm --entrypoint sh v697-app:multi -c 'du -sh vendor; …; command -v composer git node npm gcc'
47.3M	vendor
27 carpetas en vendor
composer: no
git: no
node: no
npm: no
gcc: no
# exit=0 · 0.4 s
```

```
$ docker run --rm --entrypoint sh v697-app:gorda -c 'du -sh vendor; …; command -v composer git node npm gcc'
75M	vendor
37 carpetas en vendor
composer: sí
git: sí
node: sí
npm: sí
gcc: sí
# exit=0 · 0.3 s
```


## 3 · La versión buena y el tiempo hasta la primera respuesta

```
$ docker compose up -d
 Container v697-laravel-db-1 Starting 
 Container v697-laravel-db-1 Started 
 Container v697-laravel-db-1 Waiting 
 Container v697-laravel-db-1 Healthy 
 Container v697-laravel-app-1 Starting 
 Container v697-laravel-app-1 Started 
 Container v697-laravel-web-1 Starting 
 Container v697-laravel-web-1 Started
# exit=0 · 7.2 s
```

**`up -d` volvió a los 7.2 s** (espera a que MySQL esté sano) · **primera respuesta 200 a los 7.5 s** desde el `up`.

```
$ docker compose ps
NAME                 IMAGE            COMMAND                  SERVICE   CREATED         STATUS                   PORTS
v697-laravel-app-1   v697-app:multi   "entrypoint php-fpm"     app       7 seconds ago   Up Less than a second    9000/tcp
v697-laravel-db-1    mysql:8.4        "docker-entrypoint.s…"   db        7 seconds ago   Up 7 seconds (healthy)   3306/tcp, 33060/tcp
v697-laravel-web-1   v697-web:multi   "/docker-entrypoint.…"   web       7 seconds ago   Up Less than a second    0.0.0.0:8697->80/tcp, [::]:8697->80/tcp
# exit=0 · 0.1 s
```

```
$ curl -s -o /dev/null -w "%{http_code}\n" localhost:8697/
200
# exit=0 · 0.0 s
```

```
$ docker compose logs app
app-1  |    INFO  Preparing database.  
app-1  |   Creating migration table ...................................... 15.66ms DONE
app-1  |    INFO  Running migrations.  
app-1  |   0001_01_01_000000_create_users_table .......................... 82.97ms DONE
app-1  |   0001_01_01_000001_create_cache_table .......................... 50.22ms DONE
app-1  |   0001_01_01_000002_create_jobs_table ........................... 79.60ms DONE
app-1  | [29-Oct-2026 13:17:12] NOTICE: ready to handle connections
app-1  | 192.168.192.4 -  29/Oct/2026:13:17:12 +0000 "GET /index.php" 200
app-1  | 192.168.192.4 -  29/Oct/2026:13:17:12 +0000 "GET /index.php" 200
# exit=0 · 0.1 s
```

```
$ docker compose exec app php artisan migrate:status

  Migration name .............................................. Batch / Status  
  0001_01_01_000000_create_users_table ............................... [1] Ran  
  0001_01_01_000001_create_cache_table ............................... [1] Ran  
  0001_01_01_000002_create_jobs_table ................................ [1] Ran
# exit=0 · 0.2 s
```

```
$ docker compose exec app php artisan --version
Laravel Framework 13.39.0
# exit=0 · 0.2 s
```

```
$ docker compose exec app sh -c "ps -o user,args | grep php-fpm"
root     php-fpm: master process (/usr/local/etc/php-fpm.conf)
www-data php-fpm: pool www
www-data php-fpm: pool www
# exit=0 · 0.2 s
```

```
$ docker compose down -v
 Volume v697-laravel_dbdata Removing 
 Volume v697-laravel_dbdata Removed 
 Network v697-laravel_default Removed
# exit=0 · 2.5 s
```


| ronda | `up -d` (frío) | 1.ª respuesta 200 (frío, volumen nuevo) | 1.ª respuesta 200 (tibio, volumen existente) |
|---|---|---|---|
| 1 | 7.2 s | 7.5 s | 3.3 s |
| 2 | 9.1 s | 9.5 s | 3.4 s |
| 3 | 7.1 s | 7.5 s | 3.3 s |


(`cpus: "2"` en app y db; el tiempo cuenta desde que se lanza `docker compose up -d`.)


## 4 · Trampa 1: DB_HOST=127.0.0.1 en el .env

```
$ grep DB_HOST docker/app.env.trampa-127
DB_HOST=127.0.0.1
# exit=0 · 0.0 s
```

```
$ APP_ENV_FILE=docker/app.env.trampa-127 MIGRAR=0 docker compose up -d
 Container v697-laravel-db-1 Waiting 
 Container v697-laravel-db-1 Healthy 
 Container v697-laravel-app-1 Starting 
 Container v697-laravel-app-1 Started 
 Container v697-laravel-web-1 Starting 
 Container v697-laravel-web-1 Started
# exit=0 · 9.2 s
```

```
$ docker compose ps
NAME                 IMAGE            COMMAND                  SERVICE   CREATED          STATUS                    PORTS
v697-laravel-app-1   v697-app:multi   "entrypoint php-fpm"     app       17 seconds ago   Up 8 seconds              9000/tcp
v697-laravel-db-1    mysql:8.4        "docker-entrypoint.s…"   db        17 seconds ago   Up 17 seconds (healthy)   3306/tcp, 33060/tcp
v697-laravel-web-1   v697-web:multi   "/docker-entrypoint.…"   web       17 seconds ago   Up 8 seconds              0.0.0.0:8697->80/tcp, [::]:8697->80/tcp
# exit=0 · 0.1 s
```

```
$ curl -s -o /dev/null -w "%{http_code}\n" localhost:8697/
500
# exit=0 · 0.0 s
```

```
$ docker compose logs app | grep SQLSTATE
app-1  | [2026-10-29 13:18:44] production.ERROR: SQLSTATE[HY000] [2002] Connection refused (Connection: mysql, Host: 127.0.0.1, Port: 3306, Database: laravel, SQL: select * from `sessions` where `id` = MMLAD3jjZ8odx4SHvyerj3mgTum4eyjGv5nOcA …
app-1  | [previous exception] [object] (PDOException(code: 2002): SQLSTATE[HY000] [2002] Connection refused at /var/www/html/vendor/laravel/framework/src/Illuminate/Database/Connectors/Connector.php:67)
# exit=0 · 0.1 s
```

```
$ docker compose exec app php -r "echo gethostbyname('db'), PHP_EOL;"
192.168.192.2
# exit=0 · 0.2 s
```

```
$ docker compose exec app php artisan migrate --force
[2026-10-29 13:18:45] production.ERROR: SQLSTATE[HY000] [2002] Connection refused (Connection: mysql, Host: 127.0.0.1, Port: 3306, Database: laravel, SQL: select exists (select 1 from information_schema.tables where table_schema = schema()  …
[previous exception] [object] (PDOException(code: 2002): SQLSTATE[HY000] [2002] Connection refused at /var/www/html/vendor/laravel/framework/src/Illuminate/Database/Connectors/Connector.php:67)
# exit=1 · 0.2 s
```

```
$ docker compose down -v
 Network v697-laravel_default Removing 
 Volume v697-laravel_dbdata Removed 
 Network v697-laravel_default Removed
# exit=0 · 2.5 s
```


## 5 · Trampa 2: depends_on sin healthcheck (la app arranca antes que MySQL)

```
$ docker compose -f compose.yaml -f compose.trampa-sin-healthcheck.yaml up -d
 Container v697-laravel-db-1 Starting 
 Container v697-laravel-db-1 Started 
 Container v697-laravel-app-1 Starting 
 Container v697-laravel-app-1 Started 
 Container v697-laravel-web-1 Starting 
 Container v697-laravel-web-1 Started
# exit=0 · 0.7 s
```

**La app murió a los 0.8 s; MySQL quedó sano a los 8.6 s.**

```
$ docker compose -f compose.yaml -f compose.trampa-sin-healthcheck.yaml ps -a
NAME                 IMAGE            COMMAND                  SERVICE   CREATED         STATUS                     PORTS
v697-laravel-app-1   v697-app:multi   "entrypoint php-fpm"     app       9 seconds ago   Exited (1) 8 seconds ago   
v697-laravel-db-1    mysql:8.4        "docker-entrypoint.s…"   db        9 seconds ago   Up 8 seconds (healthy)     3306/tcp, 33060/tcp
v697-laravel-web-1   v697-web:multi   "/docker-entrypoint.…"   web       9 seconds ago   Up 8 seconds               0.0.0.0:8697->80/tcp, [::]:8697->80/tcp
# exit=0 · 0.1 s
```

```
$ docker compose -f compose.yaml -f compose.trampa-sin-healthcheck.yaml logs app
app-1  | #41 /var/www/html/artisan(16): Illuminate\\Foundation\\Application->handleCommand()
app-1  |   SQLSTATE[HY000] [2002] Connection refused (Connection: mysql, Host: db, Por  
app-1  |   SQLSTATE[HY000] [2002] Connection refused  
# exit=0 · 0.1 s
```

```
$ curl -s -o /dev/null -w "%{http_code}\n" localhost:8697/
502
# exit=0 · 3.1 s
```

```
$ docker compose -f compose.yaml -f compose.trampa-sin-healthcheck.yaml down -v
 Volume v697-laravel_dbdata Removing 
 Volume v697-laravel_dbdata Removed 
 Network v697-laravel_default Removed
# exit=0 · 1.8 s
```


## 6 · Trampa 3: storage y bootstrap/cache sin permisos

```
$ docker compose -f compose.yaml -f compose.trampa-permisos.yaml up -d
 Container v697-laravel-db-1 Waiting 
 Container v697-laravel-db-1 Healthy 
 Container v697-laravel-app-1 Starting 
 Container v697-laravel-app-1 Started 
 Container v697-laravel-web-1 Starting 
 Container v697-laravel-web-1 Started
# exit=0 · 9.2 s
```

```
$ docker compose -f compose.yaml -f compose.trampa-permisos.yaml ps
NAME                 IMAGE                   COMMAND                  SERVICE   CREATED          STATUS                    PORTS
v697-laravel-app-1   v697-app:sin-permisos   "entrypoint php-fpm"     app       19 seconds ago   Up 10 seconds             9000/tcp
v697-laravel-db-1    mysql:8.4               "docker-entrypoint.s…"   db        19 seconds ago   Up 19 seconds (healthy)   3306/tcp, 33060/tcp
v697-laravel-web-1   v697-web:multi          "/docker-entrypoint.…"   web       19 seconds ago   Up 10 seconds             0.0.0.0:8697->80/tcp, [::]:8697->80/tcp
# exit=0 · 0.2 s
```

```
$ docker compose -f compose.yaml -f compose.trampa-permisos.yaml logs app
app-1  |   Creating migration table ...................................... 15.91ms DONE
app-1  |   0001_01_01_000000_create_users_table .......................... 74.33ms DONE
app-1  |   0001_01_01_000001_create_cache_table .......................... 47.02ms DONE
app-1  |   0001_01_01_000002_create_jobs_table ........................... 89.17ms DONE
app-1  | [29-Oct-2026 13:19:10] NOTICE: ready to handle connections
# exit=0 · 0.2 s
```

```
$ curl -s -o /dev/null -w "%{http_code}\n" localhost:8697/
500
# exit=0 · 0.0 s
```

```
$ docker compose -f compose.yaml -f compose.trampa-permisos.yaml logs app | grep -i 'permission denied'

# exit=0 · 0.2 s
```

```
$ docker compose -f compose.yaml -f compose.trampa-permisos.yaml logs app | grep production.ERROR
app-1  | [2026-10-29 13:19:20] production.ERROR: tempnam(): file created in the system's temporary directory {"exception":"[object] (ErrorException(code: 0): tempnam(): file created in the system's temporary directory at /var/www/html/vendo …
# exit=0 · 0.2 s
```

```
$ docker compose exec app ls -ld storage storage/framework/views bootstrap/cache
drwxr-xr-x    2 root     root          4096 Oct 29 13:17 bootstrap/cache
drwxr-xr-x    5 root     root          4096 Sep 30 13:56 storage
drwxr-xr-x    2 root     root          4096 Sep 30 13:56 storage/framework/views
# exit=0 · 0.2 s
```

```
$ docker compose exec app sh -c "ps -o user,args | grep php-fpm"
root     php-fpm: master process (/usr/local/etc/php-fpm.conf)
www-data php-fpm: pool www
www-data php-fpm: pool www
# exit=0 · 0.2 s
```

```
$ docker compose -f compose.yaml -f compose.trampa-permisos.yaml down -v
 Network v697-laravel_default Removing 
 Volume v697-laravel_dbdata Removed 
 Network v697-laravel_default Removed
# exit=0 · 2.5 s
```

El arreglo es la etapa `runtime` del Dockerfile: `RUN chown -R www-data:www-data storage bootstrap/cache`.

```
$ docker compose up -d
 Container v697-laravel-web-1 Starting 
 Container v697-laravel-web-1 Started
# exit=0 · 9.2 s
```

```
$ docker compose exec app ls -ld storage bootstrap/cache
drwxr-xr-x    1 www-data www-data      4096 Oct 29 13:16 bootstrap/cache
drwxr-xr-x    1 www-data www-data      4096 Sep 30 13:56 storage
# exit=0 · 0.2 s
```

```
$ curl -s -o /dev/null -w "%{http_code}\n" localhost:8697/
200
# exit=0 · 0.0 s
```

```
$ docker compose down -v
 Network v697-laravel_default Removing 
 Volume v697-laravel_dbdata Removed 
 Network v697-laravel_default Removed
# exit=0 · 2.0 s
```


## 7 · Trampa 4: montar el proyecto entero tapa el vendor de la imagen

```
$ ls -d vendor; grep -x /vendor .gitignore
ls: cannot access 'vendor': No such file or directory
/vendor
# exit=0 · 0.0 s
```

Primero con la imagen gorda, que (como casi todos los tutoriales) no copia ningún php.ini:

```
$ MIGRAR=0 docker compose -f compose.yaml -f compose.gorda.yaml -f compose.trampa-vendor.yaml up -d
 Container v697-laravel-app-1 Started 
 Container v697-laravel-web-1 Starting 
 Container v697-laravel-web-1 Started
# exit=0 · 9.2 s
```

```
$ docker compose -f compose.yaml -f compose.gorda.yaml -f compose.trampa-vendor.yaml ps
NAME                 IMAGE            COMMAND                  SERVICE   CREATED          STATUS                    PORTS
v697-laravel-app-1   v697-app:gorda   "entrypoint php-fpm"     app       11 seconds ago   Up 2 seconds              9000/tcp
v697-laravel-db-1    mysql:8.4        "docker-entrypoint.s…"   db        11 seconds ago   Up 10 seconds (healthy)   3306/tcp, 33060/tcp
v697-laravel-web-1   v697-web:multi   "/docker-entrypoint.…"   web       11 seconds ago   Up 2 seconds              0.0.0.0:8697->80/tcp, [::]:8697->80/tcp
# exit=0 · 0.1 s
```

```
$ curl -s -o /dev/null -w "%{http_code}\n" localhost:8697/
200
# exit=0 · 0.0 s
```

```
$ curl -s -i localhost:8697/ | grep -E 'HTTP/|Fatal error'
HTTP/1.1 200 OK
<b>Fatal error</b>:  Uncaught Error: Failed opening required '/var/www/html/public/../vendor/autoload.php' (include_path='.:/usr/local/lib/php') in /var/www/html/public/index.php:14
# exit=0 · 0.1 s
```

```
$ docker compose exec app sh -c "php -i | grep -E 'Loaded Configuration|^display_errors'"
Loaded Configuration File => (none)
display_errors => STDOUT => STDOUT
# exit=0 · 0.2 s
```

```
$ docker compose exec app ls vendor
ls: cannot access 'vendor': No such file or directory
# exit=2 · 0.2 s
```

```
$ docker run --rm --entrypoint sh v697-app:gorda -c 'ls vendor | wc -l'
37
# exit=0 · 0.4 s
```

```
$ docker compose -f compose.yaml -f compose.gorda.yaml -f compose.trampa-vendor.yaml down -v
 Volume v697-laravel_dbdata Removing 
 Volume v697-laravel_dbdata Removed 
 Network v697-laravel_default Removed
# exit=0 · 2.6 s
```

Ahora con la multietapa, que copia php.ini-production:

```
$ MIGRAR=0 docker compose -f compose.yaml -f compose.trampa-vendor.yaml up -d
 Container v697-laravel-app-1 Started 
 Container v697-laravel-web-1 Starting 
 Container v697-laravel-web-1 Started
# exit=0 · 9.2 s
```

```
$ curl -s -o /dev/null -w "%{http_code}\n" localhost:8697/
500
# exit=0 · 0.0 s
```

```
$ docker compose exec app sh -c "php -i | grep -E 'Loaded Configuration|^display_errors'"
Loaded Configuration File => /usr/local/etc/php/php.ini
display_errors => Off => Off
# exit=0 · 0.2 s
```

```
$ docker compose -f compose.yaml -f compose.trampa-vendor.yaml logs app | grep autoload
app-1  | NOTICE: PHP message: PHP Fatal error:  Uncaught Error: Failed opening required '/var/www/html/public/../vendor/autoload.php' (include_path='.:/usr/local/lib/php') in /var/www/html/public/index.php:14
# exit=0 · 0.2 s
```

```
$ docker compose -f compose.yaml -f compose.trampa-vendor.yaml down -v
 Network v697-laravel_default Removing 
 Volume v697-laravel_dbdata Removed 
 Network v697-laravel_default Removed
# exit=0 · 2.3 s
```

El arreglo: montar solo lo que editas (compose.dev.yaml: app/, routes/, resources/).

```
$ docker compose -f compose.yaml -f compose.dev.yaml up -d
 Container v697-laravel-web-1 Starting 
 Container v697-laravel-web-1 Started
# exit=0 · 9.2 s
```

```
$ curl -s -o /dev/null -w "%{http_code}\n" localhost:8697/
200
# exit=0 · 0.0 s
```

```
$ tail -1 routes/web.php
Route::get('/hola', fn () => 'hola desde el contenedor, sin rebuild');
# exit=0 · 0.0 s
```

```
$ curl -s localhost:8697/hola
hola desde el contenedor, sin rebuild
# exit=0 · 0.0 s
```

```
$ docker compose -f compose.yaml -f compose.dev.yaml down -v
 Volume v697-laravel_dbdata Removing 
 Volume v697-laravel_dbdata Removed 
 Network v697-laravel_default Removed
# exit=0 · 2.1 s
```


## 8 · La gorda también responde: el tamaño no da error

```
$ docker compose -f compose.yaml -f compose.gorda.yaml up -d
 Container v697-laravel-web-1 Starting 
 Container v697-laravel-web-1 Started
# exit=0 · 9.2 s
```

Primera respuesta 200 con la gorda (frío): **9.5 s**.

```
$ curl -s -o /dev/null -w "%{http_code}\n" localhost:8697/
200
# exit=0 · 0.0 s
```

```
$ docker compose -f compose.yaml -f compose.gorda.yaml down -v
 Network v697-laravel_default Removing 
 Volume v697-laravel_dbdata Removed 
 Network v697-laravel_default Removed
# exit=0 · 2.2 s
```


## 9 · Limpieza

```
$ docker image rm v697-app:multi v697-app:gorda v697-app:sin-permisos v697-web:multi
Untagged: v697-app:sin-permisos
Deleted: sha256:ebef8ab8e205a868cf904bd57fbc9c376966263412308abfa3efb19112785f11
Untagged: v697-web:multi
Deleted: sha256:4c0e977df8605b3c1206ca49a6d236f770ab394c0344052c992fd62bda0b24b9
# exit=0 · 0.7 s
```

```
$ docker image ls -q v697-*

# exit=0 · 0.0 s
```

```
$ docker ps -a --filter name=v697

# exit=0 · 0.0 s
```

```
$ docker volume ls --filter name=v697 -q

# exit=0 · 0.1 s
```

```
$ docker network ls --filter name=v697 -q

# exit=0 · 0.0 s
```
