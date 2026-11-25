# -*- coding: utf-8 -*-
"""ejecutar_todo.py — corre el curso «Secretos con OpenBao» de principio a fin y escribe SALIDA.md.

Todo en Docker, en esta máquina: un OpenBao en modo dev (lección 1), un OpenBao de verdad con
almacenamiento en fichero (lecciones 2 a 6) y un PostgreSQL (lección 5). Al terminar lo borra todo.
Las claves y los tokens que salen son de laboratorio: se crean y se destruyen en cada ejecución.

    python ejecutar_todo.py
"""
import datetime
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ENV = dict(os.environ, MSYS_NO_PATHCONV="1")
BAO = "openbao/openbao:2.7.1"
PG = "postgres:17-alpine"
RED = "bao-red"
salida = []
estado = {}


def p(t=""):
    print(t)
    salida.append(t)


def titulo(t):
    p("")
    p(f"== {t} ==")


def run(args):
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    return r.returncode, (r.stdout + r.stderr).strip()


def docker(*a):
    return run(["docker", *a])


def bao(*a, token=None, contenedor="bao"):
    """El cliente `bao` dentro del contenedor del servidor."""
    tok = token if token is not None else estado.get("raiz", "")
    return run(["docker", "exec", "-e", "BAO_ADDR=http://127.0.0.1:8200", "-e", f"BAO_TOKEN={tok}",
                contenedor, "bao", *a])


def mostrar(cmd, codigo, out, filtro=None, maximo=8):
    p(f"$ {cmd}")
    lineas = [l for l in out.splitlines() if l.strip()]
    if filtro:
        lineas = [l for l in lineas if re.search(filtro, l)]
    for l in lineas[:maximo]:
        p("  " + l.rstrip())
    p(f"  (código de salida {codigo})")


def corto(s, n=8):
    return s[:n] + "..."


def esperar(contenedor, cmd=("bao", "status"), codigos=(0, 2), segundos=30):
    for _ in range(segundos * 4):
        c, _ = run(["docker", "exec", "-e", "BAO_ADDR=http://127.0.0.1:8200", contenedor, *cmd])
        if c in codigos:
            return
        time.sleep(0.25)
    raise AssertionError(f"{contenedor} no responde")


def desbloquear(n=3):
    for clave in estado["claves"][:n]:
        bao("operator", "unseal", clave, token="")


def preparar():
    limpiar()
    docker("network", "create", RED)
    docker("volume", "create", "bao-datos")
    docker("run", "-d", "--name", "bao", "--network", RED,
           "-v", f"{(AQUI / 'config').as_posix()}:/curso-config:ro",
           "-v", f"{(AQUI / 'politicas').as_posix()}:/politicas:ro",
           "-v", "bao-datos:/openbao/file", "-v", "bao-extra:/openbao/extra",
           BAO, "server", "-config=/curso-config/bao.hcl", "-config=/openbao/extra")
    docker("run", "-d", "--name", "bao-pg", "--network", RED, "-e", "POSTGRES_PASSWORD=admin-de-laboratorio",
           "-e", "POSTGRES_DB=tienda", PG)
    esperar("bao")


def limpiar():
    docker("rm", "-f", "bao", "bao-dev", "bao-pg")
    docker("volume", "rm", "bao-datos", "bao-extra")
    docker("network", "rm", RED)


# ═══════════════════════════════════════════════════════════════════════════════════════════
def leccion_1():
    docker("run", "-d", "--name", "bao-dev", "-e", "BAO_DEV_ROOT_TOKEN_ID=root", BAO,
           "server", "-dev", "-dev-listen-address=0.0.0.0:8200")
    esperar("bao-dev")
    titulo("1.1 · El modo dev: arranca en un segundo y ya funciona")
    c, o = bao("kv", "put", "secret/tienda/db", "clave=s3cr3to-de-laboratorio", token="root", contenedor="bao-dev")
    mostrar("bao kv put secret/tienda/db clave=s3cr3to-de-laboratorio", c, o, filtro=r"Path|version")
    c, o = bao("kv", "get", "-field=clave", "secret/tienda/db", token="root", contenedor="bao-dev")
    mostrar("bao kv get -field=clave secret/tienda/db", c, o)
    c, o = bao("status", token="", contenedor="bao-dev")
    mostrar("bao status", c, o, filtro=r"^(Sealed|Storage Type)")

    titulo("1.2 · La trampa: se reinicia el contenedor")
    docker("restart", "bao-dev")
    esperar("bao-dev")
    c, o = bao("kv", "get", "secret/tienda/db", token="root", contenedor="bao-dev")
    mostrar("bao kv get secret/tienda/db", c, o)
    p("  el modo dev guarda en memoria: el secreto ya no existe, y nadie avisó al reiniciar")
    docker("rm", "-f", "bao-dev")


