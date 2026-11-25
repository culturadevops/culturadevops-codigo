# SALIDA — curso «Redes para gente de DevOps: DNS, NAT, TLS y el «en mi máquina sí»»

> Generado por `ejecutar_todo.py`. **No se escribe a mano.**

- fecha: `2026-10-05 14:41:34Z`
- Docker `29.6.2` · anfitrión `Windows 10`
- `curl 8.14.1`
- `OpenSSL 3.5.7 9 Jun 2026 (Library: OpenSSL 3.5.7 9 Jun 2026)`
- `nginx version: nginx/1.26.3`
- `Python 3.13.5`

## Leccion 01 — Escuchar en 127.0.0.1 o en 0.0.0.0

`sh lecciones/01_escuchar.sh   # en docker:cli, con el socket de Docker` · codigo de salida `0`

```
== 1.1 · Dentro del contenedor, todo bien ==
  curl desde DENTRO:  HTTP 200
  escuchando en:      127.0.0.1:8000

== 1.2 · Desde fuera, con el puerto publicado ==
  docker port:        0.0.0.0:18001
  curl desde FUERA:   curl: (52) Empty reply from server

== 1.3 · Lo correcto: escuchar en 0.0.0.0 (todas las interfaces DEL CONTENEDOR) ==
  escuchando en:      0.0.0.0:8000
  curl desde FUERA:   HTTP 200

== 1.4 · Y la otra cara: -p 18001:8000 publica en TODAS las interfaces de la máquina ==
  -p 18001:8000            -> 0.0.0.0:18001
  -p 127.0.0.1:18001:8000  -> 127.0.0.1:18001
```

## Leccion 02 — Las redes de Docker y quién ve a quién

`sh lecciones/02_dns_de_docker.sh   # en docker:cli, con el socket de Docker` · codigo de salida `0`

```
== 2.1 · La red por defecto: sin DNS por nombre ==
  la db tiene la IP 172.17.0.3
  getent hosts red-db -> (nada: no resuelve)

== 2.2 · Una red creada por ti: el DNS de Docker en 127.0.0.11 ==
  /etc/resolv.conf -> nameserver 127.0.0.11
  getent hosts red-db -> 192.168.16.2    red-db

== 2.3 · Dos redes no se ven entre sí ==
  desde red-otra: red-db no resuelve
  ping a 192.168.16.2 (por IP): sin respuesta

== 2.4 · Una red interna: sin salida a internet, a propósito ==
  curl a internet desde red-interna -> curl: (6) Could not resolve host: deb.debian.org
  curl a internet desde red-tienda  -> HTTP 200
```

## Leccion 03 — El DNS que resolvía a lo viejo

`sh lecciones/03_cache_dns.sh   # en docker:cli, con el socket de Docker` · codigo de salida `0`

```
== 3.1 · Todo bien: los dos nginx llegan al backend ==
  red-backend está en 10.77.0.10
  nginx (proxy_pass fijo):     soy el backend v1
  nginx (resolver + variable): soy el backend v1

== 3.2 · Se redespliega el backend, y otro servicio coge su IP vieja ==
  red-backend (v2) está ahora en 10.77.0.4 · en 10.77.0.10 está red-facturas
  nginx (proxy_pass fijo):     soy FACTURAS, otro servicio   <- HTTP 200
  nginx (resolver + variable): soy el backend v2
  getent hosts red-backend:    10.77.0.4       red-backend

== 3.3 · Lo que dice el DNS de Docker, con su TTL ==
  red-backend.		600	IN	A	10.77.0.4
```

## Leccion 04 — TLS: la cadena, el SAN, la caducidad y el nombre

`sh lecciones/04_tls.sh   # en docker:cli, con el socket de Docker` · codigo de salida `0`

```
== 4.1 · El bueno: hoja + intermedia, con SAN, en fecha ==
  bueno                          curl: ok
                                 openssl: Verify return code: 0 (ok)

== 4.2 · Cadena incompleta: el servidor manda solo la hoja ==
  sin la intermedia              curl: curl: (60) SSL certificate problem: unable to get local issuer certificate
                                 openssl: Verify return code: 21 (unable to verify the first certificate)

== 4.3 · Sin SAN: el nombre solo en el CN ==
  sin SAN                        curl: ok
                                 openssl: Verify return code: 0 (ok)

== 4.3b · El mismo certificado sin SAN, con un cliente en Go ==
  bueno:   go1.26.8 200 OK
  sin SAN: go1.26.8 Get "https://api.tienda.test:4433/": tls: failed to verify certificate: x509: certificate relies on legacy Common Name field, use SANs instead

== 4.4 · Caducado ==
  caducado                       curl: curl: (60) SSL certificate problem: certificate has expired
                                 openssl: Verify return code: 10 (certificate has expired)

== 4.5 · Nombre equivocado ==
  para otra.tienda.test          curl: curl: (60) SSL: no alternative certificate subject name matches target hostname 'api.tienda.test'
                                 openssl: Verify return code: 62 (hostname mismatch)

== 4.6 · Antes de que pase: cuántos días le quedan ==
  bueno     caduca: Jan  3 14:42:02 2027 GMT -> 89 días
  caducado  caduca: Apr  1 00:00:00 2025 GMT -> -552 días
            checkend 30 días: ALARMA
```

## Leccion 05 — El MTU: el fallo que solo aparece con respuestas grandes

`sh lecciones/05_mtu.sh   # en docker:cli, con el socket de Docker` · codigo de salida `0`

