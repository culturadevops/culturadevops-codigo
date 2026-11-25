# SALIDA — SOPS vs Infisical (vídeo 344)

Generado 2026-10-07 23:03 UTC con `python correr.py`. sops 3.13.3 + age; Infisical (docker-compose.prod.yml oficial, infisical/infisical:latest) + infisical/cli:latest.

## 1 · SOPS: el secreto en el repositorio

### lo que necesita SOPS

`$ ls -la $(which sops) $(which age); servidores`

```
5108640 /usr/bin/age
52121762 /usr/local/bin/sops
servidores: ninguno
```

### la app recibe el secreto

`$ sops exec-env app.env 'bash app.sh'`

```
conectando con la contraseña de 21 caracteres: s3c…
```

## 2 · Infisical: el secreto en un servidor

### lo que trae el .env.example oficial

`$ grep -E 'ENCRYPTION_KEY|AUTH_SECRET' .env.example`

```
ENCRYPTION_KEY=f13dbc92aaaf86fa7cb0ed8ac3265f47
AUTH_SECRET=5lrMXKKWCVocS/uerPsl7V+TX/aaUaI7iDkgl3tSmLE=
```

### levantar Infisical

`$ docker compose -f docker-compose.prod.yml up -d`

```
infisical-backend  infisical/infisical:latest
infisical-dev-redis  redis
infisical-db  postgres:14-alpine
(respondiendo en 33 s)
```

### tamaño de las imágenes

`$ docker image inspect`

```
infisical/infisical:latest: 613 MB
postgres:14-alpine: 115 MB
redis: 56 MB
```

### crear el administrador por API

`$ POST /api/v1/admin/signup → POST /api/v3/auth/select-organization`

```
organización: 3bcd3d8d-2345-47c9-b9dc-3f69ff1fcde1
con el token del registro: You are not allowed to access this resource
token de la organización: sí
```

### proyecto

`$ POST /api/v1/projects`

```
{"id": "077f293d-8230-4505-99c5-3c2851d9e340", "entornos": ["dev", "staging", "prod"]}
```

### guardar el secreto

`$ POST /api/v3/secrets/raw/DB_PASSWORD`

```
{"secretKey": "DB_PASSWORD", "version": 1, "environment": "prod"}
```

### una identidad de máquina para la app

`$ POST /identities + universal-auth + client-secret + membership (viewer)`

```
identidad: app-tienda · clientId: 9430094d… · clientSecret: sí
```

### la app inicia sesión

`$ POST /api/v1/auth/universal-auth/login`

```
accessToken: sí · caduca en 2592000 s
```

### la app recibe el secreto

`$ infisical run --projectId … --env prod -- bash -c 'echo "conectando con la contraseña de ${#DB_PASSWORD} caracteres: ${DB_PASSWORD:0:3}…"'`

```
conectando con la contraseña de 21 caracteres
[90m2026-10-07T23:03:33Z[0m [32mINF[0m Injecting 1 Infisical secrets into your application process
```

### memoria

`$ docker stats --no-stream`

```
infisical-backend 888.5MiB / 15.36GiB
infisical-db 250.5MiB / 15.36GiB
infisical-dev-redis 11.43MiB / 15.36GiB
```

### ¿está en claro en la base de datos?

`$ psql: SELECT … FROM secrets_v2`

```
DB_PASSWORD|52|1f2d3b6e4f45acabbc0dce85
```

## 3 · Cambiar el secreto

### SOPS

`$ sops set app.env … ; git commit; (y desplegar el commit)`

```
f493b00 rotar
46d9923 secreto cifrado
conectando con la contraseña de 15 caracteres: otr…
```

### Infisical

`$ PATCH /api/v3/secrets/raw/DB_PASSWORD; la app vuelve a arrancar`

```
conectando con la contraseña de 15 caracteres
[90m2026-10-07T23:03:39Z[0m [32mINF[0m Injecting 1 Infisical secrets into your application process
```

### versiones guardadas en Infisical

`$ GET /api/v1/secret/{id}/secret-versions`

```
[]
```

## 4 · Quitarle el acceso a la compañera

### SOPS: ella con el archivo actual

`$ sops decrypt app.env (con la clave de ella)`

```
codigo=128
```

### SOPS: ella con el commit anterior

`$ git show HEAD~1:app.env | sops decrypt --input-type dotenv /dev/stdin`

```
DB_PASSWORD=otra-clave-2026
codigo=0
```

### Infisical: quitar la identidad del proyecto

`$ DELETE /api/v1/projects/{id}/identity-memberships/{identityId}`

```
error: failed to fetch secrets for path "/": CallGetRawSecretsV3 Unsuccessful response [GET http://localhost:8095/api/v4/secrets?environment=prod&expandSecretReferences=true&includeImports=true&includePersonalOverrides=true&projectId=077f293d-8230-4505-99c5-3c2851d9e340&recursive=false&secretPath=%2F] [status-code=401] [request-id=req-cpqa6zgDE7GPaK] [message="Failed to authorize: client secret has been revoked"] [additional-context="Check your credentials or verify you're using the correct domain. Current domain: http://localhost:8095"]
Could not fetch secrets
If you are using a service token to fetch secrets, please ensure it is valid
(con el token que ya tenía)
```

### Infisical: y volver a iniciar sesión

`$ POST /api/v1/auth/universal-auth/login (secreto revocado)`

```
{"reqId":"req-4rjLQ88vd9e3Ar","statusCode":401,"message":"Invalid credentials","error":"UnauthorizedError"}
```

## 5 · ¿Quién leyó el secreto?

### Infisical: registro de auditoría

`$ GET /api/v1/organization/audit-logs`

```
{"auditLogs": []}
```

### SOPS: registro de auditoría

`$ —`

```
no hay servidor: quien tiene la clave descifra sin dejar rastro
(lo que queda es el historial de git de los cambios)
```

## 6 · Si el servidor de secretos se cae

### Infisical apagado

`$ infisical run … (con un token nuevo no se puede ni pedir)`

```
error: failed to fetch secrets for path "/": CallGetRawSecretsV3: Unable to complete api request [err=Get "http://localhost:8095/api/v4/secrets?environment=prod&expandSecretReferences=true&includeImports=true&includePersonalOverrides=true&projectId=077f293d-8230-4505-99c5-3c2851d9e340&recursive=false&secretPath=%2F": dial tcp [::1]:8095: connect: connection refused]
Could not fetch secrets
If you are using a service token to fetch secrets, please ensure it is valid
```

### SOPS sin red

`$ docker network disconnect …; sops exec-env`

```
conectando con la contraseña de 15 caracteres: otr…
```

## 7 · Medido aparte (2026-10-07, misma instalación desde cero)

### tamaño de sops y age

`$ docker run --rm lab-sops sh -c 'ls -la $(command -v sops) $(command -v age)'`

```
sops 52121762 /usr/local/bin/sops
age 5108640 /usr/bin/age
```

### el plan de una instalación propia de Infisical (sin licencia)

`$ GET /api/v1/organizations/{orgId}/plan`

```
{'tier': -1, 'secretVersioning': True, 'pitRecovery': False, 'rbac': False, 'auditLogs': False, 'auditLogsRetentionDays': 0, 'secretRotation': False}
```
