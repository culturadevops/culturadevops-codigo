# SALIDA — Vault contra OpenBao (vídeo 410)

Generado 2026-10-13 20:47 UTC con `python correr.py`. Modo dev, token raíz `root`, todo en Docker.

## 1 · Arrancar los dos

### versión de Vault

`$ vault version`

```
Vault v2.1.2 (76fdd6587523c4c6cb079635075e019714d23470), built 2026-10-06T15:17:37Z
```
(código de salida 0)

### versión de OpenBao

`$ bao version`

```
OpenBao v2.7.1 (a5db72cef75c24b920ade02065b18dd8eb666bac), committed 2026-10-01T15:32:54Z
```
(código de salida 0)

### tamaño de las imágenes

`$ docker image inspect -f {{.Size}}`

```
hashicorp/vault:latest 193304949
openbao/openbao:latest 80058255
```
(código de salida 0)

## 2 · Los mismos comandos

### Vault: guardar y leer un secreto

`$ vault kv put secret/app clave=s3cr3t; vault kv get -field=clave secret/app`

```
= Secret Path =
secret/data/app

======= Metadata =======
Key                Value
---                -----
created_time       2026-10-13T20:47:40.039946802Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1
s3cr3t
```
(código de salida 0)

### OpenBao: lo mismo

`$ bao kv put secret/app clave=s3cr3t; bao kv get -field=clave secret/app`

```
= Secret Path =
secret/data/app

======= Metadata =======
Key                Value
---                -----
created_time       2026-10-13T20:47:40.312578108Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1
s3cr3t
```
(código de salida 0)

### el CLI de Vault hablando con OpenBao

`$ VAULT_ADDR=http://openbao:8200 vault kv get -field=clave secret/app`

```
s3cr3t
```
(código de salida 0)

## 3 · Namespaces

### Vault (sin licencia Enterprise)

`$ vault namespace create equipo-a`

```
Error creating namespace: Error making API request.

URL: PUT http://127.0.0.1:8200/v1/sys/namespaces/equipo-a
Code: 404. Errors:

* enterprise-only feature
```
(código de salida 2)

### OpenBao

`$ bao namespace create equipo-a; bao namespace list`

```
Key                Value
---                -----
custom_metadata    map[]
id                 uIrGNU
locked             false
path               equipo-a/
tainted            false
uuid               1417c6c8-3a7a-bfba-4461-ac93398c680e
Keys
----
equipo-a/
```
(código de salida 0)

## 4 · Credenciales dinámicas contra Postgres (OpenBao)

### activar el motor de bases de datos

`$ bao secrets enable database`

```
Success! Enabled the database secrets engine at: database/
```
(código de salida 0)

### conectar con Postgres

`$ bao write database/config/pg plugin_name=postgresql-database-plugin ...`

```
Success! Data written to: database/config/pg
```
(código de salida 0)

### un rol que crea usuarios de 1 hora

`$ bao write database/roles/app ... default_ttl=1h`

```
Success! Data written to: database/roles/app
```
(código de salida 0)

### pedir una credencial

`$ bao read database/creds/app`

```
{
  "request_id": "1c93c48c-7f43-0f1d-de14-221839e0eaaf",
  "lease_id": "database/creds/app/GBYhRjt8wtqwRlje9BMBJ4w9",
  "lease_duration": 3600,
  "renewable": true,
  "data": {
    "password": "xq-n6oRJnOaeVFvh6fF7",
    "username": "v-token-app-QONPemKVstk9u727So42-1791924461"
  },
  "warnings": null
}
```
(código de salida 0)

### el usuario existe en Postgres, con caducidad

`$ psql -c "select rolname, rolvaliduntil from pg_roles where rolname like 'v-%'"`

```
v-token-app-QONPemKVstk9u727So42-1791924461|2026-10-13 21:47:46+00
```
(código de salida 0)

### revocar la credencial

`$ bao lease revoke <lease_id>`

```
All revocation operations queued successfully!
```
(código de salida 0)

### y el usuario ya no existe

`$ psql -c "select count(*) from pg_roles where rolname = '<usuario>'"`

```
0
```
(código de salida 0)

## 5 · Lo mismo en Vault

### Vault: credencial dinámica

`$ vault secrets enable database; ... vault read database/creds/app`

```
Success! Enabled the database secrets engine at: database/
Success! Data written to: database/config/pg
Success! Data written to: database/roles/app
lease_duration 3600
username v-token-app-3Po4tGBDNINzJQuHtmkn-1791924462
```
(código de salida 0)

