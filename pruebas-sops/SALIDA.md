# SALIDA — SOPS (vídeo 330)

Generado 2026-10-07 21:59 UTC con `python correr.py`. Imagen ghcr.io/getsops/sops:v3.13.3-alpine + age.

## 1 · Versiones y claves age

### versiones

`$ sops --version; age --version`

```
sops 3.13.3 (latest)
v1.3.2
```

### mi clave

`$ age-keygen -o /claves/yo.txt`

```
Public key: age195s6h8wxcahsnwklnw6nad2m9hgrkt2u3q3076609xklqxtax56qdwgwte
```

### el archivo de la clave

`$ cat /claves/yo.txt (la privada, recortada)`

```
# created: 2026-10-07T21:59:02Z
# public key: age195s6h8wxcahsnwklnw6nad2m9hgrkt2u3q3076609xklqxtax56qdwgwte
AGE-SECRET-KEY-1FL9CC9…(privada)
```

## 2 · .sops.yaml y el primer cifrado

### .sops.yaml

`$ cat .sops.yaml`

```
creation_rules:
  - path_regex: secretos/.*\.yaml$
    encrypted_regex: ^(password|token)$
    age: age195s6h8wxcahsnwklnw6nad2m9hgrkt2u3q3076609xklqxtax56qdwgwte
```

### el archivo en claro

`$ cat secretos/prod.yaml`

```
db:
  host: db.interna
  port: 5432
  user: app
  password: s3cr3t0-de-produccion
api:
  url: https://pagos.ejemplo.test
  token: tok_live_9f8e7d6c5b4a
```

### cifrar

`$ sops encrypt -i secretos/prod.yaml`

```
codigo=0
```

### el archivo cifrado

`$ cat secretos/prod.yaml`

```
db:
    host: db.interna
    port: 5432
    user: app
    password: ENC[AES256_GCM,data:e8/o4Pj8ugOf+rPRRzkYiFte0Uwv,iv:Rea/RgJk1X2oWa3zuu/dwlQnzZgMt+Og6TVcbnig9fA=,tag:OUJMowgxSFRpKHFdW8/9nQ==,type:str]
api:
    url: https://pagos.ejemplo.test
    token: ENC[AES256_GCM,data:95fS71ZkNmXBX7Y5Nyh/v3K6pIp/,iv:wPyBAN4M748esl/3wiI8rYwglg1gMfszbi8uU/p8P0M=,tag:3EMjX1qBJDhOyQ1mlIEgug==,type:str]
sops:
    age:
        - enc: |
            -----BEGIN AGE ENCRYPTED FILE-----
            YWdlLWVuY3J5cHRpb24ub3JnL3YxCi0+IFgyNTUxOSBKSUNYa0FIR0NNMjdBQXFW
            QlFpM2dKYVUzR0FqZmd0bGNzamFzSHJqblFVClFiWUQ2UmIyLzFBcW5UVEE5NnJB
            RThsTDlYN0didjM3MjI4cHY0cnhFU3MKLS0tIGtrYlJiaDU5REZrNnNvWGVVbkhl
            ZnV5OG5wdU4zbU9UM2RSenJmdG1WYWcKGAmruKsiJoOVD1EJoDLU6Yc3IfBC4+18
            yLcSoBIB3UiZn+ypMBLj2ery1nqvI4mp0TmPK4w6Nt43ForKsp4Jgg==
            -----END AGE ENCRYPTED FILE-----
          recipient: age195s6h8wxcahsnwklnw6nad2m9hgrkt2u3q3076609xklqxtax56qdwgwte
    encrypted_regex: ^(password|token)$
    lastmodified: "2026-10-07T21:59:03Z"
    mac: ENC[AES256_GCM,data:/mB6uXQtFlT83GAOGynlS6xC/kRbiM/vzTKXwKxmH92ZNCHyNAvSMR9rqtbSEI/2X/KcPgDtv88Y7xgzFqSl193tkx/iEONAk+yWeV4S5tvl9oiX3DLV+Z9k2ELpIWkyZrcm+OrWD0bLqbvARK1IqfDPTj5D09lsXwdRF+fH+uk=,iv:gKBrH48YthzA5wnZIprYqQ9STqXy9x9Xoo8OVwNb7O0=,tag:h1LTHY8FsIfgjwghGKmzew==,type:str]
    version: 3.13.3
```