```
== 5.1 · La trampa: el router tira los ICMP «fragmentation needed» ==
  MTU del cliente: 1500 · salida del router hacia el cliente: 1280
      400 bytes -> HTTP 200 · 400 bytes
     1000 bytes -> HTTP 200 · 1000 bytes
     1300 bytes -> HTTP 200 · 0 bytes · colgado: curl se rinde a los 4 s (código 28)
     1400 bytes -> HTTP 200 · 0 bytes · colgado: curl se rinde a los 4 s (código 28)
     1500 bytes -> HTTP 200 · 0 bytes · colgado: curl se rinde a los 4 s (código 28)
     3000 bytes -> HTTP 200 · 0 bytes · colgado: curl se rinde a los 4 s (código 28)
   200000 bytes -> HTTP 200 · 0 bytes · colgado: curl se rinde a los 4 s (código 28)

== 5.2 · Encontrarlo: ping desde el servidor, con «no fragmentar» ==
  ping -M do -s 1000  (1028 bytes en el cable) -> responde
  ping -M do -s 1252  (1280 bytes en el cable) -> responde
  ping -M do -s 1253  (1281 bytes en el cable) -> NADA (ni un error)
  ping -M do -s 1472  (1500 bytes en el cable) -> NADA (ni un error)

== 5.3 · Arreglo 1: dejar pasar ese ICMP ==
     1400 bytes -> HTTP 200 · 1400 bytes
   200000 bytes -> HTTP 200 · 200000 bytes
  el servidor aprendió: mtu 1280

== 5.4 · Arreglo 2, si el firewall no es tuyo: ajustar el MSS de TCP en el router ==
     1400 bytes -> HTTP 200 · 1400 bytes
   200000 bytes -> HTTP 200 · 200000 bytes
```

## Leccion 06 — La IP que ves no es la del cliente

`sh lecciones/06_ip_del_cliente.sh   # en docker:cli, con el socket de Docker` · codigo de salida `0`

```
== 6.1 · Directo a la aplicación: cada cliente con su IP ==
  cliente 10.90.0.101 -> veo 10.90.0.101 · X-Forwarded-For: -
  cliente 10.90.0.102 -> veo 10.90.0.102 · X-Forwarded-For: -

== 6.2 · Detrás de un proxy: todos son el proxy ==
  cliente 10.90.0.101 -> veo 10.90.0.20 · X-Forwarded-For: -
  cliente 10.90.0.102 -> veo 10.90.0.20 · X-Forwarded-For: -

== 6.3 · El proxy pone la IP real en X-Forwarded-For ==
  cliente 10.90.0.101 -> veo 10.90.0.21 · X-Forwarded-For: 10.90.0.101
  cliente 10.90.0.102 -> veo 10.90.0.21 · X-Forwarded-For: 10.90.0.102

== 6.4 · La trampa de la trampa: la cabecera la puede escribir cualquiera ==
  cliente 10.90.0.101, directo, con X-Forwarded-For: 10.0.0.1 (la IP «de la oficina»)
    -> veo 10.90.0.101 · X-Forwarded-For: 10.0.0.1
  lo mismo a través del proxy, que REESCRIBE la cabecera con $remote_addr
    -> veo 10.90.0.21 · X-Forwarded-For: 10.90.0.101
```

## Leccion 07 — El proyecto: diagnostico.sh

`sh lecciones/07_proyecto.sh   # en docker:cli, con el socket de Docker` · codigo de salida `0`

```
== 7.1 · Todo bien ==
diagnóstico de https://api.tienda.test/
  DNS     ✓ api.tienda.test -> 192.168.16.2 (3 ms)
  TCP     ✓ 192.168.16.2:443 abierto (2 ms)
  TLS     ✓ verificado · DNS:api.tienda.test · 2 certificados en la cadena · caduca en 89 días
  HTTP    ✓ 200 en 0.002559 s
  CUERPO  ✓ 5 bytes en 0.002539 s
  -> todo bien (0)
  (código de salida 0)

== 7.2 · Un nombre que no existe ==
diagnóstico de https://api.tienda.text/
  DNS     ✗ «api.tienda.text» no resuelve
  -> falla la capa 1 (DNS)
  (código de salida 1)

== 7.3 · El contenedor está, el servicio no ==
diagnóstico de http://red-mudo:8000/
  DNS     ✓ red-mudo -> 192.168.16.3 (2 ms)
  TCP     ✗ nadie escucha en 192.168.16.3:8000 (o un firewall lo tira)
  -> falla la capa 2 (TCP)
  (código de salida 2)

== 7.4 · El certificado sin SAN ==
diagnóstico de https://api.tienda.test:8443/
  DNS     ✓ api.tienda.test -> 192.168.16.2 (2 ms)
  TCP     ✓ 192.168.16.2:8443 abierto (3 ms)
  TLS     ✗ sin SAN: curl y openssl lo aceptan, Go lo rechaza (lección 4)
  -> falla la capa 3 (TLS)
  (código de salida 3)

== 7.5 · Escucha en 127.0.0.1 detrás de -p (lección 1) ==
diagnóstico de http://host.docker.internal:18007/
  DNS     ✓ host.docker.internal -> 192.168.65.254 (4 ms)
  TCP     ✓ 192.168.65.254:18007 abierto (4 ms)
  HTTP    ✗ (52) Empty reply from server
  -> falla la capa 4 (HTTP)
  (código de salida 4)

== 7.6 · El camino con el MTU roto (lección 5) ==
diagnóstico de http://10.82.0.10/200000
  DNS     ✓ 10.82.0.10 -> 10.82.0.10 (2 ms)
  TCP     ✓ 10.82.0.10:80 abierto (2 ms)
  HTTP    ✓ 200 en 0.000597 s
  CUERPO  ✗ llegaron 0 de 200000 bytes y se colgó (código 28): pequeño sí, grande no -> mira el MTU
  -> falla la capa 5 (CUERPO)
  (código de salida 5)
```

