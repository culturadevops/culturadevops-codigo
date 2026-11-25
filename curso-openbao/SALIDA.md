# SALIDA — curso «Secretos con OpenBao: sin contraseñas en el código»

> Generado por `ejecutar_todo.py`. **No se escribe a mano.**

- fecha: `2026-10-06 19:58:47Z`
- `OpenBao v2.7.1 (a5db72cef75c24b920ade02065b18dd8eb666bac), committed 2026-10-01T15:32:54Z`
- `postgres (PostgreSQL) 17.11`
- Docker `29.6.2`

## Leccion 1

```

== 1.1 · El modo dev: arranca en un segundo y ya funciona ==
$ bao kv put secret/tienda/db clave=s3cr3to-de-laboratorio
  ==== Secret Path ====
  version            1
  (código de salida 0)
$ bao kv get -field=clave secret/tienda/db
  s3cr3to-de-laboratorio
  (código de salida 0)
$ bao status
  Sealed          false
  Storage Type    inmem
  (código de salida 0)

== 1.2 · La trampa: se reinicia el contenedor ==
$ bao kv get secret/tienda/db
  No value found at secret/data/tienda/db
  (código de salida 2)
  el modo dev guarda en memoria: el secreto ya no existe, y nadie avisó al reiniciar
```

## Leccion 2

```

== 2.1 · Un servidor de verdad, recién arrancado ==
$ bao status
  Initialized        false
  Sealed             true
  (código de salida 2)

== 2.2 · bao operator init: 5 claves de desbloqueo, hacen falta 3 ==
$ bao operator init -key-shares=5 -key-threshold=3
  Unseal Key 1: T5jO6yQ3...
  Unseal Key 2: SbBrgPVZ...
  Unseal Key 3: fzsHi95f...
  Unseal Key 4: jqqminfK...
  Unseal Key 5: Q0NB4Qh6...
  Initial Root Token: s.C6xifC...
  (código de salida 0)
  se muestran UNA vez: quien ejecuta init las ve todas. Se reparten antes de cerrar la terminal

== 2.3 · Desbloquear: 3 de las 5 ==
$ bao operator unseal <clave 1>   -> Sealed true · progreso 1/3
$ bao operator unseal <clave 2>   -> Sealed true · progreso 2/3
$ bao operator unseal <clave 3>   -> Sealed false

== 2.4 · La otra cara: cada reinicio lo vuelve a sellar ==
$ bao status   (tras docker restart bao)
  Sealed             true
  (código de salida 2)
$ bao kv get secret/tienda/db
  Code: 503. Errors:
  * Vault is sealed
  (código de salida 2)
  hasta que tres personas metan su clave, ninguna aplicación lee nada
```

## Leccion 3

```

== 3.1 · La trampa: path "secret/*" ==
$ política tienda-mal: path "secret/*" { capabilities = ["read"] }
  secret/tienda/db         -> s3cr3to-de-laboratorio  (código 0)
  secret/pagos/pasarela    -> la-de-los-pagos  (código 0)
  la tienda lee la clave de los pagos, y nadie se entera: no es un error, es la política

== 3.2 · La que parece bien: path "secret/tienda/*" ==
  secret/tienda/db         -> Code: 403 · permission denied  (código 2)
  403 en su propio secreto: el KV v2 guarda en secret/data/tienda/..., no en secret/tienda/...

== 3.3 · Lo correcto: path "secret/data/tienda/*" ==
  secret/tienda/db         -> s3cr3to-de-laboratorio  (código 0)
  secret/pagos/pasarela    -> Code: 403 · permission denied  (código 2)
```

## Leccion 4

```

== 4.1 · La trampa: el token raíz dentro de la aplicación ==
$ bao token lookup   (con el token raíz)
  expire_time         <nil>
  policies            [root]
  ttl                 0s
  (código de salida 0)
  no caduca y puede con todo: si se filtra, se filtra todo, para siempre

== 4.2 · Un token normal: caduca, pero tarde ==
$ bao token lookup   (bao token create -policy=tienda)
  policies            [default tienda]
  ttl                 767h59m59s
  (código de salida 0)
  768 h son 32 días: un token filtrado sirve un mes

== 4.3 · Lo correcto: AppRole, con su TTL y un secret_id de un solo uso ==
$ bao write auth/approle/login role_id=... secret_id=...
  token con políticas ['default', 'tienda'] · dura 3600 s (1 h) · código 0
$ bao write auth/approle/login role_id=... secret_id=...   (el mismo secret_id, otra vez)
  Code: 400. Errors:
  * invalid role or secret ID
  (código de salida 2)
```

## Leccion 5

```

== 5.1 · Credenciales que nacen al pedirlas (aquí, con 10 s de vida) ==
$ bao read database/creds/lector
  username v-root-lector-v0o1AzNzN7... · lease_duration 10 s
  la aplicación arranca y consulta: 100 pedidos (código 0)

== 5.2 · La trampa: la aplicación que lee la credencial una vez, al arrancar ==
  a los 15 s, la misma credencial:
  psql: error: connection to server at "127.0.0.1", port 5432 failed: FATAL:  role "v-root-lector-v0o1AzNzN7rwXTCI1iOb-1791316745" does not exist  (código 2)
  ese usuario en PostgreSQL: 0 filas. OpenBao lo borró al caducar
  en una prueba corta no se ve; con un TTL de 1 h, la aplicación cae a la hora de arrancar

== 5.3 · Lo correcto: renovar antes de que caduque, o volver a pedir ==
$ bao lease renew <lease_id>
  lease_duration 10 s · se puede renovar hasta max_ttl (1 min); después, credencial nueva
  bao agent lo hace solo: renueva, y cuando ya no se puede, pide otra y la reescribe
```

## Leccion 6

```

== 6.1 · La trampa: ¿quién leyó la clave de los pagos? ==
$ bao audit list
  No audit devices are enabled.
  (código de salida 2)
  la tienda la leyó en la lección 3, y no queda rastro en ningún sitio

== 6.2 · Activarla como dicen los tutoriales: por la API ==
$ bao audit enable file file_path=/openbao/logs/auditoria.log
  Code: 400. Errors:
  * cannot enable audit device via API; use declarative, config-based audit device management instead
  (código de salida 2)
  OpenBao 2.7 ya no lo permite: la auditoría se declara en la configuración

== 6.3 · Lo correcto: declararla, y recargar con SIGHUP (sin reiniciar, sin sellar) ==
  audit "file" "auditoria" {
    options {
      file_path = "/openbao/logs/auditoria.log"
    }
  }
$ bao audit list   (tras docker kill -s HUP bao)
  Path          Type    Description
  ----          ----    -----------
  auditoria/    file    n/a
  (código de salida 0)
  Sealed                  false
  la entrada: ruta secret/data/pagos/pasarela · políticas ['default', 'tienda-mal']
  el valor leído, en el registro: hmac-sha256:4be48da0bcd294c2f9...
  ¿aparece la clave en claro en el fichero?: False

== 6.4 · Buscar quién leyó un valor, sin guardarlo en claro ==
$ bao write sys/audit-hash/auditoria input=la-de-los-pagos
  hmac-sha256:4be48da0bcd294c2f9...  ¿es el del registro?: True
```
