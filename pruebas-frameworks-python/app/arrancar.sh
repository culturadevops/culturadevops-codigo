# Cada framework con su servidor de producción habitual. WORKERS procesos (por defecto 2: uno por CPU del contenedor).
# gunicorn: workers síncronos (el tipo por defecto) para las apps WSGI. uvicorn: uvloop + httptools (uvicorn[standard]).
set -e
case "$FW" in
  django)  exec gunicorn srv_django:application -b 0.0.0.0:8080 -w "$WORKERS" --log-level warning ;;
  flask)   exec gunicorn srv_flask:app -b 0.0.0.0:8080 -w "$WORKERS" --log-level warning ;;
  falcon)  exec gunicorn srv_falcon:app -b 0.0.0.0:8080 -w "$WORKERS" --log-level warning ;;
  fastapi|starlette|litestar)
           exec uvicorn "srv_$FW:app" --host 0.0.0.0 --port 8080 --workers "$WORKERS" --log-level warning --no-access-log ;;
  sanic)   exec sanic srv_sanic:app --host 0.0.0.0 --port 8080 --workers "$WORKERS" --no-access-logs ;;
  *)       echo "FW desconocido: $FW" >&2; exit 1 ;;
esac
