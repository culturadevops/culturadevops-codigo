# -*- coding: utf-8 -*-
"""SOPS vs Infisical — banco de pruebas del vídeo 344 (cultura-devops, serie versus).

La MISMA prueba para los dos: el secreto DB_PASSWORD tiene que llegar a app.sh sin escribirse
en disco; luego se cambia, se le quita el acceso a una compañera y se apaga lo que haya que apagar.
  · SOPS:      imagen lab-sops (sops 3.13.3 + age), repo git local con el secreto cifrado.
  · Infisical: su docker-compose.prod.yml oficial (backend + postgres + redis) en :8095, con
               ENCRYPTION_KEY y AUTH_SECRET generados (NO los del .env.example), y su CLI en Docker.

    python correr.py
"""
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
INF = AQUI / "infisical"
API = "http://localhost:8095/api"
CLI = "infisical/cli:latest"
S = "sops-vs"
salida = []
APP = 'echo "conectando con la contraseña de ${#DB_PASSWORD} caracteres: ${DB_PASSWORD:0:3}…"'


def sh(cmd, timeout=900, entrada=None, cwd=None):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout, input=entrada, cwd=cwd)
    return (r.stdout + r.stderr).strip()


def anota(titulo, cmd_txt, texto):
    salida.extend(["", f"### {titulo}", "", f"`$ {cmd_txt}`", "", "```", texto.strip(), "```"])
    print(f"--- {titulo}\n{texto.strip()[:1500]}\n", flush=True)


def xs(script, env=None):
    e = []
    for k, v in (env or {}).items():
        e += ["-e", f"{k}={v}"]
    return sh(["docker", "exec", *e, "-w", "/repo", S, "bash", "-c", script])


def api(metodo, ruta, token, datos=None):
    cmd = ["curl", "-s", "-X", metodo, "-H", f"Authorization: Bearer {token}"]
    if datos is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(datos)]
    r = sh(cmd + [API + ruta])
    try:
        return json.loads(r)
    except ValueError:
        return {"_texto": r[:300]}


def cli(token, *args):
    return sh(["docker", "run", "--rm", "--network", "host", "-e", f"INFISICAL_TOKEN={token}",
               "-e", "INFISICAL_API_URL=http://localhost:8095/api", CLI, *args], timeout=300)