### ¿está el secreto en git?

`$ git grep -c 's3cr3t0' ; git grep -n 'tok_live'`

```
codigo=1
codigo=1
```

## 3 · Descifrar: con la clave y sin ella

### con mi clave

`$ sops decrypt secretos/prod.yaml`

```
db:
    host: db.interna
    port: 5432
    user: app
    password: s3cr3t0-de-produccion
api:
    url: https://pagos.ejemplo.test
    token: tok_live_9f8e7d6c5b4a
```

### un solo valor

`$ sops decrypt --extract '["db"]["password"]' secretos/prod.yaml`

```
s3cr3t0-de-produccion
```

### sin la clave

`$ sops decrypt secretos/prod.yaml`

```
codigo=128
Failed to get the data key required to decrypt the SOPS file.

Group 0: FAILED
  age195s6h8wxcahsnwklnw6nad2m9hgrkt2u3q3076609xklqxtax56qdwgwte: FAILED
    - | failed to load age identities. Errors while loading age
      | identities: failed to open SOPS_AGE_KEY_FILE file: open
      | /claves/no-existe.txt: no such file or directory. Did not
      | find keys in locations 'SOPS_AGE_SSH_PRIVATE_KEY_FILE',
      | 'SOPS_AGE_SSH_PRIVATE_KEY_CMD', '/root/.ssh/id_ed25519',
      | '/root/.ssh/id_rsa', 'SOPS_AGE_KEY', 'SOPS_AGE_KEY_CMD', and
      | '/root/.config/sops/age/keys.txt'.

Recovery failed because no master key was able to decrypt the file. In
order for SOPS to recover the file, at least one key has to be successful,
but none were.
```

## 4 · Cambiar un valor y el diff en git

### sops set

`$ sops set secretos/prod.yaml '["db"]["password"]' '"otra-clave-2026"'`

```
codigo=0
```

### git diff

`$ git diff --stat; git diff`

```
secretos/prod.yaml | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)
diff --git a/secretos/prod.yaml b/secretos/prod.yaml
index 28932e3..742dd4e 100644
--- a/secretos/prod.yaml
+++ b/secretos/prod.yaml
@@ -2,7 +2,7 @@ db:
     host: db.interna
     port: 5432
     user: app
-    password: ENC[AES256_GCM,data:e8/o4Pj8ugOf+rPRRzkYiFte0Uwv,iv:Rea/RgJk1X2oWa3zuu/dwlQnzZgMt+Og6TVcbnig9fA=,tag:OUJMowgxSFRpKHFdW8/9nQ==,type:str]
+    password: ENC[AES256_GCM,data:OeO3EVkBN9+aQPZg619v,iv:tY8r7X1pH9DY9KEMaLyc/dGhm8OXVQ43vPP95vkQPmA=,tag:HQI4Qv2k6RYPUCW2r0gloQ==,type:str]
 api:
     url: https://pagos.ejemplo.test
     token: ENC[AES256_GCM,data:95fS71ZkNmXBX7Y5Nyh/v3K6pIp/,iv:wPyBAN4M748esl/3wiI8rYwglg1gMfszbi8uU/p8P0M=,tag:3EMjX1qBJDhOyQ1mlIEgug==,type:str]
@@ -19,5 +19,5 @@ sops:
           recipient: age195s6h8wxcahsnwklnw6nad2m9hgrkt2u3q3076609xklqxtax56qdwgwte
     encrypted_regex: ^(password|token)$
     lastmodified: "2026-10-07T21:59:03Z"
-    mac: ENC[AES256_GCM,data:/mB6uXQtFlT83GAOGynlS6xC/kRbiM/vzTKXwKxmH92ZNCHyNAvSMR9rqtbSEI/2X/KcPgDtv88Y7xgzFqSl193tkx/iEONAk+yWeV4S5tvl9oiX3DLV+Z9k2ELpIWkyZrcm+OrWD0bLqbvARK1IqfDPTj5D09lsXwdRF+fH+uk=,iv:gKBrH48YthzA5wnZIprYqQ9STqXy9x9Xoo8OVwNb7O0=,tag:h1LTHY8FsIfgjwghGKmzew==,type:str]
+    mac: ENC[AES256_GCM,data:gK8GSVR1NiNMYULNh9EC9r6cZRhnQ04mdJx4pZmvvfiHdCle/qfe5eERF7eS07W08ZE0pCX1QGQ5DnCvW9mmcK9lHgbQM5u2lU031N97KJhZhT5+PkqBNYluXgnaqKZeJO1VhLhcxRohiTo1efqDEEdT0g9YqiEWidtMkPpvPDA=,iv:pmCanbgpQsLEvlJaR/suAznXH+aA1oheJo8Fj/nHGCQ=,tag:SbFwp//hWIvcsQFFKt8YcQ==,type:str]
     version: 3.13.3
```

