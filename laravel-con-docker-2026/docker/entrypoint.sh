#!/bin/sh
# Si MIGRAR=1, corre las migraciones antes de arrancar php-fpm. set -e: si fallan, el contenedor muere.
set -e
if [ "${MIGRAR:-0}" = "1" ]; then
  php artisan migrate --force
fi
exec "$@"