def main():
    YO = {"SOPS_AGE_KEY_FILE": "/claves/yo.txt"}
    ELLA = {"SOPS_AGE_KEY_FILE": "/claves/ella.txt"}

    # ───────────── SOPS
    salida.append("\n## 1 · SOPS: el secreto en el repositorio")
    sh(["docker", "rm", "-f", S])
    sh(["docker", "run", "-d", "--name", S, "lab-sops", "sh", "-c", "mkdir -p /repo /claves && sleep infinity"])
    time.sleep(2)
    xs("git init -q -b main && git config user.email dev@ejemplo.test && git config user.name dev && "
       "age-keygen -o /claves/yo.txt 2>/dev/null && age-keygen -o /claves/ella.txt 2>/dev/null")
    yo, ella = xs("age-keygen -y /claves/yo.txt"), xs("age-keygen -y /claves/ella.txt")
    xs(f"printf 'creation_rules:\\n  - path_regex: .*\\\\.env$\\n    age: {yo},{ella}\\n' > .sops.yaml && "
       "printf 'DB_PASSWORD=s3cr3t0-de-produccion\\n' > app.env && sops encrypt -i app.env && "
       f"printf '%s\\n' '{APP}' > app.sh && git add -A && git commit -qm 'secreto cifrado'", YO)
    anota("lo que necesita SOPS", "ls -la $(which sops) $(which age); servidores",
          xs("ls -la $(which sops) $(which age) | awk '{print $5, $9}'") + "\nservidores: ninguno")
    anota("la app recibe el secreto", "sops exec-env app.env 'bash app.sh'", xs("sops exec-env app.env 'bash app.sh'", YO))

    # ───────────── Infisical
    salida.append("\n## 2 · Infisical: el secreto en un servidor")
    sh(["docker", "compose", "-p", "infisical", "-f", "docker-compose.prod.yml", "down", "-v"], cwd=INF, timeout=300)
    anota("lo que trae el .env.example oficial", "grep -E 'ENCRYPTION_KEY|AUTH_SECRET' .env.example",
          sh(["grep", "-E", "^(ENCRYPTION_KEY|AUTH_SECRET)=", str(INF / ".env.example")]))
    t0 = time.time()
    sh(["docker", "compose", "-p", "infisical", "-f", "docker-compose.prod.yml", "up", "-d"], cwd=INF, timeout=900)
    for _ in range(120):
        if '"Ok"' in sh(["curl", "-s", API + "/status"]):
            break
        time.sleep(2)
    anota("levantar Infisical", "docker compose -f docker-compose.prod.yml up -d",
          sh(["docker", "ps", "--filter", "name=infisical", "--format", "{{.Names}}  {{.Image}}"]) + f"\n(respondiendo en {time.time() - t0:.0f} s)")
    anota("tamaño de las imágenes", "docker image inspect",
          "\n".join(f"{i}: {int(sh(['docker', 'image', 'inspect', i, '--format', '{{.Size}}'])) / 1e6:.0f} MB"
                    for i in ("infisical/infisical:latest", "postgres:14-alpine", "redis")))
    r = json.loads(sh(["curl", "-s", "-H", "Content-Type: application/json", "-d", json.dumps(
        {"email": "dev@ejemplo.test", "password": "Clave-de-prueba-123!", "firstName": "Dev",
         "lastName": "Ops", "organizationName": "tienda"}), API + "/v1/admin/signup"]))
    org = r.get("organization", {}).get("id")
    sin_org = api("POST", "/v1/projects", r.get("token"), {"projectName": "prueba", "type": "secret-manager"})
    tok = json.loads(sh(["curl", "-s", "-X", "POST", "-H", f"Authorization: Bearer {r.get('token')}",
                         "-H", "Content-Type: application/json", "-d", json.dumps({"organizationId": org}),
                         API + "/v3/auth/select-organization"])).get("token")
    anota("crear el administrador por API", "POST /api/v1/admin/signup → POST /api/v3/auth/select-organization",
          f"organización: {org}\ncon el token del registro: {sin_org.get('message')}\ntoken de la organización: {'sí' if tok else 'NO'}")
    pj = api("POST", "/v1/projects", tok, {"projectName": "tienda", "type": "secret-manager"})
    pid = (pj.get("project") or pj).get("id")
    anota("proyecto", "POST /api/v1/projects", json.dumps({"id": pid, "entornos": [e["slug"] for e in (pj.get("project") or pj).get("environments", [])]}))
    sc = api("POST", "/v3/secrets/raw/DB_PASSWORD", tok, {"workspaceId": pid, "environment": "prod",
                                                         "secretValue": "s3cr3t0-de-produccion", "type": "shared"})
    anota("guardar el secreto", "POST /api/v3/secrets/raw/DB_PASSWORD", json.dumps({k: (sc.get("secret") or {}).get(k) for k in ("secretKey", "version", "environment")}))
    ident = api("POST", "/v1/identities", tok, {"name": "app-tienda", "organizationId": org, "role": "no-access"})
    iid = (ident.get("identity") or {}).get("id")
    api("POST", f"/v1/auth/universal-auth/identities/{iid}", tok, {})
    cs = api("POST", f"/v1/auth/universal-auth/identities/{iid}/client-secrets", tok, {"description": "servidor"})
    cid = api("GET", f"/v1/auth/universal-auth/identities/{iid}", tok).get("identityUniversalAuth", {}).get("clientId")
    secreto = cs.get("clientSecret")
    csid = (cs.get("clientSecretData") or {}).get("id")
    api("POST", f"/v1/projects/{pid}/identity-memberships/{iid}", tok, {"role": "viewer"})
    anota("una identidad de máquina para la app", "POST /identities + universal-auth + client-secret + membership (viewer)",
          f"identidad: app-tienda · clientId: {str(cid)[:8]}… · clientSecret: {'sí' if secreto else 'NO'}")
    login = json.loads(sh(["curl", "-s", "-H", "Content-Type: application/json", "-d",
                           json.dumps({"clientId": cid, "clientSecret": secreto}), API + "/v1/auth/universal-auth/login"]))
    at = login.get("accessToken")
    anota("la app inicia sesión", "POST /api/v1/auth/universal-auth/login",
          f"accessToken: {'sí' if at else 'NO'} · caduca en {login.get('expiresIn')} s")
    anota("la app recibe el secreto", f"infisical run --projectId … --env prod -- bash -c '{APP}'",
          cli(at, "run", f"--projectId={pid}", "--env=prod", "--", "sh", "-c",
              'echo "conectando con la contraseña de ${#DB_PASSWORD} caracteres"'))
    time.sleep(3)
    anota("memoria", "docker stats --no-stream", sh(["docker", "stats", "--no-stream", "--format", "{{.Name}} {{.MemUsage}}",
                                                    "infisical-backend", "infisical-db", "infisical-dev-redis"]))
    anota("¿está en claro en la base de datos?", "psql: SELECT … FROM secrets_v2",
          sh(["docker", "exec", "infisical-db", "psql", "-U", "infisical", "-d", "infisical", "-At", "-c",
              "SELECT key, length(\"encryptedValue\"), encode(substring(\"encryptedValue\" from 1 for 12), 'hex') "
              "FROM secrets_v2 LIMIT 3"]) or "(tabla distinta)")

    # ───────────── cambiar el secreto
    salida.append("\n## 3 · Cambiar el secreto")
    xs("sops set app.env '[\"DB_PASSWORD\"]' '\"otra-clave-2026\"' && git commit -qam 'rotar'", YO)
    anota("SOPS", "sops set app.env … ; git commit; (y desplegar el commit)",
          xs("git log --oneline | head -2; sops exec-env app.env 'bash app.sh'", YO))
    api("PATCH", "/v3/secrets/raw/DB_PASSWORD", tok, {"workspaceId": pid, "environment": "prod",
                                                     "secretValue": "otra-clave-2026", "type": "shared"})
    anota("Infisical", "PATCH /api/v3/secrets/raw/DB_PASSWORD; la app vuelve a arrancar",
          cli(at, "run", f"--projectId={pid}", "--env=prod", "--", "sh", "-c",
              'echo "conectando con la contraseña de ${#DB_PASSWORD} caracteres"'))
    ver = api("GET", f"/v1/secret/{(sc.get('secret') or {}).get('id')}/secret-versions", tok)
    anota("versiones guardadas en Infisical", "GET /api/v1/secret/{id}/secret-versions",
          json.dumps([{"version": v.get("version")} for v in (ver.get("secretVersions") or [])]) if isinstance(ver, dict) else str(ver)[:300])

    # ───────────── quitar el acceso
    salida.append("\n## 4 · Quitarle el acceso a la compañera")
    xs(f"sed -i 's|,{ella}||' .sops.yaml && sops updatekeys -y app.env >/dev/null 2>&1 && git commit -qam 'fuera ella'", YO)
    anota("SOPS: ella con el archivo actual", "sops decrypt app.env (con la clave de ella)",
          xs("sops decrypt app.env > /dev/null 2>&1; echo codigo=$?", ELLA))
    anota("SOPS: ella con el commit anterior", "git show HEAD~1:app.env | sops decrypt --input-type dotenv /dev/stdin",
          xs("git show HEAD~1:app.env > /tmp/viejo.env && sops decrypt --input-type dotenv --output-type dotenv /tmp/viejo.env; echo codigo=$?", ELLA))
    api("POST", f"/v1/auth/universal-auth/identities/{iid}/client-secrets/{csid}/revoke", tok, {})
    api("DELETE", f"/v1/projects/{pid}/identity-memberships/{iid}", tok)
    anota("Infisical: quitar la identidad del proyecto", "DELETE /api/v1/projects/{id}/identity-memberships/{identityId}",
          cli(at, "run", f"--projectId={pid}", "--env=prod", "--", "sh", "-c", 'echo "DB_PASSWORD=${DB_PASSWORD}"') + "\n(con el token que ya tenía)")
    anota("Infisical: y volver a iniciar sesión", "POST /api/v1/auth/universal-auth/login (secreto revocado)",
          sh(["curl", "-s", "-H", "Content-Type: application/json", "-d",
              json.dumps({"clientId": cid, "clientSecret": secreto}), API + "/v1/auth/universal-auth/login"])[:300])

    # ───────────── auditoría
    salida.append("\n## 5 · ¿Quién leyó el secreto?")
    al = api("GET", f"/v1/organization/audit-logs?limit=12&offset=0", tok)
    filas = []
    for e in (al.get("auditLogs") or [])[:12]:
        ev = e.get("event", {})
        filas.append(f"{e.get('createdAt', '')[11:19]}  {ev.get('type', ''):<28} {(e.get('actor') or {}).get('type', '')}")
    anota("Infisical: registro de auditoría", "GET /api/v1/organization/audit-logs", "\n".join(filas) or json.dumps(al)[:300])
    anota("SOPS: registro de auditoría", "—", "no hay servidor: quien tiene la clave descifra sin dejar rastro\n(lo que queda es el historial de git de los cambios)")

    # ───────────── el servidor se cae
    salida.append("\n## 6 · Si el servidor de secretos se cae")
    sh(["docker", "stop", "infisical-backend"])
    anota("Infisical apagado", "infisical run … (con un token nuevo no se puede ni pedir)",
          cli(at, "run", f"--projectId={pid}", "--env=prod", "--", "sh", "-c", "echo arrancó"))
    anota("SOPS sin red", "docker network disconnect …; sops exec-env",
          sh(["docker", "network", "disconnect", "bridge", S]) + xs("sops exec-env app.env 'bash app.sh'", YO))

    sh(["docker", "rm", "-f", S])
    sh(["docker", "compose", "-p", "infisical", "-f", "docker-compose.prod.yml", "down", "-v"], cwd=INF, timeout=300)
    cab = ["# SALIDA — SOPS vs Infisical (vídeo 344)", "",
           f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. "
           f"sops 3.13.3 + age; Infisical (docker-compose.prod.yml oficial, infisical/infisical:latest) + {CLI}."]
    (AQUI / "SALIDA.md").write_text("\n".join(cab + salida) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
