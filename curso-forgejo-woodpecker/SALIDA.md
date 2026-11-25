# SALIDA — curso «Tu propio GitHub y tu propio CI: Forgejo y Woodpecker»

> Generado por `ejecutar_todo.py`. **No se escribe a mano.**

- fecha: `2026-10-06 20:16:29Z`
- `forgejo version 13.0.5+gitea-1.22.0`
- `woodpecker-server version 3.18.1`
- Docker `29.6.2`

## Lecciones 1, 2 y 3 · Forgejo recién instalado

```
== 1.1 · Un Forgejo recién instalado. Se registra el primero que llega ==
  alta de «intruso»: HTTP 303, redirige a / · is_admin: True
  alta de «duena»: HTTP 303, redirige a / · is_admin: False
  el primero en registrarse es administrador: si la instancia está en internet, gana quien llegue antes

== 2.1 · El registro, abierto por defecto ==
  alta de «cualquiera», sin invitación: HTTP 303, redirige a /
  usuarios en la instancia: 3

== 3.1 · La URL de clonado, con ROOT_URL sin tocar ==
  clone_url: http://localhost:3000/duena/tienda.git
  es la que Forgejo enseña en la web y manda a Woodpecker: desde otra máquina, localhost es ella misma
```

## Lecciones 2 y 3 · Forgejo bien configurado

```
$ forgejo admin user create --admin --username duena ...
  New user 'duena' has been successfully created!  (código de salida 0)
== 2.2 · Lo correcto: DISABLE_REGISTRATION=true (y el administrador, creado por consola) ==
  alta de «cualquiera»: HTTP 403 · la página dice «Registration is disabled. Please contact your site administrator.»; el servidor lo rechaza
  ¿existe «cualquiera»?: False

== 3.2 · Lo correcto: ROOT_URL con la dirección por la que se llega de verdad ==
  clone_url: http://forgejo:3000/duena/tienda.git
```

## Lección 4 · Woodpecker

```
== 4.1 · Woodpecker: entrar con la cuenta de Forgejo y activar el repositorio ==
  login por OAuth: hecho · repositorio duena/tienda activado en Woodpecker (HTTP 200)
  webhooks en Forgejo: 1 · apunta a http://woodpecker:8000/api/hook

== 4.2 · La trampa: el primer push, y el pipeline que nunca llega ==
  push hecho · 20 s después, pipelines en Woodpecker: 0
  ni Woodpecker ni el push dan error: el webhook se queda en Forgejo
  en el registro de Forgejo (docker logs forgejo):
    webhook can only call allowed HTTP servers (check your webhook.ALLOWED_HOST_LIST setting), deny 'woodpecker(192.168.16.3:8000)'
$ (Forgejo reiniciado con FORGEJO__webhook__ALLOWED_HOST_LIST=private)
```

## Lecciones 4 y 5 · El pipeline y el secreto

```
== 4.3 · Lo correcto: ALLOWED_HOST_LIST con la red de Woodpecker, y otro push ==
  pipeline #1 · evento push · estado success
    + echo "pruebas de la tienda, todo bien"
    pruebas de la tienda, todo bien

== 5.1 · Un secreto en Woodpecker, y el log que lo tapa ==
  pipeline #2 · estado success
    + echo "la clave es $CLAVE"
    la clave es ********
    + echo "$CLAVE" | base64
    bGEtZGUtbG9zLXBhZ29zCg==
    + echo "$CLAVE" | rev
    sogap-sol-ed-al
  el log solo tapa el texto exacto: en base64 o al revés, la clave sale entera

== 5.2 · Lo correcto: el secreto, solo para la imagen que lo necesita ==
  clave_pagos limitada a la imagen: ['woodpeckerci/plugin-docker-buildx']
  pipeline #3 · estado error
    secret "clave_pagos" is only allowed to be used by plugins (a filter has been set on the secret). Note: Image filters do not work for normal steps
  pasos que llegaron a ejecutarse: 0
  el paso con alpine ya no recibe la clave: ni siquiera arranca
```