## 7 · Políticas: un token que solo lee lo suyo (OpenBao)

### guardar un segundo secreto

`$ bao kv put secret/otro clave=privado`

```
== Secret Path ==
secret/data/otro

======= Metadata =======
Key                Value
---                -----
created_time       2026-10-13T20:47:42.852474914Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1
ok
```
(código de salida 0)

### la política

`$ cat solo-app.hcl`

```
path "secret/data/app" { capabilities = ["read"] }
```
(código de salida 0)

### cargarla

`$ bao policy write solo-app solo-app.hcl`

```
Success! Uploaded policy: solo-app
```
(código de salida 0)

### un token con esa política, de 15 minutos

`$ bao token create -policy=solo-app -ttl=15m`

```
s.0iaZUV...
```
(código de salida 0)

### leer lo suyo

`$ BAO_TOKEN=<token> bao kv get -field=clave secret/app`

```
s3cr3t
```
(código de salida 0)

### leer lo de otro

`$ BAO_TOKEN=<token> bao kv get secret/otro`

```
Error reading secret/data/otro: Error making API request.

URL: GET http://127.0.0.1:8200/v1/secret/data/otro
Code: 403. Errors:

* 1 error occurred:
	* permission denied
```
(código de salida 2)

## 8 · Cifrar sin tener la clave: el motor transit (OpenBao)

### activarlo y crear una clave

`$ bao secrets enable transit; bao write -f transit/keys/pagos`

```
Success! Enabled the transit secrets engine at: transit/
Key                       Value
---                       -----
allow_plaintext_backup    false
auto_rotate_period        0s
deletion_allowed          false
derived                   false
exportable                false
imported_key              false
keys                      map[1:1791924463]
latest_version            1
min_available_version     0
min_decryption_version    1
min_encryption_version    0
name                      pagos
soft_deleted              false
supports_decryption       true
supports_derivation       true
supports_encryption       true
supports_signing          false
type                      aes256-gcm96
clave creada
```
(código de salida 0)

### cifrar un número de tarjeta de prueba

`$ bao write transit/encrypt/pagos plaintext=<4111111111111111 en base64>`

```
vault:v1:nZ8d/L+KgKb32SHCZggpmB/B1VAx299O/77dqh8qy0xUdBcwPAjUq+I/BZw=
```
(código de salida 0)

### descifrarlo

`$ bao write transit/decrypt/pagos ciphertext=<lo de arriba> | base64 -d`

```
4111111111111111
```

### y la clave, ¿se puede sacar?

`$ bao read transit/export/encryption-key/pagos`

```
Error reading transit/export/encryption-key/pagos: Error making API request.

URL: GET http://127.0.0.1:8200/v1/transit/export/encryption-key/pagos
Code: 400. Errors:

* private key material is not exportable
```
(código de salida 2)

## 9 · Auditoría: quién leyó qué

### OpenBao: activarla por la API

`$ bao audit enable file file_path=/tmp/audit.log`

```
Error enabling audit device: Error making API request.

URL: PUT http://127.0.0.1:8200/v1/sys/audit/file
Code: 400. Errors:

* cannot enable audit device via API; use declarative, config-based audit device management instead
```
(código de salida 2)

### Vault: lo mismo

`$ vault audit enable file file_path=/tmp/audit.log`

```
Success! Enabled the file audit device at: file/
```
(código de salida 0)

### Vault: leer el secreto y mirar el registro

`$ tail -1 /tmp/audit.log (tipo, ruta, valor)`

```
tipo: response
ruta: secret/data/app
valor: hmac-sha256:fd03196651f4ed7671832e3369b54d3e527a254440f5b550f203908a03096322
```
(código de salida 0)

## 10 · Renovar una credencial dinámica (OpenBao)

### renovarla por 2 horas

`$ bao lease renew -increment=2h <lease_id>`

```
lease_duration     2h
```
(código de salida 0)

### pedir más del máximo (24 h)

`$ bao lease renew -increment=48h <lease_id>`

```
lease_duration     24h
WARNING! The following warnings were returned from OpenBao:

  * TTL of "48h" exceeded the effective max_ttl of "24h"; TTL value is capped
  accordingly
```
(código de salida 0)

## 6 · Lo que pesa en reposo

### memoria

`$ docker stats --no-stream`

```
vault 37.49MiB / 15.36GiB
openbao 27.46MiB / 15.36GiB
```
(código de salida 0)
