# SALIDA — Nginx: errores 403, 404 y 502 y cómo arreglarlos (cultura-devops)

> Corrida del 2026-10-23 12:51. nginx version: nginx/1.31.8 (nginx:1.31.8-alpine), backend python:3.13-alpine, cliente curlimages/curl:8.23.0, en una red de Docker propia.

```
### 0 · La configuración de partida
web$ cat /etc/nginx/conf.d/default.conf
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;
    error_log /var/log/nginx/demo-error.log;

    location / {
    }

    location /api/ {
        proxy_pass http://app:8080/;
    }
}
web$ nginx -t
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
$ curl -s -o /dev/null -w '%{http_code}' http://web/
200

### 1 · 403: una carpeta sin index.html
web$ ls /usr/share/nginx/html/docs/
manual.txt
$ curl http://web/docs/
403
web$ tail -n 1 /var/log/nginx/demo-error.log
[error] 73#73: *2 directory index of "/usr/share/nginx/html/docs/" is forbidden, client: 192.168.192.4, server: localhost, request: "GET /docs/ HTTP/1.1", host: "web"
web$ echo '<h1>Docs</h1>' > /usr/share/nginx/html/docs/index.html
$ curl http://web/docs/
200

### 2 · 403: un archivo que nginx no puede leer
web$ ls -l /usr/share/nginx/html/reporte.html
-rw-------    1 root     root            17 Oct 23 17:51 /usr/share/nginx/html/reporte.html
$ curl http://web/reporte.html
403
web$ tail -n 1 /var/log/nginx/demo-error.log
[error] 75#75: *4 open() "/usr/share/nginx/html/reporte.html" failed (13: Permission denied), client: 192.168.192.4, server: localhost, request: "GET /reporte.html HTTP/1.1", host: "web"
web$ ps -o user,args | grep 'nginx: '
nginx    nginx: worker process
root     nginx: master process nginx -g daemon off;
web$ chmod 644 /usr/share/nginx/html/reporte.html
$ curl http://web/reporte.html
200

### 3 · 403: la carpeta, no el archivo
web$ ls -ld /usr/share/nginx/html/privado; ls -l /usr/share/nginx/html/privado/hola.html
drwx------    2 root     root          4096 Oct 23 17:51 /usr/share/nginx/html/privado
-rw-r--r--    1 root     root             5 Oct 23 17:51 /usr/share/nginx/html/privado/hola.html
$ curl http://web/privado/hola.html
403
web$ tail -n 1 /var/log/nginx/demo-error.log
[error] 77#77: *6 open() "/usr/share/nginx/html/privado/hola.html" failed (13: Permission denied), client: 192.168.192.4, server: localhost, request: "GET /privado/hola.html HTTP/1.1", host: "web"
web$ chmod 755 /usr/share/nginx/html/privado
$ curl http://web/privado/hola.html
200

### 4 · 404: el root mal escrito
web$ grep root /etc/nginx/conf.d/default.conf
    root /usr/share/nginx/htm;
web$ nginx -t
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
$ curl http://web/
404
web$ tail -n 1 /var/log/nginx/demo-error.log
[error] 215#215: *8 "/usr/share/nginx/htm/index.html" is not found (2: No such file or directory), client: 192.168.192.4, server: localhost, request: "GET / HTTP/1.1", host: "web"
(root corregido a /usr/share/nginx/html)
$ curl http://web/
200

### 5 · 404: una aplicación de una sola página (SPA)
$ curl http://web/                 # la portada de la SPA
200
$ curl http://web/panel/usuarios   # una ruta que existe en JavaScript, no en el disco
404
web$ tail -n 1 /var/log/nginx/demo-error.log
[error] 272#272: *11 open() "/usr/share/nginx/html/panel/usuarios" failed (2: No such file or directory), client: 192.168.192.4, server: localhost, request: "GET /panel/usuarios HTTP/1.1", host: "web"
web$ grep try_files /etc/nginx/conf.d/default.conf
        try_files $uri $uri/ /index.html;
$ curl http://web/panel/usuarios
200
$ curl http://web/no-existe.png   # ojo: con este try_files todo devuelve 200
200
web$ grep -A2 'location' /etc/nginx/conf.d/default.conf | grep -v '^--'
    location / {
        try_files $uri $uri/ /index.html;
    }
    location /assets/ {
        try_files $uri =404;
    }
    location /api/ {
        proxy_pass http://app:8080/;
    }
$ curl http://web/panel/usuarios ; curl http://web/assets/no-existe.png
200
404

### 6 · 502: el backend está caído
$ curl http://web/api/   # con el backend arriba
200
(paro el backend)
$ curl http://web/api/
502
web$ tail -n 1 /var/log/nginx/demo-error.log
[error] 398#398: *18 connect() failed (111: Connection refused) while connecting to upstream, client: 192.168.192.4, server: localhost, request: "GET /api/ HTTP/1.1", upstream: "http://192.168.192.2:8080/", host: "web"
web$ curl -s -o /dev/null -w '%{http_code}' http://app:8080/   # ¿responde el backend desde nginx?
000
curl salió con código 7

### 7 · 502: el puerto equivocado
web$ grep proxy_pass /etc/nginx/conf.d/default.conf
        proxy_pass http://app:8081/;
$ curl http://web/api/
502
web$ tail -n 1 /var/log/nginx/demo-error.log
[error] 447#447: *20 connect() failed (111: Connection refused) while connecting to upstream, client: 192.168.192.4, server: localhost, request: "GET /api/ HTTP/1.1", upstream: "http://192.168.192.2:8081/", host: "web"
(proxy_pass corregido a http://app:8080/)
$ curl http://web/api/
200

### 8 · nginx -t antes de recargar
(a la config le falta el ; al final de proxy_pass)
web$ nginx -t
2026/10/23 17:52:16 [emerg] 531#531: unexpected "}" in /etc/nginx/conf.d/default.conf:18
nginx: [emerg] unexpected "}" in /etc/nginx/conf.d/default.conf:18
nginx: configuration file /etc/nginx/nginx.conf test failed
web$ nginx -t   # con la configuración buena
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful

### 9 · Dónde está el log en la imagen oficial de Docker
web$ ls -l /var/log/nginx/
total 4
lrwxrwxrwx    1 root     root            11 Oct 21 22:47 access.log -> /dev/stdout
-rw-r--r--    1 root     root          1510 Oct 23 17:52 demo-error.log
lrwxrwxrwx    1 root     root            11 Oct 21 22:47 error.log -> /dev/stderr
```
