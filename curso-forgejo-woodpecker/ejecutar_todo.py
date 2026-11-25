# -*- coding: utf-8 -*-
"""ejecutar_todo.py — corre el curso «Tu propio GitHub y tu propio CI» y escribe SALIDA.md.

Todo en Docker, en una red propia (forja-red): Forgejo, el servidor y el agente de Woodpecker, y el
«navegador» del curso (lecciones.py, en la imagen curso-forja-cliente:1). Entre fase y fase se
reinicia Forgejo con otra configuración, que es justo lo que enseña cada lección. Al terminar se
borra todo: contenedores, volúmenes, red, estado.json (tokens de laboratorio).

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
RED = "forja-red"
FORGEJO = "codeberg.org/forgejo/forgejo:13"
WP_SERVER = "woodpeckerci/woodpecker-server:v3"
WP_AGENTE = "woodpeckerci/woodpecker-agent:v3"
CLIENTE = "curso-forja-cliente:1"
CLAVE = "Clave-de-laboratorio-1"
salida = []


def p(t=""):
    print(t)
    salida.append(t)


def run(args):
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    return r.returncode, (r.stdout + r.stderr).strip()


def docker(*a):
    return run(["docker", *a])


def forgejo(volumen_nuevo=False, **config):
    """(Re)arranca Forgejo. `config` son claves FORGEJO__seccion__CLAVE, es decir, su app.ini."""
    docker("rm", "-f", "forgejo")
    if volumen_nuevo:
        docker("volume", "rm", "forja-datos")
    env = ["-e", "FORGEJO__security__INSTALL_LOCK=true"]
    for k, v in config.items():
        env += ["-e", f"FORGEJO__{k}={v}"]
    c, o = docker("run", "-d", "--name", "forgejo", "--hostname", "forgejo", "--network", RED,
                  "-v", "forja-datos:/data", *env, FORGEJO)
    assert c == 0, o
    for _ in range(120):
        c, _ = docker("exec", "forgejo", "wget", "-qO-", "http://127.0.0.1:3000/api/healthz")
        if c == 0:
            return
        time.sleep(0.5)
    raise AssertionError("Forgejo no arranca")


def woodpecker(cliente, secreto):
    docker("rm", "-f", "woodpecker", "woodpecker-agente")
    c, o = docker("run", "-d", "--name", "woodpecker", "--hostname", "woodpecker", "--network", RED,
                  "-e", "WOODPECKER_HOST=http://woodpecker:8000", "-e", "WOODPECKER_FORGEJO=true",
                  "-e", "WOODPECKER_FORGEJO_URL=http://forgejo:3000",
                  "-e", f"WOODPECKER_FORGEJO_CLIENT={cliente}", "-e", f"WOODPECKER_FORGEJO_SECRET={secreto}",
                  "-e", "WOODPECKER_AGENT_SECRET=secreto-de-laboratorio", "-e", "WOODPECKER_ADMIN=duena",
                  "-e", "WOODPECKER_OPEN=true", WP_SERVER)
    assert c == 0, o
    c, o = docker("run", "-d", "--name", "woodpecker-agente", "--network", RED,
                  "-e", "WOODPECKER_SERVER=woodpecker:9000", "-e", "WOODPECKER_AGENT_SECRET=secreto-de-laboratorio",
                  "-e", f"WOODPECKER_BACKEND_DOCKER_NETWORK={RED}",
                  "-v", "//var/run/docker.sock:/var/run/docker.sock", WP_AGENTE)
    assert c == 0, o
    time.sleep(5)


def fase(letra):
    c, o = docker("run", "--rm", "--network", RED, "-v", f"{AQUI.as_posix()}:/curso", "-w", "/curso",
                  "-e", "PYTHONUNBUFFERED=1", CLIENTE, "python", "lecciones.py", letra)
    for l in o.splitlines():
        p(l)
    if c != 0:
        p(f"  [X] la fase {letra} terminó con código {c}")
    return c


def limpiar():
    docker("rm", "-f", "forgejo", "woodpecker", "woodpecker-agente")
    _, o = docker("ps", "-aq", "--filter", "label=wp_uuid")   # los contenedores de los pasos
    for cid in o.split():
        docker("rm", "-f", cid)
    docker("volume", "rm", "forja-datos")
    docker("network", "rm", RED)
    (AQUI / "estado.json").unlink(missing_ok=True)


def main():
    for imagen in (FORGEJO, WP_SERVER, WP_AGENTE, "alpine:3.22"):
        docker("pull", "-q", imagen)
    docker("build", "-q", "-t", CLIENTE, str(AQUI / "cliente"))
    limpiar()
    docker("network", "create", RED)
    _, fv = docker("run", "--rm", FORGEJO, "forgejo", "--version")
    _, wv = docker("run", "--rm", WP_SERVER, "--version")
    _, dv = docker("version", "--format", "{{.Server.Version}}")
    version_fj = re.search(r"forgejo version \S+", fv).group(0)
    cabecera = ["# SALIDA — curso «Tu propio GitHub y tu propio CI: Forgejo y Woodpecker»", "",
                "> Generado por `ejecutar_todo.py`. **No se escribe a mano.**", "",
                f"- fecha: `{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%SZ}`",
                f"- `{version_fj}`",
                f"- `{wv.strip().splitlines()[-1]}`", f"- Docker `{dv.strip()}`"]
    fallos = 0
    try:
        salida.append("\n## Lecciones 1, 2 y 3 · Forgejo recién instalado\n\n```")
        forgejo(volumen_nuevo=True)
        fallos += fase("A") != 0
        salida.append("```\n\n## Lecciones 2 y 3 · Forgejo bien configurado\n\n```")
        forgejo(volumen_nuevo=True, server__ROOT_URL="http://forgejo:3000/", service__DISABLE_REGISTRATION="true")
        c, o = docker("exec", "-u", "git", "forgejo", "forgejo", "admin", "user", "create", "--admin",
                      "--username", "duena", "--password", CLAVE, "--email", "duena@ejemplo.test",
                      "--must-change-password=false")
        p(f"$ forgejo admin user create --admin --username duena ...")
        p(f"  {o.splitlines()[-1] if o else ''}  (código de salida {c})")
        fallos += fase("B") != 0
        salida.append("```\n\n## Lección 4 · Woodpecker\n\n```")
        e = json.loads((AQUI / "estado.json").read_text())
        woodpecker(e["cliente"], e["secreto"])
        fallos += fase("C") != 0
        _, log = docker("logs", "forgejo")
        # Solo el motivo: la línea entera lleva la URL del webhook con su access_token.
        motivos = re.findall(r"webhook can only call allowed HTTP servers.*?deny '[^']*'", log)
        p("  en el registro de Forgejo (docker logs forgejo):")
        p("    " + (motivos[-1] if motivos else "(ninguna línea sobre ALLOWED_HOST_LIST)"))
        forgejo(server__ROOT_URL="http://forgejo:3000/", service__DISABLE_REGISTRATION="true",
                webhook__ALLOWED_HOST_LIST="private")
        p("$ (Forgejo reiniciado con FORGEJO__webhook__ALLOWED_HOST_LIST=private)")
        salida.append("```\n\n## Lecciones 4 y 5 · El pipeline y el secreto\n\n```")
        fallos += fase("D") != 0
        salida.append("```")
    finally:
        limpiar()
    (AQUI / "SALIDA.md").write_bytes(("\n".join(cabecera) + "\n" + "\n".join(salida) + "\n").encode("utf-8"))
    print(f"\n[{'ok' if not fallos else 'X'}] SALIDA.md · {fallos} fases con fallos")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