def leccion_2():
    titulo("2.1 · Un servidor de verdad, recién arrancado")
    c, o = bao("status", token="")
    mostrar("bao status", c, o, filtro=r"^(Initialized|Sealed)")

    titulo("2.2 · bao operator init: 5 claves de desbloqueo, hacen falta 3")
    c, o = bao("operator", "init", "-key-shares=5", "-key-threshold=3", "-format=json", token="")
    assert c == 0, o
    d = json.loads(o)
    estado["claves"] = d["unseal_keys_b64"]
    estado["raiz"] = d["root_token"]
    p("$ bao operator init -key-shares=5 -key-threshold=3")
    for i, k in enumerate(estado["claves"], 1):
        p(f"  Unseal Key {i}: {corto(k)}")
    p(f"  Initial Root Token: {corto(estado['raiz'])}")
    p("  (código de salida 0)")
    p("  se muestran UNA vez: quien ejecuta init las ve todas. Se reparten antes de cerrar la terminal")

    titulo("2.3 · Desbloquear: 3 de las 5")
    for i, clave in enumerate(estado["claves"][:3], 1):
        c, o = bao("operator", "unseal", clave, token="")
        prog = re.search(r"Unseal Progress\s+(\S+)", o)
        sellado = re.search(r"Sealed\s+(\S+)", o)
        p(f"$ bao operator unseal <clave {i}>   -> Sealed {sellado.group(1)}"
          + (f" · progreso {prog.group(1)}" if prog else ""))

    titulo("2.4 · La otra cara: cada reinicio lo vuelve a sellar")
    docker("restart", "bao")
    esperar("bao")
    c, o = bao("status", token="")
    mostrar("bao status   (tras docker restart bao)", c, o, filtro=r"^Sealed")
    c, o = bao("kv", "get", "secret/tienda/db")
    mostrar("bao kv get secret/tienda/db", c, o, filtro=r"^Code|^\* ", maximo=2)
    p("  hasta que tres personas metan su clave, ninguna aplicación lee nada")
    desbloquear()


def leccion_3():
    bao("secrets", "enable", "-path=secret", "kv-v2")
    bao("kv", "put", "secret/tienda/db", "clave=s3cr3to-de-laboratorio")
    bao("kv", "put", "secret/pagos/pasarela", "clave=la-de-los-pagos")
    tokens = {}
    for pol in ("tienda-mal", "tienda-casi", "tienda"):
        bao("policy", "write", pol, f"/politicas/{pol}.hcl")
        c, o = bao("token", "create", f"-policy={pol}", "-field=token")
        tokens[pol] = o.strip()
    estado["tokens"] = tokens

    def probar(pol, ruta):
        c, o = bao("kv", "get", "-field=clave", ruta, token=tokens[pol])
        if c == 0:
            res = o.splitlines()[-1]
        else:
            codigo_http = next((l.split(".")[0] for l in o.splitlines() if l.startswith("Code:")), "")
            motivos = [l.strip()[2:] for l in o.splitlines() if l.strip().startswith("* ")]
            motivo = motivos[-1] if motivos else o.splitlines()[0]  # el último: el de dentro
            res = f"{codigo_http} · {motivo}"
        p(f"  {ruta:<24} -> {res}  (código {c})")

    titulo("3.1 · La trampa: path \"secret/*\"")
    p("$ política tienda-mal: " + " ".join((AQUI / "politicas/tienda-mal.hcl").read_text(encoding="utf-8").split("\n", 1)[1].split()))
    probar("tienda-mal", "secret/tienda/db")
    probar("tienda-mal", "secret/pagos/pasarela")
    p("  la tienda lee la clave de los pagos, y nadie se entera: no es un error, es la política")

    titulo("3.2 · La que parece bien: path \"secret/tienda/*\"")
    probar("tienda-casi", "secret/tienda/db")
    p("  403 en su propio secreto: el KV v2 guarda en secret/data/tienda/..., no en secret/tienda/...")

    titulo("3.3 · Lo correcto: path \"secret/data/tienda/*\"")
    probar("tienda", "secret/tienda/db")
    probar("tienda", "secret/pagos/pasarela")


