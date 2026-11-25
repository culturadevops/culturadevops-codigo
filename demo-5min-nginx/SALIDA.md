# SALIDA — Nginx en 5 minutos (cultura-devops)

Generado 2026-10-23 12:32 UTC con `python correr.py`. Imagen `nginx:1.31-alpine`; red de Docker propia; cliente curl en un contenedor Alpine.

## 1 · Versión y configuración

### versión

`$ nginx -v`

```
nginx version: nginx/1.31.8
```
(código de salida 0)

### la configuración

`$ cat /etc/nginx/nginx.conf`

```
events {}
http {
    upstream api {
        server backend-a;
        server backend-b;
    }
    server {
        listen 80;
        location / {
            root /usr/share/nginx/html;
        }
        location /api/ {
            proxy_pass http://api/;
        }
    }
}
```
(código de salida 0)

## 2 · Servidor web y proxy inverso

### la web estática

`$ curl http://web/`

```
<h1>Mi tienda</h1>
```
(código de salida 0)

### /api/ cuatro veces

`$ for i in 1 2 3 4; do curl -s http://web/api/; done`

```
backend-a
backend-b
backend-a
backend-b
```
(código de salida 0)

## 3 · Un error de sintaxis

### probar antes de recargar

`$ nginx -t`

```
2026/10/23 12:32:14 [emerg] 85#85: unexpected "}" in /etc/nginx/nginx.conf:6
nginx: [emerg] unexpected "}" in /etc/nginx/nginx.conf:6
nginx: configuration file /etc/nginx/nginx.conf test failed
```
(código de salida 1)

### ¿y la web sigue?

`$ curl http://web/api/`

```
backend-a
```
(código de salida 0)

### arreglado

`$ nginx -t`

```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```
(código de salida 0)

## 4 · Recargar con tráfico

### 1000 peticiones a /api/ mientras se recarga 5 veces

`$ (1000 x curl -w %{http_code} http://web/api/) & nginx -s reload x5`

```
1000 200
```

## 5 · Se cae un backend

### backend-a apagado: 6 peticiones, con su tiempo

`$ docker stop backend-a; for i in $(seq 6); do curl -w '%{http_code} %{time_total}s' http://web/api/; done`

```
200 0.000880s backend-b
200 38.547946s backend-b
200 0.000636s backend-b
200 0.000487s backend-b
200 0.000422s backend-b
200 0.000514s backend-b
```
(código de salida 0)

### lo que dejó nginx en su registro

`$ docker logs web | grep error | tail -1`

```
2026/10/23 12:32:56 [error] 137#137: *1020 connect() failed (113: Host is unreachable) while connecting to upstream, client: 192.168.192.5, server: , request: "GET /api/ HTTP/1.1", upstream: "http://192.168.192.2:80/", host: "web"
```

## 6 · El arreglo: no esperar tanto

### la línea nueva

`$ grep -n proxy_connect_timeout /etc/nginx/nginx.conf`

```
14:            proxy_connect_timeout 2s;
```
(código de salida 0)

### probar y recargar

`$ nginx -t && nginx -s reload`

```
recargado
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
2026/10/23 12:32:58 [notice] 157#157: signal process started
```
(código de salida 0)

### backend-a apagado otra vez: las mismas 6 peticiones

`$ docker stop backend-a; for i in $(seq 6); do curl -w '%{http_code} %{time_total}s' http://web/api/; done`

```
200 2.003544s backend-b
200 0.000527s backend-b
200 0.000534s backend-b
200 0.000447s backend-b
200 0.000483s backend-b
200 0.000479s backend-b
```
(código de salida 0)

## Nota · otra corrida de la sección 5 (2026-10-23 12:31 UTC, mismo `correr.py`)

La primera petición con backend-a apagado no siempre tarda lo mismo: depende de cómo falle la conexión.

```
200 60.002438s backend-b
200 0.000615s backend-b
200 0.000425s backend-b
200 0.000454s backend-b
200 0.000446s backend-b
200 0.000513s backend-b
```
y en el registro: `upstream timed out (110: Operation timed out) while connecting to upstream` (60 s es el valor por defecto de `proxy_connect_timeout`).