### cambiar un dato NO secreto

`$ sops set ... '["db"]["host"]' '"db2.interna"'; git diff`

```
-    host: db.interna
+    host: db2.interna
-    lastmodified: "2026-10-07T21:59:03Z"
-    mac: ENC[AES256_GCM,data:gK8GSVR1NiNMYULNh9EC9r6cZRhnQ04mdJx4pZmvvfiHdCle/qfe5eERF7eS07W08ZE0pCX1QGQ5DnCvW9mmcK9lHgbQM5u2lU031N97KJhZhT5+PkqBNYluXgnaqKZeJO1VhLhcxRohiTo1efqDEEdT0g9YqiEWidtMkPpvPDA=,iv:pmCanbgpQsLEvlJaR/suAznXH+aA1oheJo8Fj/nHGCQ=,tag:SbFwp//hWIvcsQFFKt8YcQ==,type:str]
+    lastmodified: "2026-10-07T21:59:04Z"
+    mac: ENC[AES256_GCM,data:nVVn57RriQNEJUKRB8S0Dwarsq5HrFbndMeNHorgHBVQRuJkXemk3OjN1fN0nzk7uS988sWnwSpidhkP5o71meCVQ/id/5b3oCxnmhMSb3FibdXHx4LlKUY70HqaVJvZZzwnGaIpAjqVNSSrj+Bmsx+v+3m/UHP0tX0x9yXfAZ4=,iv:3mQIlX+3e76zwnX/6m5BcBicWToNw5Je8XXAcezKA0Q=,tag:9yLFUAEFdEygJNeRwjL3FQ==,type:str]
```

## 5 · Alguien toca el archivo a mano

### cambiar el puerto con sed (sin sops)

`$ sed -i 's/port: 5432/port: 6543/' secretos/prod.yaml; git diff`

```
-    port: 5432
+    port: 6543
```

### descifrar el archivo tocado

`$ sops decrypt secretos/prod.yaml`

```
codigo=51
MAC mismatch. File has 20CA32F5741EC4CB99AC43922A243C0A46E4670FB51B5B49B0B1EB57AB13725F5FE1A727E7C7C0833C20012E76B8456EB00195A3C4D4D739F7A7859FAFCF1CFA, computed 95BF85D1923C203C8B07782A5E38E07A4742684582BEC6414E21FF63656FCBD2BC0B40558C0731E10D308B738F570AA897726039A4A44D1735D12B5DF3CA0977
```

## 6 · Una compañera: añadir su clave

### ella intenta descifrar

