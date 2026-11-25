# syntax=docker/dockerfile:1
# Laravel 13 + PHP-FPM 8.5, imagen MULTIETAPA (cultura-devops 697).
# Etapa 1: composer instala vendor. Etapa 2: runtime ligero sin composer. Etapa 3: nginx con /public.

# ── 1 · vendor: composer instala las dependencias ──────────────────────────
FROM composer:2 AS vendor
WORKDIR /app
# Primero SOLO composer.json y composer.lock: si no cambian, esta capa sale de la caché.
COPY composer.json composer.lock ./
RUN composer install --no-dev --no-scripts --no-autoloader --prefer-dist --no-interaction --no-progress
# Luego el código, y el autoload optimizado (aquí sí corren los scripts: package:discover).
COPY . .
RUN composer dump-autoload --optimize --classmap-authoritative --no-dev

# ── 2 · base: el runtime, sin composer ni herramientas de compilación ──────
FROM php:8.5-fpm-alpine AS base
RUN docker-php-ext-install pdo_mysql
# La imagen oficial NO trae php.ini: sin él, display_errors=STDOUT y un error fatal sale en la página con un 200.
RUN cp "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini"
WORKDIR /var/www/html
COPY --from=vendor /app /var/www/html
COPY docker/entrypoint.sh /usr/local/bin/entrypoint
RUN chmod +x /usr/local/bin/entrypoint
ENTRYPOINT ["entrypoint"]
CMD ["php-fpm"]

# ── trampa: la misma imagen SIN arreglar permisos (todo es de root) ───────
FROM base AS sin-permisos

# ── 2b · runtime: php-fpm corre como www-data; solo estas dos carpetas se escriben
FROM base AS runtime
RUN chown -R www-data:www-data storage bootstrap/cache

# ── 3 · web: nginx con los archivos públicos ───────────────────────────────
FROM nginx:1.28-alpine AS web
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=vendor /app/public /var/www/html/public
