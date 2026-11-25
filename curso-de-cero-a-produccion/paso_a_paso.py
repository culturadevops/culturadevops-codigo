# -*- coding: utf-8 -*-
"""De cero a producción, paso a paso: lo corre entero y escribe SALIDA.md.

Una aplicación pequeña (la tienda del curso de incidentes) desde el repositorio vacío hasta que
atiende tráfico con su certificado, sus alertas y su copia probada. En cada paso, la trampa que no
da error y el curso donde ese trozo está a fondo. «Producción» es el Docker de esta máquina, con
OpenTofu y el proveedor de Docker; el certificado es de una CA propia. Se dice.

    python paso_a_paso.py            # y al terminar lo destruye todo
    python paso_a_paso.py --dejar
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
INFRA = AQUI / "infra"
CERTS = AQUI / "secretos" / "certs"
FRASE, CLAVE = "una-frase-larga-para-el-estado-2026", "clave-de-produccion-9f3"
TF = dict(os.environ, TF_IN_AUTOMATION="1", TF_VAR_frase_estado=FRASE, TF_VAR_clave_db=CLAVE,
          TF_VAR_certs=str(CERTS).replace("\\", "/"), MSYS_NO_PATHCONV="1")
SALIDA = []


def sh(cmd, cwd=AQUI, env=TF, check=False, timeout=900):
    r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout)
    if check and r.returncode != 0:
        raise SystemExit(f"{' '.join(cmd)}:\n{r.stdout[-800:]}{r.stderr[-800:]}")
    return r.returncode, (r.stdout + r.stderr).strip()


def p(t=""):
    print(t, flush=True)
    SALIDA.append(t)


def paso(n, titulo, curso):
    p(f"\n== Paso {n} · {titulo} ==")
    p(f"   (a fondo: {curso})")


def docker_red(*args):
    return ["docker", "run", "--rm", "--network", "capstone-prod", *args]


# ── preparar: lo de una ejecución anterior fuera, certificados e imágenes ───────────────────
sh(["tofu", "destroy", "-auto-approve", "-no-color"], cwd=INFRA)
for c in ("capstone-trafico", "capstone-demo-env"):
    sh(["docker", "rm", "-f", c])
sh(["docker", "volume", "rm", "-f", "capstone-copias", "capstone-datos-db"])
for f in ("terraform.tfstate", "terraform.tfstate.backup"):
    (INFRA / f).unlink(missing_ok=True)
CERTS.mkdir(parents=True, exist_ok=True)
sh(["docker", "run", "--rm", "-v", f"{CERTS}:/c", "-w", "/c", "python:3.13-slim", "sh", "-c",
    'set -e; q(){ "$@" >/dev/null 2>&1; }; '
    'q openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -keyout raiz.key -out raiz.pem -days 3650 '
    '-subj "/CN=CA del capstone" -addext "basicConstraints=critical,CA:TRUE" -addext "keyUsage=critical,keyCertSign,cRLSign"; '
    'q openssl req -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -keyout tienda.key -out tienda.csr -subj "/CN=tienda.prod.test"; '
    'printf "subjectAltName=DNS:tienda.prod.test\\n" > san.ext; '
    'q openssl x509 -req -in tienda.csr -CA raiz.pem -CAkey raiz.key -CAcreateserial -out tienda.pem -days 90 -extfile san.ext; '
    'cp tienda.pem tienda-cadena.pem; chmod 644 *'], check=True)
sh(["docker", "build", "-q", "-t", "capstone-cliente:1", "-f", "herramientas/Dockerfile.cliente", "herramientas"], check=True)
sello = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
_, tv = sh(["tofu", "version"])
_, dv = sh(["docker", "version", "--format", "{{.Server.Version}}"])
p(f"de cero a producción · {sello} · {tv.splitlines()[0]} · Docker {dv}")

# ── 1 · el repositorio ──────────────────────────────────────────────────────────────────────
paso(1, "El repositorio: el secreto que se queda en la historia", "Git por dentro (17-23)")
repo = Path(tempfile.mkdtemp(prefix="capstone-git-"))
g = lambda *a: sh(["git", "-C", str(repo), *a])  # noqa: E731
g("init", "-q", "-b", "main")
g("config", "user.email", "curso@ejemplo.dev"); g("config", "user.name", "Curso")
shutil.copy(AQUI / "app" / "tienda.py", repo)
(repo / ".env").write_text(f"DB_PASSWORD={CLAVE}\n", encoding="utf-8")
g("add", "."); g("commit", "-qm", "primera versión de la tienda")
p("  git add . && git commit   -> se cuela el .env")
g("rm", "-q", ".env"); g("commit", "-qm", "quito el .env")
p("  git rm .env && git commit -> «arreglado»")
_, ls = g("ls-files")
p(f"  git ls-files: {ls.replace(chr(10), ' ')}")
_, hist = g("log", "--all", "--oneline", "-S", CLAVE)
p("  git log -S <la clave>:"); [p(f"    {l}") for l in hist.splitlines()]
_, prim = g("rev-list", "--max-parents=0", "HEAD")
_, viejo = g("show", f"{prim}:.env")
p(f"  git show <primer commit>:.env -> {viejo}")
p("  lo correcto: .gitignore ANTES del primer commit, y si ya se coló, la clave se cambia: está filtrada")

# ── 2 · la imagen ───────────────────────────────────────────────────────────────────────────
paso(2, "La imagen: grande y como root, o pequeña y sin privilegios", "Contenedores por dentro (128)")
for tag, df in (("capstone-tienda:ingenua", "Dockerfile.ingenuo"), ("capstone-tienda:1", "Dockerfile")):
    sh(["docker", "build", "-q", "-t", tag, "-f", f"app/{df}", "app"], check=True)
    _, tam = sh(["docker", "image", "inspect", tag, "--format", "{{.Size}}"])
    _, quien = sh(["docker", "run", "--rm", "--entrypoint", "sh", tag, "-c", "echo $(whoami) uid=$(id -u)"])
    p(f"  {df:20s} {int(tam) / 1e6:7.0f} MB · corre como {quien}")

# ── 3 · la infraestructura y su estado ──────────────────────────────────────────────────────
paso(3, "La infraestructura con OpenTofu, y el estado que guarda la clave", "OpenTofu desde cero (126)")
sin = Path(tempfile.mkdtemp(prefix="capstone-sin-cifrar-"))
texto = (INFRA / "main.tf").read_text(encoding="utf-8")
texto = re.sub(r"\n  encryption \{.*?\n  \}\n", "\n", texto, flags=re.S)       # el mismo, sin cifrar el estado
(sin / "main.tf").write_text(texto, encoding="utf-8")
for f in ("proxy.conf", "prometheus.yml", "alertas.yml"):
    shutil.copy(INFRA / f, sin)
sh(["tofu", "init", "-no-color"], cwd=sin, check=True)
_, ap = sh(["tofu", "apply", "-auto-approve", "-no-color"], cwd=sin, check=True)
p("  sin cifrar: " + next(l for l in ap.splitlines() if "Apply complete" in l))
n = (sin / "terraform.tfstate").read_text(encoding="utf-8").count(CLAVE)
p(f"  la clave, en claro en terraform.tfstate: {n} {'vez' if n == 1 else 'veces'} (y la variable es «sensitive»)")
sh(["tofu", "destroy", "-auto-approve", "-no-color"], cwd=sin, check=True)
sh(["tofu", "init", "-no-color"], cwd=INFRA, check=True)
_, ap = sh(["tofu", "apply", "-auto-approve", "-no-color"], cwd=INFRA, check=True)
p("  con el estado cifrado: " + next(l for l in ap.splitlines() if "Apply complete" in l))
estado = (INFRA / "terraform.tfstate").read_text(encoding="utf-8")
p(f"  la clave en terraform.tfstate: {estado.count(CLAVE)} veces · empieza por: {json.loads(estado)['encrypted_data'][:24]}...")
c, mal = sh(["tofu", "plan", "-no-color"], cwd=INFRA, env=dict(TF, TF_VAR_frase_estado="otra-frase-equivocada-2026"))
p(f"  tofu plan con otra frase: código {c} · {next((l.strip() for l in mal.splitlines() if 'decrypt' in l.lower()), mal.splitlines()[-1])[:90]}")

# ── 4 · los secretos ────────────────────────────────────────────────────────────────────────
paso(4, "Los secretos: lo que enseña docker inspect", "Terraform 2026: variables y secretos (253)")
sh(["docker", "run", "-d", "--name", "capstone-demo-env", "-e", f"POSTGRES_PASSWORD={CLAVE}", "postgres:17"])
_, e = sh(["docker", "inspect", "capstone-demo-env", "--format", "{{range .Config.Env}}{{println .}}{{end}}"])
p("  como variable de entorno:  " + next(l for l in e.splitlines() if "PASSWORD" in l))
sh(["docker", "rm", "-f", "capstone-demo-env"])
_, e = sh(["docker", "inspect", "capstone-db", "--format", "{{range .Config.Env}}{{println .}}{{end}}"])
p("  como fichero (producción): " + next(l for l in e.splitlines() if "PASSWORD" in l))

# ── 5 · red y TLS ───────────────────────────────────────────────────────────────────────────
paso(5, "La red y el certificado: diagnostico.sh, de abajo arriba", "Redes para gente de DevOps (314)")
time.sleep(5)
# La tienda tal cual salió del curso de incidentes, sin do_HEAD: lo que encontró juntar las piezas.
sh(["docker", "build", "-q", "-t", "capstone-tienda:sin-head", "-f", "app/Dockerfile", str(AQUI.parent / "curso-incidentes" / "tienda")])
sh(["docker", "rm", "-f", "capstone-tienda-vieja"])
sh(["docker", "run", "-d", "--name", "capstone-tienda-vieja", "--network", "capstone-prod", "-e", "LOKI=http://127.0.0.1:1/",
    "capstone-tienda:sin-head"], check=True)
time.sleep(3)
c, d = sh(docker_red("-v", f"{AQUI / 'herramientas'}:/h:ro", "capstone-cliente:1", "bash", "/h/diagnostico.sh",
                     "http://capstone-tienda-vieja:8000/salud"))
p("  la tienda tal cual salió del curso de incidentes:")
[p("  " + l) for l in d.splitlines()]
sh(["docker", "rm", "-f", "capstone-tienda-vieja"])
p("  -> le faltaba do_HEAD (BaseHTTPRequestHandler contesta 501). Añadido, y la de producción:")
diag = docker_red("-v", f"{AQUI / 'herramientas'}:/h:ro", "-v", f"{CERTS}:/c:ro", "capstone-cliente:1",
                  "bash", "/h/diagnostico.sh", "https://tienda.prod.test/salud", "--ca", "/c/raiz.pem")
c, d = sh(diag)
[p("  " + l) for l in d.splitlines()]
p(f"  código de salida {c}")

# ── 6 · observabilidad ──────────────────────────────────────────────────────────────────────
paso(6, "Las alertas: que Prometheus vea las dos réplicas", "Observabilidad de verdad (41-60) · Incidentes (315)")
time.sleep(10)
t = json.loads(urllib.request.urlopen("http://127.0.0.1:19091/api/v1/targets").read())
for x in t["data"]["activeTargets"]:
    p(f"  objetivo {x['labels']['instance']:24s} {x['health']}")
r = json.loads(urllib.request.urlopen("http://127.0.0.1:19091/api/v1/rules").read())
p("  alertas cargadas: " + ", ".join(rr["name"] for gr in r["data"]["groups"] for rr in gr["rules"]))

# ── 7 · la copia, probada ───────────────────────────────────────────────────────────────────
paso(7, "La copia de seguridad, probada: ensayo.sh contra producción", "Restaurar, no copiar (313)")
pg = ["-e", "PGHOST=capstone-db", "-e", "PGUSER=admin", "-e", f"PGPASSWORD={CLAVE}", "-e", "PGDATABASE=tienda"]
for _ in range(30):
    if sh(docker_red(*pg, "postgres:17", "pg_isready", "-q"))[0] == 0:
        break
    time.sleep(1)
sh(docker_red(*pg, "postgres:17", "psql", "-q", "-c",
              "CREATE TABLE IF NOT EXISTS pedidos (id bigserial PRIMARY KEY, cliente int, total numeric(10,2), "
              "creado timestamptz DEFAULT now()); INSERT INTO pedidos (cliente,total) SELECT g%500, g*0.5 "
              "FROM generate_series(1,5000) g;"), check=True)
c, d = sh(docker_red(*pg, "-v", "capstone-copias:/copias", "-v", f"{AQUI / 'herramientas'}:/h:ro", "postgres:17",
                     "bash", "/h/ensayo.sh"))
[p("  " + l) for l in d.splitlines() if not l.startswith("NOTICE")]
p(f"  código de salida {c}")

# ── 8 · desplegar sin cortar ────────────────────────────────────────────────────────────────
paso(8, "Desplegar sin cortar: réplica a réplica, con tráfico", "Un incidente de principio a fin (315)")
sh(["docker", "run", "-d", "--name", "capstone-trafico", "--network", "capstone-prod", "-v", f"{CERTS}:/c:ro",
    "capstone-cliente:1", "bash", "-c",
    'fin=$((SECONDS+30)); while [ $SECONDS -lt $fin ]; do for i in 1 2 3 4 5 6; do '
    'curl -s -o /dev/null -m 10 -w "%{http_code}\\n" --cacert /c/raiz.pem https://tienda.prod.test/lento & done; wait; done'])
time.sleep(3)
for rep in ("a", "b"):
    t0 = time.time()
    _, ap = sh(["tofu", "apply", "-auto-approve", "-no-color", f'-replace=docker_container.tienda["{rep}"]'], cwd=INFRA, check=True)
    p(f"  tofu apply -replace=tienda[\"{rep}\"]: {next(l for l in ap.splitlines() if 'Apply complete' in l)} ({time.time() - t0:.0f} s)")
    time.sleep(4)
sh(["docker", "wait", "capstone-trafico"])
_, codigos = sh(["docker", "logs", "capstone-trafico"])
sh(["docker", "rm", "capstone-trafico"])
cuenta = {}
for l in codigos.split():
    cuenta[l] = cuenta.get(l, 0) + 1
p("  pagos durante el despliegue: " + " · ".join(f"{k}: {v}" for k, v in sorted(cuenta.items())))
fallidos = sum(v for k, v in cuenta.items() if k != "200")

# ── 9 · la lista ────────────────────────────────────────────────────────────────────────────
paso(9, "¿Listo para producción? La lista, comprobada", "todos")
_, quien = sh(["docker", "run", "--rm", "--entrypoint", "id", "capstone-tienda:1", "-u"])
_, env_db = sh(["docker", "inspect", "capstone-db", "--format", "{{range .Config.Env}}{{println .}}{{end}}"])
c_diag, d = sh(diag)
dias = re.search(r"caduca en (\d+) días", d)
c_ens, _ = sh(docker_red(*pg, "-v", "capstone-copias:/copias", "-v", f"{AQUI / 'herramientas'}:/h:ro", "postgres:17",
                         "bash", "/h/ensayo.sh"))
r = json.loads(urllib.request.urlopen("http://127.0.0.1:19091/api/v1/rules").read())
t = json.loads(urllib.request.urlopen("http://127.0.0.1:19091/api/v1/targets").read())
lista = [
    (".env fuera del repositorio (.gitignore)", ".env" in (AQUI / ".gitignore").read_text(encoding="utf-8").split()),
    ("la imagen no corre como root", quien.strip() != "0"),
    ("el estado de OpenTofu, cifrado", CLAVE not in (INFRA / "terraform.tfstate").read_text(encoding="utf-8")),
    ("ninguna clave en docker inspect", CLAVE not in env_db),
    ("diagnóstico de red y TLS: código 0", c_diag == 0),
    ("al certificado le quedan más de 30 días", bool(dias) and int(dias.group(1)) > 30),
    ("alertas cargadas y réplicas vigiladas", bool(r["data"]["groups"]) and all(x["health"] == "up" for x in t["data"]["activeTargets"])),
    ("la copia se restaura: ensayo.sh, código 0", c_ens == 0),
    ("desplegar sin cortar: 0 pagos fallidos", fallidos == 0),
]
for texto, ok in lista:
    p(f"  {'✓' if ok else '✗'} {texto}")
malos = sum(1 for _, ok in lista if not ok)
p(f"  RESULTADO: {len(lista) - malos} de {len(lista)} · " + ("listo para producción (código 0)" if not malos else f"faltan {malos} (código 1)"))

(AQUI / "SALIDA.md").write_text("# SALIDA — curso «De cero a producción»\n\n> Generado por `paso_a_paso.py`. **No se escribe a mano.**\n\n```\n"
                                + "\n".join(SALIDA) + "\n```\n", encoding="utf-8", newline="\n")
if "--dejar" not in sys.argv:
    sh(["tofu", "destroy", "-auto-approve", "-no-color"], cwd=INFRA)
    sh(["docker", "volume", "rm", "-f", "capstone-copias", "capstone-datos-db"])
sys.exit(1 if malos else 0)