`$ sops decrypt secretos/prod.yaml (con su clave)`

```
Recovery failed because no master key was able to decrypt the file. In
order for SOPS to recover the file, at least one key has to be successful,
but none were.
codigo=128
```

### .sops.yaml con dos destinatarios

`$ cat .sops.yaml`

```
creation_rules:
  - path_regex: secretos/.*\.yaml$
    encrypted_regex: ^(password|token)$
    age: age195s6h8wxcahsnwklnw6nad2m9hgrkt2u3q3076609xklqxtax56qdwgwte,age1x93j97rsxkkfm8tuqnlradyv6j8490np4s8en4nlt0hvugrj6d2q38mxnk
```

### sops updatekeys

`$ sops updatekeys -y secretos/prod.yaml`

```
2026/10/07 21:59:04 Syncing keys for file /repo/secretos/prod.yaml
The following changes will be made to the file's groups:
Group 1
    age195s6h8wxcahsnwklnw6nad2m9hgrkt2u3q3076609xklqxtax56qdwgwte
+++ age1x93j97rsxkkfm8tuqnlradyv6j8490np4s8en4nlt0hvugrj6d2q38mxnk
2026/10/07 21:59:04 File /repo/secretos/prod.yaml synced with new keys
```

### ahora sí

`$ sops decrypt --extract '["api"]["token"]' secretos/prod.yaml (con su clave)`

```
tok_live_9f8e7d6c5b4a
```

### los destinatarios en el archivo

`$ yq '.sops.age[].recipient' secretos/prod.yaml`

```
age195s6h8wxcahsnwklnw6nad2m9hgrkt2u3q3076609xklqxtax56qdwgwte
age1x93j97rsxkkfm8tuqnlradyv6j8490np4s8en4nlt0hvugrj6d2q38mxnk
```

## 7 · Llevarlo a la aplicación sin escribirlo en disco

### cifrar un .env pasando la clave a mano

`$ sops encrypt --age age195s6h8wx… -i secretos/app.env`

```
codigo=1
error loading config: no matching creation rules found
```

### una regla para los .env

`$ cat .sops.yaml`

```
creation_rules:
  - path_regex: secretos/.*\.yaml$
    encrypted_regex: ^(password|token)$
    age: age195s6h8wxcahsnwklnw6nad2m9hgrkt2u3q3076609xklqxtax56qdwgwte,age1x93j97rsxkkfm8tuqnlradyv6j8490np4s8en4nlt0hvugrj6d2q38mxnk
  - path_regex: secretos/.*\.env$
    age: age195s6h8wxcahsnwklnw6nad2m9hgrkt2u3q3076609xklqxtax56qdwgwte,age1x93j97rsxkkfm8tuqnlradyv6j8490np4s8en4nlt0hvugrj6d2q38mxnk
```

### ahora sí

`$ sops encrypt -i secretos/app.env`

```
codigo=0
```

### app.env cifrado (formato dotenv)

`$ cat secretos/app.env`