def leccion_4():
    titulo("4.1 · La trampa: el token raíz dentro de la aplicación")
    c, o = bao("token", "lookup")
    mostrar("bao token lookup   (con el token raíz)", c, o, filtro=r"^(policies|ttl|expire_time)\s")
    p("  no caduca y puede con todo: si se filtra, se filtra todo, para siempre")

    titulo("4.2 · Un token normal: caduca, pero tarde")
    c, o = bao("token", "lookup", token=estado["tokens"]["tienda"])
    mostrar("bao token lookup   (bao token create -policy=tienda)", c, o, filtro=r"^(policies|ttl)\s")
    p("  768 h son 32 días: un token filtrado sirve un mes")

    titulo("4.3 · Lo correcto: AppRole, con su TTL y un secret_id de un solo uso")
    bao("auth", "enable", "approle")
    bao("write", "auth/approle/role/tienda", "token_policies=tienda", "token_ttl=1h", "token_max_ttl=4h",
        "secret_id_ttl=10m", "secret_id_num_uses=1")
    _, rid = bao("read", "-field=role_id", "auth/approle/role/tienda/role-id")
    _, sid = bao("write", "-f", "-field=secret_id", "auth/approle/role/tienda/secret-id")
    rid, sid = rid.strip(), sid.strip()
    c, o = bao("write", "-format=json", "auth/approle/login", f"role_id={rid}", f"secret_id={sid}", token="")
    tok = json.loads(o)["auth"] if c == 0 else {}
    p("$ bao write auth/approle/login role_id=... secret_id=...")
    p(f"  token con políticas {tok.get('policies')} · dura {tok.get('lease_duration')} s (1 h) · código {c}")
    c, o = bao("write", "auth/approle/login", f"role_id={rid}", f"secret_id={sid}", token="")
    mostrar("bao write auth/approle/login role_id=... secret_id=...   (el mismo secret_id, otra vez)", c, o,
            filtro=r"^Code|^\* ", maximo=2)


def psql(usuario, clave, *sql):
    args = ["docker", "exec", "-e", f"PGPASSWORD={clave}", "bao-pg", "psql", "-h", "127.0.0.1", "-U", usuario,
            "-d", "tienda", "-At"]
    for s in sql:
        args += ["-c", s]
    return run(args)


def leccion_5():
    run(["docker", "exec", "bao-pg", "psql", "-U", "postgres", "-d", "tienda", "-qc",
         "create table pedidos(id int); insert into pedidos select generate_series(1, 100);"])
    bao("secrets", "enable", "database")
    c, o = bao("write", "database/config/tienda", "plugin_name=postgresql-database-plugin",
               "allowed_roles=lector",
               "connection_url=postgresql://{{username}}:{{password}}@bao-pg:5432/tienda?sslmode=disable",
               "username=postgres", "password=admin-de-laboratorio")
    assert c == 0, o
    bao("write", "database/roles/lector", "db_name=tienda", "default_ttl=10s", "max_ttl=1m",
        "creation_statements=CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' "
        "VALID UNTIL '{{expiration}}'; GRANT SELECT ON pedidos TO \"{{name}}\";")

    titulo("5.1 · Credenciales que nacen al pedirlas (aquí, con 10 s de vida)")
    c, o = bao("read", "-format=json", "database/creds/lector")
    assert c == 0, o
    d = json.loads(o)
    usuario, clave = d["data"]["username"], d["data"]["password"]
    p("$ bao read database/creds/lector")
    p(f"  username {usuario[:24]}... · lease_duration {d['lease_duration']} s")
    c, o = psql(usuario, clave, "select count(*) from pedidos")
    p(f"  la aplicación arranca y consulta: {o} pedidos (código {c})")

    titulo("5.2 · La trampa: la aplicación que lee la credencial una vez, al arrancar")
    t0 = time.time()
    time.sleep(15)
    c, o = psql(usuario, clave, "select count(*) from pedidos")
    p(f"  a los {time.time() - t0:.0f} s, la misma credencial:")
    p("  " + o.splitlines()[-1].strip() + f"  (código {c})")
    c, o = run(["docker", "exec", "bao-pg", "psql", "-U", "postgres", "-d", "tienda", "-Atc",
                f"select count(*) from pg_roles where rolname = '{usuario}'"])
    p(f"  ese usuario en PostgreSQL: {o} filas. OpenBao lo borró al caducar")
    p("  en una prueba corta no se ve; con un TTL de 1 h, la aplicación cae a la hora de arrancar")

    titulo("5.3 · Lo correcto: renovar antes de que caduque, o volver a pedir")
    c, o = bao("read", "-format=json", "database/creds/lector")
    d = json.loads(o)
    c, o = bao("lease", "renew", "-format=json", d["lease_id"])
    r = json.loads(o) if c == 0 else {}
    p("$ bao lease renew <lease_id>")
    p(f"  lease_duration {r.get('lease_duration')} s · se puede renovar hasta max_ttl (1 min); después, credencial nueva")
    p("  bao agent lo hace solo: renueva, y cuando ya no se puede, pide otra y la reescribe")


