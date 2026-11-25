# SALIDA — curso «Cadena de suministro: Trivy, firmas con cosign y registro propio»

> Generado por `ejecutar_todo.py`. **No se escribe a mano.**

- fecha: `2026-10-06 19:43:49Z`
- trivy: `0.75.0`
- cosign: `v3.1.3`
- syft: `1.54.1`
- registry: `3.1.2`
- Docker `29.6.2`

## Leccion 1

```

== 1.1 · Se sube la tienda 1.0 ==
  localhost:5000/tienda:1.0 -> sha256:e6886b70d87c...
$ docker run localhost:5000/tienda:1.0
  tienda 1.0
  (código de salida 0)

== 1.2 · La trampa: alguien sube otra imagen con la misma etiqueta ==
  docker push no preguntó nada. localhost:5000/tienda:1.0 -> sha256:6f301ad30576...
$ docker run localhost:5000/tienda:1.0
  tienda 1.0 (cambiada)
  (código de salida 0)
  la misma etiqueta, otra imagen, y ningún error

== 1.3 · Lo correcto: desplegar por digest ==
$ docker run localhost:5000/tienda@sha256:e6886b70d87c...
  tienda 1.0
  (código de salida 0)
  un digest es el hash del contenido: no se puede mover
```

## Leccion 2

```

== 2.1 · Trivy contra una imagen vieja (alpine:3.14.0) ==
$ trivy image alpine:3.14.0
  Total: 48 (UNKNOWN: 0, LOW: 0, MEDIUM: 10, HIGH: 34, CRITICAL: 4)
  (código de salida 0)
  48 vulnerabilidades, 4 críticas... y código 0: en un pipeline, este paso sale en verde

== 2.2 · Lo correcto: --exit-code 1 para lo que no se acepta ==
$ trivy image --exit-code 1 --severity CRITICAL alpine:3.14.0
  Total: 4 (CRITICAL: 4)
  (código de salida 1)

== 2.3 · Y la imagen de la tienda, con su base de hoy (alpine:3.22) ==
$ trivy image localhost:5000/tienda:1.0
  │ localhost:5000/tienda:1.0 (alpine 3.22.6) │ alpine │        0        │
  (código de salida 0)
$ trivy image --exit-code 1 --severity CRITICAL localhost:5000/tienda:1.0
  (código de salida 0)
  base de datos de Trivy del 2026-10-06: mañana el resultado puede ser otro
```

## Leccion 3

```

== 3.1 · El SBOM: la lista de lo que lleva la imagen (syft) ==
$ syft alpine:3.14.0 -o cyclonedx-json=syft.cdx.json
  14 paquetes: alpine-baselayout 3.2.0-r15, alpine-keys 2.3-r1, apk-tools 2.12.5-r1, busybox 1.33.1-r2, ...

== 3.2 · La trampa: Trivy escanea el SBOM de syft ==
$ trivy sbom syft.cdx.json
  Third-party SBOM may lead to inaccurate vulnerability detection
  Recommend using Trivy to generate SBOMs
  This OS version is no longer supported by the distribution	family="alpine" version="3.14.0"
  The vulnerability detection may be insufficient because security updates are not provided
  vulnerabilidades: 16 · escaneando la imagen eran 48 · y sin ningún error

== 3.3 · Lo que falta, y por qué ==
  libcrypto1.1    10 vulnerabilidades que el SBOM de syft no destapa
  libssl1.1       10 vulnerabilidades que el SBOM de syft no destapa
  ssl_client      12 vulnerabilidades que el SBOM de syft no destapa
  sus paquetes de origen: libcrypto1.1 -> openssl, libssl1.1 -> openssl, ssl_client -> busybox
  Trivy busca por paquete de origen; syft lo guarda en su propio campo (syft:metadata:originPackage)

== 3.4 · Lo correcto: el SBOM de la misma herramienta que lo va a escanear ==
$ trivy image --format cyclonedx --output trivy.cdx.json alpine:3.14.0 && trivy sbom trivy.cdx.json
  vulnerabilidades: 48 · escaneando la imagen: 48 · ¿iguales?: True
  y el día que salga un CVE nuevo, se vuelve a escanear el SBOM guardado, sin bajar la imagen
```

## Leccion 4

```

== 4.1 · Firmar la tienda 2.0 con cosign (por digest) ==
$ cosign sign --key cosign.key registro:5000/tienda@sha256:b308fa5e8ee6...
  Pushing signature to: registro:5000/tienda
  (código de salida 0)
$ cosign verify --key cosign.pub registro:5000/tienda:2.0
    - The signatures were verified against the specified public key
  (código de salida 0)

== 4.2 · La trampa: la etiqueta se mueve a una imagen sin firmar ==
$ cosign verify --key cosign.pub registro:5000/tienda:2.0
  Error: no signatures found
  (código de salida 10)
$ docker run localhost:5000/tienda:2.0
  tienda 2.0 (sin firmar)
  (código de salida 0)
  cosign dice que la imagen nueva no está firmada... pero docker run no le pregunta: se ejecuta igual
```

## Leccion 5

```

== 5.1 · desplegar.sh con una imagen firmada ==
$ ./desplegar.sh tienda:3.0
  desplegar: firma válida para tienda:3.0
  desplegar: arranco el digest verificado, no la etiqueta: sha256:b47e360908f1...
  tienda 3.0
  (código de salida 0)

== 5.2 · desplegar.sh con la etiqueta movida a una imagen sin firmar ==
$ ./desplegar.sh tienda:3.0
  desplegar: NO. tienda:3.0 no tiene una firma válida:
    Error: no signatures found
  (código de salida 1)
```

## Leccion 6

```

== 6.1 · La trampa: el registro sin autenticación ==
$ crane catalog registro:5000   (desde otro contenedor de la red, sin credenciales)
  tienda
  (código de salida 0)
$ crane copy registro:5000/tienda:2.0 registro:5000/tienda:1.0
  (código de salida 0)
  tienda:1.0 antes: sha256:6f301ad30576... · después: sha256:0c187abd519b... · ¿cambió?: True
  cualquiera que llegue al puerto puede leer, subir y sobrescribir etiquetas

== 6.2 · Lo correcto: el registro con usuario y contraseña (htpasswd) ==
$ crane catalog registro-auth:5000   (sin credenciales)
  Error: reading tags for registro-auth:5000: GET http://registro-auth:5000/v2/_catalog?n=1000: UNAUTHORIZED: authentication required; [map[Action:* Class: Name:catalog Type:registry]]
  (código de salida 1)
$ crane auth login registro-auth:5000 -u ci ... && crane catalog registro-auth:5000
  vacío, pero dentro
  (código de salida 0)
  ojo: por HTTP la contraseña viaja en claro. Con usuario, siempre detrás de TLS
```
