# SALIDA — «System design: el proxy inverso» (cultura-devops, vídeo 349)

> Generado por `correr.py`. **No se escribe a mano.**

- fecha: `2026-10-11 15:09:12Z`
- `nginx version: nginx/1.30.5` · curl 8.11.1 · app en Go 1.27.2 (dos instancias)
- una sola máquina; los tiempos son de esta.

```
== 1 · ¿Qué IP de cliente ve la aplicación? ==
  [nginx: proxy_pass y nada más]
$ curl http://app1:8000/ip   # directo
  app1 ve: RemoteAddr=10.77.25.5 · X-Forwarded-For="" · X-Real-IP="" · X-Forwarded-Proto=""
$ curl http://proxy/ip   # por el proxy
  app1 ve: RemoteAddr=10.77.25.4 · X-Forwarded-For="" · X-Real-IP="" · X-Forwarded-Proto=""
  [nginx: con X-Real-IP, X-Forwarded-For y X-Forwarded-Proto]
$ curl http://proxy/ip
  app1 ve: RemoteAddr=10.77.25.4 · X-Forwarded-For="10.77.25.5" · X-Real-IP="10.77.25.5" · X-Forwarded-Proto="http"
$ curl -k https://proxy/ip   # TLS termina en el proxy; la app sigue en HTTP
  app2 ve: RemoteAddr=10.77.25.4 · X-Forwarded-For="10.77.25.5" · X-Real-IP="10.77.25.5" · X-Forwarded-Proto="https"

== 2 · Una respuesta que tarda 70 s ==
  [nginx: por defecto (proxy_read_timeout 60s)]
$ curl http://proxy/lento?s=70   # por el proxy
  HTTP 504 a los 120.123972 s
$ curl http://app1:8000/lento?s=70   # directo
  HTTP 200 a los 72.037336 s

== 3 · Un cliente lento (2 MB/s) descarga 40 MB: ¿cuánto queda ocupada la aplicación? ==
  [nginx: por defecto (proxy_buffering on)]
$ curl --limit-rate 2M http://proxy/grande?mb=40
  el cliente tardó 19.933458 s
  la app: 15:14:12.976 app1 soltó 40 MB en 0.1 s
  [nginx: proxy_buffering off]
$ curl --limit-rate 2M http://proxy/grande?mb=40
  el cliente tardó 19.949716 s
  la app: 15:15:06.166 app1 soltó 40 MB en 16.6 s

== 4 · Reintentos: la app tarda 3 s y el proxy espera 2 s ==
  [nginx: proxy_read_timeout 2s · proxy_next_upstream por defecto (error timeout)]
$ curl http://proxy/procesar?s=3   # un GET con efectos
  HTTP 504 a los 4.006993 s
  procesados.log: 15:15:23.987 app1 procesado
  procesados.log: 15:15:25.989 app2 procesado
$ curl -X POST http://proxy/pagar?s=3
  HTTP 504 a los 2.002819 s
  pagos.log: 15:15:49.341 app2 cobrado
  [nginx: … y proxy_next_upstream error timeout non_idempotent]
$ curl -X POST http://proxy/pagar?s=3
  HTTP 504 a los 4.006381 s
  pagos.log: 15:16:18.390 app1 cobrado
  pagos.log: 15:16:20.392 app2 cobrado

== 5 · Subir un fichero de 2 MB ==
  [nginx: por defecto (client_max_body_size 1m)]
$ curl --data-binary @ca-certificates.crt http://proxy/subir   # unos 200 KB
  HTTP 200
$ curl --data-binary @2mb.bin http://proxy/subir
  HTTP 413
  [nginx: client_max_body_size 10m]
$ curl --data-binary @2mb.bin http://proxy/subir
  llegaron 2097152 bytes

== 6 · TLS en el proxy: lo que cuesta abrir la conexión ==
  [nginx: TLS con un certificado autofirmado (RSA 2048)]
$ curl -k https://proxy/ip   # una conexión nueva
  conectar 0.000606 s · TLS listo 0.006683 s · total 0.007710 s
$ curl http://proxy/ip   # sin TLS
  conectar 0.001138 s · total 0.002034 s
```
