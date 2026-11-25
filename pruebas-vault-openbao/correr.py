# -*- coding: utf-8 -*-
"""Banco del vídeo 410 «¿Vale la pena Vault (u OpenBao) en 2027?». Todo en Docker, modo dev (token raíz «root»).

    python correr.py      -> SALIDA.md (literal: lo que sale en pantalla se copia de aquí)
"""
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
NET = "lab-vault"
OUT = []


def sh(cmd, check=False):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (p.stdout + p.stderr).strip(), p.returncode


def bloque(titulo, mostrado, cmd):
    salida, rc = sh(cmd)
    OUT.append(f"### {titulo}\n\n`$ {mostrado}`\n\n```\n{salida}\n```\n(código de salida {rc})\n")
    print(f"[{rc}] {titulo}")
    return salida, rc


def V(args, srv="vault"):   # CLI de Vault dentro de su contenedor
    return f"docker exec -e VAULT_ADDR=http://127.0.0.1:8200 -e VAULT_TOKEN=root {srv} vault {args}"


def O(args):                # CLI de OpenBao dentro de su contenedor
    return f"docker exec -e BAO_ADDR=http://127.0.0.1:8200 -e BAO_TOKEN=root openbao bao {args}"


def main():
    for c in ("vault", "openbao", "pg"):
        sh(f"docker rm -f {c}")
    sh(f"docker network rm {NET}")
    sh(f"docker network create {NET}")
    OUT.append(f"# SALIDA — Vault contra OpenBao (vídeo 410)\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. "
               "Modo dev, token raíz `root`, todo en Docker.\n")

    OUT.append("## 1 · Arrancar los dos\n")
    sh(f"docker run -d --name vault --network {NET} --cap-add IPC_LOCK -e VAULT_DEV_ROOT_TOKEN_ID=root hashicorp/vault:latest")
    sh(f"docker run -d --name openbao --network {NET} --cap-add IPC_LOCK -e BAO_DEV_ROOT_TOKEN_ID=root openbao/openbao:latest server -dev -dev-listen-address=0.0.0.0:8200")
    sh(f"docker run -d --name pg --network {NET} -e POSTGRES_PASSWORD=pgroot postgres:17-alpine")
    time.sleep(8)
    bloque("versión de Vault", "vault version", V("version"))
    bloque("versión de OpenBao", "bao version", O("version"))
    bloque("tamaño de las imágenes", "docker image inspect -f {{.Size}}",
           "docker image inspect -f \"hashicorp/vault:latest {{.Size}}\" hashicorp/vault:latest && docker image inspect -f \"openbao/openbao:latest {{.Size}}\" openbao/openbao:latest")

    OUT.append("## 2 · Los mismos comandos\n")
    bloque("Vault: guardar y leer un secreto", "vault kv put secret/app clave=s3cr3t; vault kv get -field=clave secret/app",
           V("kv put secret/app clave=s3cr3t") + " && " + V("kv get -field=clave secret/app"))
    bloque("OpenBao: lo mismo", "bao kv put secret/app clave=s3cr3t; bao kv get -field=clave secret/app",
           O("kv put secret/app clave=s3cr3t") + " && " + O("kv get -field=clave secret/app"))
    bloque("el CLI de Vault hablando con OpenBao", "VAULT_ADDR=http://openbao:8200 vault kv get -field=clave secret/app",
           "docker exec -e VAULT_ADDR=http://openbao:8200 -e VAULT_TOKEN=root vault vault kv get -field=clave secret/app")

    OUT.append("## 3 · Namespaces\n")
    bloque("Vault (sin licencia Enterprise)", "vault namespace create equipo-a", V("namespace create equipo-a"))
    bloque("OpenBao", "bao namespace create equipo-a; bao namespace list", O("namespace create equipo-a") + " && " + O("namespace list"))

    OUT.append("## 4 · Credenciales dinámicas contra Postgres (OpenBao)\n")
    bloque("activar el motor de bases de datos", "bao secrets enable database", O("secrets enable database"))
    bloque("conectar con Postgres", "bao write database/config/pg plugin_name=postgresql-database-plugin ...",
           O('write database/config/pg plugin_name=postgresql-database-plugin allowed_roles=app '
             '"connection_url=postgresql://{{username}}:{{password}}@pg:5432/postgres?sslmode=disable" username=postgres password=pgroot'))
    bloque("un rol que crea usuarios de 1 hora", "bao write database/roles/app ... default_ttl=1h",
           O('write database/roles/app db_name=pg default_ttl=1h max_ttl=24h '
             '"creation_statements=CREATE ROLE \\"{{name}}\\" WITH LOGIN PASSWORD \'{{password}}\' VALID UNTIL \'{{expiration}}\';"'))
    cred, _ = bloque("pedir una credencial", "bao read database/creds/app", O("read -format=json database/creds/app"))
    usuario = cred.split('"username":')[1].split('"')[1] if '"username":' in cred else ""
    lease = cred.split('"lease_id":')[1].split('"')[1] if '"lease_id":' in cred else ""
    bloque("el usuario existe en Postgres, con caducidad", "psql -c \"select rolname, rolvaliduntil from pg_roles where rolname like 'v-%'\"",
           "docker exec pg psql -U postgres -tAc \"select rolname, rolvaliduntil from pg_roles where rolname like 'v-%'\"")
    bloque("revocar la credencial", "bao lease revoke <lease_id>", O(f"lease revoke {lease}"))
    bloque("y el usuario ya no existe", "psql -c \"select count(*) from pg_roles where rolname = '<usuario>'\"",
           f"docker exec pg psql -U postgres -tAc \"select count(*) from pg_roles where rolname = '{usuario}'\"")

    OUT.append("## 5 · Lo mismo en Vault\n")
    bloque("Vault: credencial dinámica", "vault secrets enable database; ... vault read database/creds/app",
           V("secrets enable database") + " && " +
           V('write database/config/pg plugin_name=postgresql-database-plugin allowed_roles=app '
             '"connection_url=postgresql://{{username}}:{{password}}@pg:5432/postgres?sslmode=disable" username=postgres password=pgroot') + " && " +
           V('write database/roles/app db_name=pg default_ttl=1h max_ttl=24h '
             '"creation_statements=CREATE ROLE \\"{{name}}\\" WITH LOGIN PASSWORD \'{{password}}\' VALID UNTIL \'{{expiration}}\';"') + " && " +
           V("read -format=json database/creds/app") + " | python -c \"import json,sys; d=json.load(sys.stdin); print('lease_duration', d['lease_duration']); print('username', d['data']['username'])\"")

    OUT.append("## 7 · Políticas: un token que solo lee lo suyo (OpenBao)\n")
    bloque("guardar un segundo secreto", "bao kv put secret/otro clave=privado", O("kv put secret/otro clave=privado") + " && echo ok")
    pol = AQUI / "_solo-app.hcl"
    pol.write_text('path "secret/data/app" { capabilities = ["read"] }\n', encoding="utf-8")
    sh(f'docker cp "{pol}" openbao:/tmp/solo-app.hcl')
    bloque("la política", "cat solo-app.hcl", "docker exec openbao cat /tmp/solo-app.hcl")
    bloque("cargarla", "bao policy write solo-app solo-app.hcl", O("policy write solo-app /tmp/solo-app.hcl"))
    tok, _ = sh(O("token create -policy=solo-app -ttl=15m -field=token"))
    tok = tok.strip()
    bloque("un token con esa política, de 15 minutos", "bao token create -policy=solo-app -ttl=15m", f"echo {tok[:8]}...")
    T = lambda a: f"docker exec -e BAO_ADDR=http://127.0.0.1:8200 -e BAO_TOKEN={tok} openbao bao {a}"
    bloque("leer lo suyo", "BAO_TOKEN=<token> bao kv get -field=clave secret/app", T("kv get -field=clave secret/app"))
    bloque("leer lo de otro", "BAO_TOKEN=<token> bao kv get secret/otro", T("kv get secret/otro"))

    OUT.append("## 8 · Cifrar sin tener la clave: el motor transit (OpenBao)\n")
    bloque("activarlo y crear una clave", "bao secrets enable transit; bao write -f transit/keys/pagos",
           O("secrets enable transit") + " && " + O("write -f transit/keys/pagos") + " && echo clave creada")
    cif, _ = bloque("cifrar un número de tarjeta de prueba", "bao write transit/encrypt/pagos plaintext=<4111111111111111 en base64>",
                    O("write -field=ciphertext transit/encrypt/pagos plaintext=NDExMTExMTExMTExMTExMQ=="))
    plano, _ = sh(O(f"write -field=plaintext transit/decrypt/pagos ciphertext={cif.strip()}"))
    import base64
    OUT.append(f"### descifrarlo\n\n`$ bao write transit/decrypt/pagos ciphertext=<lo de arriba> | base64 -d`\n\n```\n"
               f"{base64.b64decode(plano.strip()).decode()}\n```\n")
    bloque("y la clave, ¿se puede sacar?", "bao read transit/export/encryption-key/pagos", O("read transit/export/encryption-key/pagos"))

    OUT.append("## 9 · Auditoría: quién leyó qué\n")
    bloque("OpenBao: activarla por la API", "bao audit enable file file_path=/tmp/audit.log",
           O("audit enable file file_path=/tmp/audit.log"))
    bloque("Vault: lo mismo", "vault audit enable file file_path=/tmp/audit.log", V("audit enable file file_path=/tmp/audit.log"))
    sh(V("kv get -field=clave secret/app"))
    bloque("Vault: leer el secreto y mirar el registro", "tail -1 /tmp/audit.log (tipo, ruta, valor)",
           "docker exec vault sh -c \"tail -1 /tmp/audit.log\" | python -c \"import json,sys; d=json.loads(sys.stdin.read()); "
           "print('tipo:', d['type']); print('ruta:', d['request']['path']); print('valor:', d['response']['data']['data']['clave'])\"")

    OUT.append("## 10 · Renovar una credencial dinámica (OpenBao)\n")
    cred2, _ = sh(O("read -format=json database/creds/app"))
    import json as _j
    lid = _j.loads(cred2)["lease_id"]
    bloque("renovarla por 2 horas", "bao lease renew -increment=2h <lease_id>", O(f"lease renew -increment=2h {lid}") + " | findstr lease_duration")
    bloque("pedir más del máximo (24 h)", "bao lease renew -increment=48h <lease_id>", O(f"lease renew -increment=48h {lid}") + " | findstr lease_duration")

    OUT.append("## 6 · Lo que pesa en reposo\n")
    time.sleep(5)
    bloque("memoria", "docker stats --no-stream", "docker stats --no-stream --format \"{{.Name}} {{.MemUsage}}\" vault openbao")

    (AQUI / "SALIDA.md").write_text("\n".join(OUT), encoding="utf-8")
    for c in ("vault", "openbao", "pg"):
        sh(f"docker rm -f {c}")
    sh(f"docker network rm {NET}")
    print("ok SALIDA.md")


if __name__ == "__main__":
    main()
