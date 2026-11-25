# SALIDA — tu primer incidente: un 502 (ejecutado)

Generado por `python correr.py`. **No se edita a mano.**

- fecha: 2026-10-12 01:43 UTC
- imagen: nginx:1.30.5-alpine

## 1 · Lo que ve el usuario

`$ curl -sI http://localhost/ | head -1`

```
HTTP/1.1 502 Bad Gateway
```

## 2 · Lo que dice el registro

`$ docker logs incidente-502 2>&1 | grep error | tail -1`

```
2026/10/12 01:43:53 [error] 21#21: *1 connect() failed (111: Connection refused) while connecting to upstream, client: 127.0.0.1, server: , request: "HEAD / HTTP/1.1", upstream: "http://127.0.0.1:8080/", host: "localhost"
```

## 3 · Lo que escucha la máquina

`$ netstat -tln | grep LISTEN`

```
tcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN
```

## 4 · Arrancar el servicio

`$ cp servicio.conf /etc/nginx/conf.d/ && nginx -s reload`

```
2026/10/12 01:43:53 [notice] 68#68: signal process started
recargado
```

## 5 · Comprobar

`$ netstat -tln | grep LISTEN`

```
tcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN      
tcp        0      0 0.0.0.0:8080            0.0.0.0:*               LISTEN
```

## 6 · Lo que ve el usuario ahora

`$ curl -s -i http://localhost/ | sed -n '1p;$p'`

```
HTTP/1.1 200 OK
ok desde el servicio
```

## 7 · Otro clásico: un nombre que no resuelve

`$ nslookup api.interna`

```
** server can't find api.interna: NXDOMAIN
```

## 8 · Y lo que ve el programa

`$ curl -s http://api.interna/; echo "código de salida: $?"`

```
código de salida: 6
```

## 9 · El tercero: un certificado caducado

`$ curl -sS https://expired.badssl.com/ -o /dev/null`

```
curl: (60) SSL certificate OpenSSL verify result: certificate has expired (10)
More details here: https://curl.se/docs/sslcerts.html

curl failed to verify the legitimacy of the server and therefore could not
establish a secure connection to it. To learn more about this situation and
how to fix it, please visit the webpage mentioned above.
código de salida: 60
```

## 10 · Cuándo caducó

`$ openssl s_client … | openssl x509 -noout -enddate`

```
sh: openssl: not found
sin openssl en la imagen
```
