# -*- coding: utf-8 -*-
"""Laravel con Docker en 2026 (cultura-devops 697): ejecuta TODO y regenera SALIDA.md y medidas.json.

    python ejecutar_todo.py            # todo (unos 15-20 min)
    python ejecutar_todo.py --rapido   # 1 repetición por medida

Qué hace:
  1. Copia app/ (Laravel 13, sin vendor: como un git clone), docker/ y compose*.yaml a un directorio
     temporal (tempfile.mkdtemp). Nada se monta ni se modifica dentro de recursos/.
  2. Construye la imagen multietapa y la «gorda», sin caché y con caché, y mide tiempos y tamaños.
  3. Levanta la versión buena y mide el tiempo hasta la primera respuesta 200.
  4. Ejecuta las trampas, una por una, con `docker compose down -v` entre cada una.
  5. Limpia: contenedores, volúmenes, red e imágenes v697-*; borra solo SU directorio temporal.
Requiere Docker con compose v2 y el puerto 8697 libre.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
URL = "http://127.0.0.1:8697"
REPS = 1 if "--rapido" in sys.argv else 2
MD = []
MEDIDAS = {}
W = None  # directorio de trabajo temporal


def corre(args, show=None, env=None, timeout=900, cola=None, filtro=None, md=True):
    """Ejecuta, mide y (si md) apunta el comando y su salida en SALIDA.md."""
    e = dict(os.environ, **(env or {}))
    t0 = time.perf_counter()
    p = subprocess.run(args, cwd=W, env=e, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    s = time.perf_counter() - t0
    txt = (p.stdout + p.stderr).rstrip()
    lineas = txt.splitlines()
    if filtro:
        lineas = [x for x in lineas if any(f in x for f in filtro)]
    if cola:
        lineas = lineas[-cola:]
    lineas = [x if len(x) <= 240 else x[:240] + " …" for x in lineas]
    if md:
        pre = "".join(f"{k}={v} " for k, v in (env or {}).items())
        MD.append("```\n$ " + pre + (show or " ".join(args)) + "\n" + "\n".join(lineas) + f"\n# exit={p.returncode} · {s:.1f} s\n```\n")
    return p.returncode, txt, s


def h(t):
    MD.append(f"\n## {t}\n")


def nota(t):
    MD.append(t + "\n")


def codigo(url=URL):
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            return r.status
    except urllib.error.HTTPError as ex:
        return ex.code
    except Exception:
        return None


def curl(ruta="/"):
    return corre(["curl", "-s", "-o", os.devnull, "-w", "%{http_code}\\n", URL + ruta],
                 show=f'curl -s -o /dev/null -w "%{{http_code}}\\n" localhost:8697{ruta}')


def espera_200(t0, tope=180):
    while time.perf_counter() - t0 < tope:
        if codigo() == 200:
            return time.perf_counter() - t0
        time.sleep(0.2)
    return float("nan")


def compose(files, *args):
    return ["docker", "compose", "--ansi", "never"] + sum((["-f", f] for f in files), []) + list(args)


def show_compose(files, *args):
    extra = "".join(f" -f {f}" for f in files) if len(files) > 1 else ""
    return "docker compose" + extra + " " + " ".join(args)


def abajo(files=("compose.yaml",), md=True):
    corre(compose(files, "down", "-v", "--remove-orphans"), show=show_compose(files, "down", "-v"), cola=3, md=md)


def build(target, tag, dockerfile="docker/Dockerfile", cache=True):
    a = ["docker", "build", "--progress", "plain", "-f", dockerfile, "--target", target, "-t", tag, "."]
    if not cache:
        a.insert(2, "--no-cache")
    show = "docker build " + ("--no-cache " if not cache else "") + f"-f {dockerfile} --target {target} -t {tag} ."
    rc, txt, s = corre(a, show=show, cola=2)
    if rc != 0:
        raise SystemExit(f"falló el build {tag}:\n{txt[-3000:]}")
    return s


def toca_ruta(n):
    with open(Path(W) / "routes" / "web.php", "a", encoding="utf-8") as f:
        # Único por ejecución: si el texto se repitiera, BuildKit reusaría la capa de una ejecución anterior.
        f.write(f"\n// cambio {n} {time.time_ns()}\n")


def preparar():
    global W
    W = tempfile.mkdtemp(prefix="v697-laravel-")
    shutil.copytree(AQUI / "app", W, dirs_exist_ok=True)
    shutil.copytree(AQUI / "docker", Path(W) / "docker")
    for f in AQUI.glob("compose*.yaml"):
        shutil.copy(f, W)
    lock = json.loads((AQUI / "app" / "composer.lock").read_text(encoding="utf-8"))
    fw = next(p["version"] for p in lock["packages"] if p["name"] == "laravel/framework")
    MEDIDAS["laravel_framework"] = fw
    return fw


def versiones(fw):
    h("0 · Versiones")
    nota(f"- laravel/laravel (esqueleto) 13.11.0 · laravel/framework **{fw}** (de app/composer.lock)")
    corre(["docker", "version", "--format", "Docker {{.Server.Version}}"], show="docker version --format 'Docker {{.Server.Version}}'")
    corre(["docker", "compose", "version"])
    corre(["docker", "run", "--rm", "php:8.5-fpm-alpine", "php", "-r", "echo PHP_VERSION, PHP_EOL;"],
          show="docker run --rm php:8.5-fpm-alpine php -r 'echo PHP_VERSION, PHP_EOL;'")
    corre(["docker", "run", "--rm", "composer:2", "composer", "--version"], show="docker run --rm composer:2 composer --version", filtro=["Composer version", "PHP version"])
    corre(["docker", "run", "--rm", "mysql:8.4", "mysqld", "--version"], show="docker run --rm mysql:8.4 mysqld --version")
    corre(["docker", "run", "--rm", "--entrypoint", "sh", "mysql:8.4", "-c", "grep -n 'skip-networking' /usr/local/bin/docker-entrypoint.sh"],
          show="docker run --rm --entrypoint sh mysql:8.4 -c \"grep -n 'skip-networking' /usr/local/bin/docker-entrypoint.sh\"")
    corre(["docker", "run", "--rm", "nginx:1.28-alpine", "nginx", "-v"], show="docker run --rm nginx:1.28-alpine nginx -v", cola=1)
    corre(["docker", "info", "--format", "CPUs {{.NCPU}} · RAM {{.MemTotal}} B · {{.OperatingSystem}}"],
          show="docker info --format 'CPUs {{.NCPU}} · RAM {{.MemTotal}} B · {{.OperatingSystem}}'")


def builds():
    h("1 · Builds: sin caché y con caché")
    nota("Las imágenes base ya estaban descargadas: `--no-cache` mide construir las capas, no bajar las bases. "
         "composer sí descarga paquetes de Internet en cada build sin caché, así que esos tiempos dependen de la red.")
    m = MEDIDAS.setdefault("build", {})
    for i in range(REPS):
        m.setdefault("multi_sin_cache", []).append(build("runtime", "v697-app:multi", cache=False))
    for i in range(REPS):
        m.setdefault("gorda_sin_cache", []).append(build("runtime", "v697-app:gorda", "docker/Dockerfile.gorda", cache=False))
    build("web", "v697-web:multi")
    build("sin-permisos", "v697-app:sin-permisos")
    nota("\n### Con caché y sin tocar nada\n")
    m["multi_cache_sin_cambios"] = build("runtime", "v697-app:multi")
    m["gorda_cache_sin_cambios"] = build("runtime", "v697-app:gorda", "docker/Dockerfile.gorda")
    nota("\n### Con caché, tras cambiar UNA línea de routes/web.php\n")
    for i in range(REPS):
        toca_ruta(f"multi {i}")
        m.setdefault("multi_cache_1_linea", []).append(build("runtime", "v697-app:multi"))
    for i in range(REPS):
        toca_ruta(f"gorda {i}")
        m.setdefault("gorda_cache_1_linea", []).append(build("runtime", "v697-app:gorda", "docker/Dockerfile.gorda"))
    build("web", "v697-web:multi")
    build("sin-permisos", "v697-app:sin-permisos")
    nota("En la gorda, `COPY . .` va ANTES de `composer install`: cambiar una línea de código invalida la capa de composer y "
         "reinstala todo. En la multietapa, composer.json y composer.lock se copian primero y `composer install` sale de la caché.")


def tamanos():
    h("2 · Tamaños")
    corre(["docker", "image", "ls", "--format", "table {{.Repository}}:{{.Tag}}\t{{.Size}}", "v697-*"],
          show="docker image ls v697-*")
    corre(["docker", "image", "ls", "--format", "table {{.Repository}}:{{.Tag}}\t{{.Size}}"],
          show="docker image ls (bases)", filtro=["php:8.5", "composer:2", "nginx:1.28", "mysql:8.4", "REPOSITORY"])
    nota("`docker image ls` (almacén containerd de Docker Desktop) da el tamaño en disco y el comprimido (lo que se sube y se baja). "
         "Abajo, el comprimido exacto en bytes:")
    t = {}
    for img in ["v697-app:multi", "v697-app:gorda", "v697-web:multi", "php:8.5-fpm-alpine", "php:8.5-fpm"]:
        rc, txt, _ = corre(["docker", "image", "inspect", "--format", "{{.Size}}", img], show=f"docker image inspect --format '{{{{.Size}}}}' {img}")
        t[img] = int(txt.strip()) if rc == 0 else None
    MEDIDAS["tamano_comprimido_bytes"] = t
    rc, txt, _ = corre(["docker", "image", "ls", "--format", "{{.Repository}}:{{.Tag}}|{{.Size}}", "v697-*"], md=False)
    MEDIDAS["tamano_disco"] = dict(x.split("|", 1) for x in txt.splitlines() if "|" in x)
    nota("\n### Qué hay dentro de cada una\n")
    for img in ["v697-app:multi", "v697-app:gorda"]:
        corre(["docker", "run", "--rm", "--entrypoint", "sh", img, "-c",
               "du -sh vendor; ls vendor | wc -l | sed 's/$/ carpetas en vendor/'; "
               "for b in composer git node npm gcc; do command -v $b >/dev/null && echo \"$b: sí\" || echo \"$b: no\"; done"],
              show=f"docker run --rm --entrypoint sh {img} -c 'du -sh vendor; …; command -v composer git node npm gcc'")


def primera_respuesta():
    h("3 · La versión buena y el tiempo hasta la primera respuesta")
    f = ("compose.yaml",)
    abajo(f, md=False)
    t0 = time.perf_counter()
    rc, txt, s_up = corre(compose(f, "up", "-d"), show="docker compose up -d", cola=8)
    t200 = espera_200(t0)
    nota(f"**`up -d` volvió a los {s_up:.1f} s** (espera a que MySQL esté sano) · **primera respuesta 200 a los {t200:.1f} s** desde el `up`.")
    corre(compose(f, "ps"), show="docker compose ps")
    curl()
    corre(compose(f, "logs", "app"), show="docker compose logs app", filtro=["INFO", "DONE", "ready to handle", "GET /"])
    corre(compose(f, "exec", "-T", "app", "php", "artisan", "migrate:status"), show="docker compose exec app php artisan migrate:status")
    corre(compose(f, "exec", "-T", "app", "php", "artisan", "--version"), show="docker compose exec app php artisan --version")
    corre(compose(f, "exec", "-T", "app", "sh", "-c", "ps -o user,args | grep '[p]hp-fpm'"),
          show="docker compose exec app sh -c \"ps -o user,args | grep php-fpm\"")
    frio, tibio, ups = [t200], [], [s_up]
    abajo(f)
    for i in range(REPS):  # más rondas en frío (volumen nuevo: MySQL se inicializa)
        t0 = time.perf_counter()
        _, _, su = corre(compose(f, "up", "-d"), md=False)
        frio.append(espera_200(t0))
        ups.append(su)
        corre(compose(f, "down", "-v"), md=False)
    for i in range(REPS + 1):  # en tibio: el volumen ya existe
        _, _, _ = corre(compose(f, "up", "-d"), md=False)
        espera_200(time.perf_counter())
        corre(compose(f, "down"), md=False)
        t0 = time.perf_counter()
        corre(compose(f, "up", "-d"), md=False)
        tibio.append(espera_200(t0))
        corre(compose(f, "down", "-v"), md=False)
    MEDIDAS["primera_respuesta_s"] = {"frio_volumen_nuevo": frio, "up_d_frio": ups, "tibio_volumen_existente": tibio}
    filas = ["\n| ronda | `up -d` (frío) | 1.ª respuesta 200 (frío, volumen nuevo) | 1.ª respuesta 200 (tibio, volumen existente) |",
             "|---|---|---|---|"]
    for i in range(max(len(frio), len(tibio))):
        a = f"{ups[i]:.1f} s" if i < len(ups) else "—"
        b = f"{frio[i]:.1f} s" if i < len(frio) else "—"
        c = f"{tibio[i]:.1f} s" if i < len(tibio) else "—"
        filas.append(f"| {i + 1} | {a} | {b} | {c} |")
    nota("\n".join(filas))
    nota("\n(`cpus: \"2\"` en app y db; el tiempo cuenta desde que se lanza `docker compose up -d`.)")


def trampa_127():
    h("4 · Trampa 1: DB_HOST=127.0.0.1 en el .env")
    f = ("compose.yaml",)
    env = {"APP_ENV_FILE": "docker/app.env.trampa-127", "MIGRAR": "0"}
    corre(["sh", "-c", "grep DB_HOST docker/app.env.trampa-127"], show="grep DB_HOST docker/app.env.trampa-127")
    corre(compose(f, "up", "-d"), show="docker compose up -d", env=env, cola=6)
    espera_200(time.perf_counter(), tope=8)
    corre(compose(f, "ps"), show="docker compose ps")
    curl()
    corre(compose(f, "logs", "app"), show="docker compose logs app | grep SQLSTATE", filtro=["SQLSTATE"], cola=2)
    corre(compose(f, "exec", "-T", "app", "php", "-r", "echo gethostbyname('db'), PHP_EOL;"),
          show="docker compose exec app php -r \"echo gethostbyname('db'), PHP_EOL;\"")
    corre(compose(f, "exec", "-T", "app", "php", "artisan", "migrate", "--force"), show="docker compose exec app php artisan migrate --force", filtro=["SQLSTATE"], cola=2)
    abajo(f)


def trampa_healthcheck():
    h("5 · Trampa 2: depends_on sin healthcheck (la app arranca antes que MySQL)")
    f = ("compose.yaml", "compose.trampa-sin-healthcheck.yaml")
    t0 = time.perf_counter()
    corre(compose(f, "up", "-d"), show=show_compose(f, "up", "-d"), cola=6)
    muerte = None
    while time.perf_counter() - t0 < 90:
        rc, txt, _ = corre(["docker", "inspect", "--format", "{{.State.Status}} {{.State.ExitCode}}", "v697-laravel-app-1"], md=False)
        if txt.startswith("exited"):
            muerte = time.perf_counter() - t0
            break
        time.sleep(0.3)
    sano = None
    while time.perf_counter() - t0 < 120:
        rc, txt, _ = corre(["docker", "inspect", "--format", "{{.State.Health.Status}}", "v697-laravel-db-1"], md=False)
        if txt.strip() == "healthy":
            sano = time.perf_counter() - t0
            break
        time.sleep(0.3)
    MEDIDAS["trampa_healthcheck"] = {"app_murio_s": muerte, "db_sana_s": sano}
    nota(f"**La app murió a los {muerte:.1f} s; MySQL quedó sano a los {sano:.1f} s.**" if muerte and sano else f"app murió: {muerte} · db sana: {sano}")
    corre(compose(f, "ps", "-a"), show=show_compose(f, "ps", "-a"))
    corre(compose(f, "logs", "app"), show=show_compose(f, "logs", "app"), filtro=["SQLSTATE", "Illuminate", "Connection refused"], cola=3)
    curl()
    abajo(f)


def trampa_permisos():
    h("6 · Trampa 3: storage y bootstrap/cache sin permisos")
    f = ("compose.yaml", "compose.trampa-permisos.yaml")
    corre(compose(f, "up", "-d"), show=show_compose(f, "up", "-d"), cola=6)
    espera_200(time.perf_counter(), tope=10)
    corre(compose(f, "ps"), show=show_compose(f, "ps"))
    corre(compose(f, "logs", "app"), show=show_compose(f, "logs", "app"), filtro=["DONE", "ready to handle"], cola=5)
    curl()
    corre(compose(f, "logs", "app"), show=show_compose(f, "logs", "app") + " | grep -i 'permission denied'",
          filtro=["ermission denied"], cola=2)
    corre(compose(f, "logs", "app"), show=show_compose(f, "logs", "app") + " | grep production.ERROR",
          filtro=["production.ERROR"], cola=1)
    corre(compose(f, "exec", "-T", "app", "ls", "-ld", "storage", "storage/framework/views", "bootstrap/cache"),
          show="docker compose exec app ls -ld storage storage/framework/views bootstrap/cache")
    corre(compose(f, "exec", "-T", "app", "sh", "-c", "ps -o user,args | grep '[p]hp-fpm'"),
          show="docker compose exec app sh -c \"ps -o user,args | grep php-fpm\"")
    abajo(f)
    nota("El arreglo es la etapa `runtime` del Dockerfile: `RUN chown -R www-data:www-data storage bootstrap/cache`.")
    f = ("compose.yaml",)
    corre(compose(f, "up", "-d"), show="docker compose up -d", cola=2)
    espera_200(time.perf_counter(), tope=60)
    corre(compose(f, "exec", "-T", "app", "ls", "-ld", "storage", "bootstrap/cache"), show="docker compose exec app ls -ld storage bootstrap/cache")
    curl()
    abajo(f)


def trampa_vendor():
    h("7 · Trampa 4: montar el proyecto entero tapa el vendor de la imagen")
    corre(["sh", "-c", "ls -d vendor 2>&1; grep -x /vendor .gitignore"], show="ls -d vendor; grep -x /vendor .gitignore")
    nota("Primero con la imagen gorda, que (como casi todos los tutoriales) no copia ningún php.ini:")
    f = ("compose.yaml", "compose.gorda.yaml", "compose.trampa-vendor.yaml")
    corre(compose(f, "up", "-d"), show=show_compose(f, "up", "-d"), env={"MIGRAR": "0"}, cola=3)
    time.sleep(2)
    corre(compose(f, "ps"), show=show_compose(f, "ps"))
    curl()
    corre(["sh", "-c", f"curl -s -i {URL}/ | grep -E 'HTTP/|Fatal error'"], show="curl -s -i localhost:8697/ | grep -E 'HTTP/|Fatal error'")
    corre(compose(f, "exec", "-T", "app", "sh", "-c", "php -i | grep -E 'Loaded Configuration|^display_errors'"),
          show="docker compose exec app sh -c \"php -i | grep -E 'Loaded Configuration|^display_errors'\"")
    corre(compose(f, "exec", "-T", "app", "ls", "vendor"), show="docker compose exec app ls vendor")
    corre(["docker", "run", "--rm", "--entrypoint", "sh", "v697-app:gorda", "-c", "ls vendor | wc -l"],
          show="docker run --rm --entrypoint sh v697-app:gorda -c 'ls vendor | wc -l'")
    abajo(f)
    nota("Ahora con la multietapa, que copia php.ini-production:")
    f = ("compose.yaml", "compose.trampa-vendor.yaml")
    corre(compose(f, "up", "-d"), show=show_compose(f, "up", "-d"), env={"MIGRAR": "0"}, cola=3)
    time.sleep(2)
    curl()
    corre(compose(f, "exec", "-T", "app", "sh", "-c", "php -i | grep -E 'Loaded Configuration|^display_errors'"),
          show="docker compose exec app sh -c \"php -i | grep -E 'Loaded Configuration|^display_errors'\"")
    corre(compose(f, "logs", "app"), show=show_compose(f, "logs", "app") + " | grep autoload", filtro=["autoload"], cola=1)
    abajo(f)
    nota("El arreglo: montar solo lo que editas (compose.dev.yaml: app/, routes/, resources/).")
    f = ("compose.yaml", "compose.dev.yaml")
    corre(compose(f, "up", "-d"), show=show_compose(f, "up", "-d"), cola=2)
    espera_200(time.perf_counter(), tope=60)
    curl()
    with open(Path(W) / "routes" / "web.php", "a", encoding="utf-8") as fh:
        fh.write("\nRoute::get('/hola', fn () => 'hola desde el contenedor, sin rebuild');\n")
    time.sleep(3)
    corre(["sh", "-c", "tail -1 routes/web.php"], show="tail -1 routes/web.php")
    corre(["curl", "-s", URL + "/hola"], show="curl -s localhost:8697/hola")
    abajo(f)


def gorda_respuesta():
    h("8 · La gorda también responde: el tamaño no da error")
    f = ("compose.yaml", "compose.gorda.yaml")
    t0 = time.perf_counter()
    corre(compose(f, "up", "-d"), show=show_compose(f, "up", "-d"), cola=2)
    t = espera_200(t0)
    MEDIDAS["gorda_primera_respuesta_frio_s"] = t
    nota(f"Primera respuesta 200 con la gorda (frío): **{t:.1f} s**.")
    curl()
    abajo(f)


def limpiar():
    h("9 · Limpieza")
    for f in [("compose.yaml",)]:
        corre(compose(f, "down", "-v", "--remove-orphans"), md=False)
    rc, txt, _ = corre(["docker", "image", "ls", "-q", "v697-*"], md=False)
    corre(["docker", "image", "rm", "-f", "v697-app:multi", "v697-app:gorda", "v697-app:sin-permisos", "v697-web:multi"],
          show="docker image rm v697-app:multi v697-app:gorda v697-app:sin-permisos v697-web:multi", cola=4)
    corre(["docker", "image", "ls", "-q", "v697-*"], show="docker image ls -q v697-*")
    corre(["docker", "ps", "-a", "--filter", "name=v697", "--format", "{{.Names}}"], show="docker ps -a --filter name=v697")
    corre(["docker", "volume", "ls", "--filter", "name=v697", "-q"], show="docker volume ls --filter name=v697 -q")
    corre(["docker", "network", "ls", "--filter", "name=v697", "-q"], show="docker network ls --filter name=v697 -q")


def resumen():
    m = MEDIDAS
    b = m["build"]
    f = lambda xs: " / ".join(f"{x:.1f} s" for x in xs) if isinstance(xs, list) else f"{xs:.1f} s"
    t = m["tamano_comprimido_bytes"]
    mb = lambda k: f"{t[k] / 1e6:.1f} MB" if t.get(k) else "—"
    r = ["## Resumen medido\n", "| medida | multietapa | gorda |", "|---|---|---|",
         f"| tamaño en disco (`docker image ls`) | {m['tamano_disco'].get('v697-app:multi')} | {m['tamano_disco'].get('v697-app:gorda')} |",
         f"| tamaño comprimido (lo que se sube/baja) | {mb('v697-app:multi')} | {mb('v697-app:gorda')} |",
         f"| build sin caché | {f(b['multi_sin_cache'])} | {f(b['gorda_sin_cache'])} |",
         f"| build con caché, sin cambios | {f(b['multi_cache_sin_cambios'])} | {f(b['gorda_cache_sin_cambios'])} |",
         f"| build con caché, 1 línea cambiada | {f(b['multi_cache_1_linea'])} | {f(b['gorda_cache_1_linea'])} |",
         "", f"- nginx (v697-web:multi): {m['tamano_disco'].get('v697-web:multi')} en disco, {mb('v697-web:multi')} comprimido.",
         f"- Primera respuesta 200 en frío (volumen nuevo): {f(m['primera_respuesta_s']['frio_volumen_nuevo'])}; "
         f"en tibio: {f(m['primera_respuesta_s']['tibio_volumen_existente'])}.",
         f"- Trampa del healthcheck: {m.get('trampa_healthcheck')}.", ""]
    return "\n".join(r)


def main():
    t0 = time.time()
    fw = preparar()
    print("directorio de trabajo:", W)
    try:
        versiones(fw)
        builds()
        tamanos()
        primera_respuesta()
        trampa_127()
        trampa_healthcheck()
        trampa_permisos()
        trampa_vendor()
        gorda_respuesta()
    finally:
        limpiar()
        cab = ["# SALIDA — Laravel con Docker en 2026 (cultura-devops 697)\n",
               f"Generado por `python ejecutar_todo.py` el {time.strftime('%Y-%m-%d %H:%M')} (hora local) · {time.time() - t0:.0f} s en total · "
               f"{REPS} repeticiones por medida. Cada bloque es el comando tal cual y su salida real (las líneas largas, recortadas con «…»).\n"]
        res = resumen() if "primera_respuesta_s" in MEDIDAS else "## Resumen\n(la ejecución se cortó antes de medir)\n"
        (AQUI / "SALIDA.md").write_text("\n".join(cab) + "\n" + res + "\n" + "\n".join(MD), encoding="utf-8")
        (AQUI / "medidas.json").write_text(json.dumps(MEDIDAS, indent=1, ensure_ascii=False), encoding="utf-8")
        shutil.rmtree(W, ignore_errors=True)  # solo el mkdtemp de esta ejecución
        print("SALIDA.md escrito")


if __name__ == "__main__":
    main()