def leccion_6():
    titulo("6.1 · La trampa: ¿quién leyó la clave de los pagos?")
    bao("kv", "get", "secret/pagos/pasarela", token=estado["tokens"]["tienda-mal"])
    c, o = bao("audit", "list")
    mostrar("bao audit list", c, o, maximo=2)
    p("  la tienda la leyó en la lección 3, y no queda rastro en ningún sitio")

    titulo("6.2 · Activarla como dicen los tutoriales: por la API")
    c, o = bao("audit", "enable", "file", "file_path=/openbao/logs/auditoria.log")
    mostrar("bao audit enable file file_path=/openbao/logs/auditoria.log", c, o, filtro=r"^Code|^\* ", maximo=2)
    p("  OpenBao 2.7 ya no lo permite: la auditoría se declara en la configuración")

    titulo("6.3 · Lo correcto: declararla, y recargar con SIGHUP (sin reiniciar, sin sellar)")
    bloque = ('audit "file" "auditoria" {\n  options {\n    file_path = "/openbao/logs/auditoria.log"\n'
              '  }\n}\n')
    run(["docker", "exec", "-u", "0", "bao", "sh", "-c",
         f"printf '%s' '{bloque}' > /openbao/extra/auditoria.hcl && chown openbao /openbao/extra/auditoria.hcl"])
    for l in bloque.strip().splitlines():
        p("  " + l)
    docker("kill", "-s", "HUP", "bao")
    time.sleep(2)
    c, o = bao("audit", "list")
    mostrar("bao audit list   (tras docker kill -s HUP bao)", c, o, maximo=3)
    c, o = bao("status", token="")
    p("  " + next(l for l in o.splitlines() if l.startswith("Sealed")))
    bao("kv", "get", "secret/pagos/pasarela", token=estado["tokens"]["tienda-mal"])
    _, log = run(["docker", "exec", "bao", "cat", "/openbao/logs/auditoria.log"])
    entradas = [json.loads(l) for l in log.splitlines() if l.strip()]
    lectura = next(e for e in entradas if e.get("type") == "response"
                   and e.get("request", {}).get("path") == "secret/data/pagos/pasarela")
    p(f"  la entrada: ruta {lectura['request']['path']} · políticas {lectura['auth'].get('policies')}")
    valor = lectura["response"]["data"]["data"]["clave"]
    p(f"  el valor leído, en el registro: {valor[:30]}...")
    p(f"  ¿aparece la clave en claro en el fichero?: {'la-de-los-pagos' in log}")

    titulo("6.4 · Buscar quién leyó un valor, sin guardarlo en claro")
    c, o = bao("write", "-field=hash", "sys/audit-hash/auditoria", "input=la-de-los-pagos")
    p("$ bao write sys/audit-hash/auditoria input=la-de-los-pagos")
    p(f"  {o.strip()[:30]}...  ¿es el del registro?: {o.strip() == valor}")


def main():
    for imagen in (BAO, PG):
        docker("pull", "-q", imagen)
    preparar()
    _, v = docker("run", "--rm", BAO, "version")
    _, pgv = docker("run", "--rm", PG, "postgres", "--version")
    _, dv = docker("version", "--format", "{{.Server.Version}}")
    cabecera = ["# SALIDA — curso «Secretos con OpenBao: sin contraseñas en el código»", "",
                "> Generado por `ejecutar_todo.py`. **No se escribe a mano.**", "",
                f"- fecha: `{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%SZ}`",
                f"- `{v.splitlines()[0]}`", f"- `{pgv.strip()}`", f"- Docker `{dv.strip()}`"]
    fallos = 0
    try:
        for n, f in enumerate((leccion_1, leccion_2, leccion_3, leccion_4, leccion_5, leccion_6), 1):
            salida.append(f"\n## Leccion {n}\n\n```")
            try:
                f()
            except Exception as e:  # noqa: BLE001 — un fallo del banco se apunta y se sigue
                p(f"  [X] fallo del banco de pruebas: {type(e).__name__}: {e}")
                fallos += 1
            salida.append("```")
    finally:
        limpiar()
    texto = "\n".join(cabecera) + "\n" + "\n".join(salida) + "\n"
    (AQUI / "SALIDA.md").write_bytes(texto.encode("utf-8"))
    print(f"\n[{'ok' if not fallos else 'X'}] SALIDA.md · {fallos} fallos del banco")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
