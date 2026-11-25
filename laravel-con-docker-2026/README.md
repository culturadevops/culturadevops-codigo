# Laravel con Docker en 2026 (cultura-devops 697)

Código del vídeo [«Laravel con Docker en 2026: PHP, MySQL y Compose, paso a paso (medido)»](https://youtu.be/mRkmKa0yilU) del canal Cultura DevOps.

---

Laravel 13 + PHP-FPM 8.5 (imagen multietapa) + nginx 1.28 + MySQL 8.4 con Docker Compose, y las trampas que no dan error.
Todo lo que sale en el vídeo está en `SALIDA.md`, que se regenera con `python ejecutar_todo.py`.

## Qué hay

| archivo | qué es |
|---|---|
| `app/` | El esqueleto `laravel/laravel` 13.11.0 tal cual (framework v13.39.0 en `composer.lock`), **sin `vendor/`**, como queda después de un `git clone`. Se le añadió solo `.dockerignore`. |
| `docker/Dockerfile` | Multietapa: `vendor` (composer:2) → `base` (php:8.5-fpm-alpine + pdo_mysql) → `runtime` (chown de `storage` y `bootstrap/cache`) · `sin-permisos` (trampa) · `web` (nginx con `public/`). |
| `docker/Dockerfile.gorda` | La imagen de tutorial: una etapa, Debian, git, node, npm, composer y dependencias de desarrollo. |
| `docker/entrypoint.sh` | Con `MIGRAR=1` corre `php artisan migrate --force` y luego arranca php-fpm. |
| `docker/nginx.conf` | `fastcgi_pass app:9000` y `root /var/www/html/public`. |
| `docker/app.env` | Variables de la app: `DB_HOST=db`, `LOG_CHANNEL=stderr`. La `APP_KEY` es de demo. |
| `docker/app.env.trampa-127` | Igual, pero con `DB_HOST=127.0.0.1`. |
| `compose.yaml` | La versión buena: healthcheck en MySQL y `depends_on: condition: service_healthy`. |
| `compose.trampa-*.yaml`, `compose.gorda.yaml` | Las trampas, que se suman con `-f`. |
| `compose.dev.yaml` | El arreglo para desarrollar: monta solo `app/`, `routes/` y `resources/`. |
| `ejecutar_todo.py` | Ejecuta y mide todo, y escribe `SALIDA.md` y `medidas.json`. |

## Usarlo a mano

```sh
cp -r app/. /tmp/milaravel && cp -r docker compose*.yaml /tmp/milaravel && cd /tmp/milaravel
docker compose up -d --build        # la primera vez, construye
curl -s -o /dev/null -w "%{http_code}\n" localhost:8697   # 200
docker compose down -v              # siempre con -v: si no, el volumen de MySQL se queda
```

Las trampas:

```sh
APP_ENV_FILE=docker/app.env.trampa-127 MIGRAR=0 docker compose up -d   # 1 · 127.0.0.1 → 500
docker compose -f compose.yaml -f compose.trampa-sin-healthcheck.yaml up -d   # 2 · la app muere
docker compose -f compose.yaml -f compose.trampa-permisos.yaml up -d --build  # 3 · storage → 500
MIGRAR=0 docker compose -f compose.yaml -f compose.trampa-vendor.yaml up -d   # 4 · sin vendor → 500
docker compose -f compose.yaml -f compose.gorda.yaml up -d --build            # 5 · la gorda
```

## Repetir las medidas

```sh
python ejecutar_todo.py           # 2 repeticiones por medida
python ejecutar_todo.py --rapido  # 1
```

- Ejecútalo desde una shell con `sh` y `curl` en el PATH (Git Bash en Windows, Linux o macOS).
- Copia todo a un directorio de `tempfile.mkdtemp()` y trabaja ahí; al acabar borra solo ese directorio.
- Necesita el puerto 8697 libre.
- Limpia lo suyo: `down -v` después de cada escenario, y al final `docker image rm` de las imágenes `v697-*`.
- `cpus: "2"` en app y db. Los builds sin caché bajan paquetes de composer (y de apt en la gorda), así que esos tiempos dependen de la red.
- Las bases (`php:8.5-fpm-alpine`, `php:8.5-fpm`, `composer:2`, `nginx:1.28-alpine`, `mysql:8.4`) tienen que estar descargadas antes: no se mide la descarga.

## Regenerar `app/`

```sh
docker run --rm -v "$PWD/app:/out" composer:2 sh -c "composer create-project laravel/laravel:13.11.0 /tmp/app --no-interaction -q && \
  tar -C /tmp/app --exclude=./vendor --exclude=./.env --exclude=./database/database.sqlite -cf - . | tar -C /out -xf -"
```

El esqueleto trae un `CLAUDE.md` y un `AGENTS.md` (instrucciones de Laravel Boost para agentes). Se movieron a `_ARCHIVO/` para que no los lea ningún agente de la fábrica: no hacen falta para la app.