```
DB_HOST=ENC[AES256_GCM,data:7HpzJBB6Dm+wFj4=,iv:I4pUSSVQzVmwKZke1GGhB6LCHLQ3UJ5E/38PYLem3j0=,tag:Ye94sEDdtbCI0lbU6sL1NQ==,type:str]
DB_PASSWORD=ENC[AES256_GCM,data:wA86LiUZ4qNDrSpU4/aW,iv:qEVEZMMWA45QLMz/c/9XZQtPUHw2d4HBunuzevfEzn8=,tag:PekXFO2uDiT7g+TD6jVdIQ==,type:str]
sops_age__list_0__map_enc=-----BEGIN AGE ENCRYPTED FILE-----\nYWdlLWVuY3J5cHRpb24ub3JnL3YxCi0+IFgyNTUxOSAzM2pRd2hkbnpoeHo2L0to\nVTM0OXhiakpCczRMbWFhTlZvNWljaHdRelY4CmdHRkt2emZZMW1qTXN5SE8yL3or\nbzIvMUlkUHVuUlMxUDNHaFI1YTArcGcKLS0tIHhqd0kzNUg2OEVGWlNJQ0E5M1d1\nbEIzcE1LdjRnRUw2cU9FSnQ0T1pTUW8KOtEvx2B2Gvy1rfaO8wcs0q0wdBRkORTk\n4RYrAC8qiS6cqVU3x8v5Gv/g7JsgY7tkzs5HZ+4RtzxGX6dcVrvGYw==\n-----END AGE ENCRYPTED FILE-----\n
sops_age__list_0__map_recipient=age195s6h8wxcahsnwklnw6nad2m9hgrkt2u3q3076609xklqxtax56qdwgwte
sops_age__list_1__map_enc=-----BEGIN AGE ENCRYPTED FILE-----\nYWdlLWVuY3J5cHRpb24ub3JnL3YxCi0+IFgyNTUxOSA1U3dmcHRVNXAxUUI2akps\nN0ZlUkVFM2VJR3U5MmhxNEFaTllrbnhjMG1VCkMzclMzSjdnRWJHN1ViU0dLc0ZJ\nZm1WR1c1SkJXR2lvK0lKQmdzRFBUL00KLS0tIDZweUN5OStCdmxQQkM2MEhnMWky\nbnpmYlI1cUZwUG51eTFtOEhJSCtiTGcKltGEX5yHuG0g8IomA4vHmF8hcDnptnBu\n3WVja7yjxcb5fwrR1kfXe2CYLPiaVUv7JD3KdUGk+eUBNniq/F0Rig==\n-----END AGE ENCRYPTED FILE-----\n
sops_age__list_1__map_recipient=age1x93j97rsxkkfm8tuqnlradyv6j8490np4s8en4nlt0hvugrj6d2q38mxnk
sops_lastmodified=2026-10-07T21:59:05Z
sops_mac=ENC[AES256_GCM,data:a5wyLN+MfTf70K0+/MuKVfAtYkd64I7vpwJgVIytwULaedL/21mMnRxh+5VBN5lJzSHyovxqw+dO/mKM9Hm/bVZB0B+GgT/jQOnHPMpQZaGgZHgp7F5fDPItllktbGFqW6Vb+E1IhFl5nDnkiutmfoC6xY67ZOISU+V6F9W1DFk=,iv:iHmCIMKTORWWDM4iS/4JnQDY17Eyzn51x5IVJ/6oKQI=,tag:Ib55mYeYfwPVSW6oG3DGzA==,type:str]
sops_unencrypted_suffix=_unencrypted
sops_version=3.13.3
```

### sops exec-env

`$ sops exec-env secretos/app.env 'bash app.sh'`

```
conectando a db2.interna con la contraseña de 15 caracteres
```

### ¿quedó algo en disco?

`$ ls; env | grep DB_`

```
app.sh
secretos
codigo=1
```

## 8 · Rotar la clave de datos

### antes

`$ yq '.sops.lastmodified' secretos/prod.yaml; grep -c ENC`

```
2026-10-07T21:59:04Z
ENC[AES256_GCM,data:OeO3EVkBN9+aQPZg619v
ENC[AES256_GCM,data:95fS71ZkNmXBX7Y5Nyh/v3K6pIp/
```

### sops rotate

`$ sops rotate -i secretos/prod.yaml`

```
codigo=0
```

### después: mismo contenido, otro cifrado

`$ grep -o 'ENC[...' secretos/prod.yaml`

```
ENC[AES256_GCM,data:GqzLDEROrqDdHu9qO838
ENC[AES256_GCM,data:YDCPbZ/eZS+uzw+CJcLn03WyCFIx
otra-clave-2026
```

### historial

`$ git log --oneline`

```
49997de mover la base de datos
9b51941 rotar la contraseña de la base de datos
17a51c7 secretos de producción, cifrados
```
