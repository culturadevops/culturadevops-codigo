# -*- coding: utf-8 -*-
"""correr.py — banco del vídeo «Cómo escalar un sistema web y hacerlo tolerante a fallos, medido» (cd, 396).

Nueva versión del vídeo de 2021 (LZ7JFg9d6U4): la misma progresión, cada paso medido. Una sola aplicación
(app/app.py) que cambia de sitio sus datos con variables; el cliente (app/carga.py) corre dentro de la red.

  1 todo en una máquina · 2 la base de datos aparte · 3 dos réplicas con disco propio detrás de nginx
  4 los ficheros en un almacén de objetos · 5 se cae una réplica · 6 una caché delante de la base de datos
  7 una CDN de juguete: un origen «lejos» (150 ms) y una caché cerca

    python correr.py      -> SALIDA.md
"""
import datetime
import os
import shutil
import subprocess
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ENV = dict(os.environ, MSYS_NO_PATHCONV="1")
RED, SUBRED = "esc", "10.77.30.0/24"
APP, PG, MINIO, VALKEY, NGINX = ("sd-escalar:1", "postgres:17-alpine", "minio/minio:latest",
                                 "valkey/valkey:9.1.2-alpine", "nginx:1.30.5-alpine")
salida = []


def p(t=""):
    print(t, flush=True)
    salida.append(t)


def docker(*a, check=False):
    r = subprocess.run(["docker", *a], capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    if check and r.returncode:
        raise SystemExit(f"[X] docker {' '.join(a[:4])}: {r.stdout}{r.stderr}")
    return (r.stdout + r.stderr).strip()


def carga(*a, mostrar=None):
    p(f"$ python carga.py {mostrar or ' '.join(a)}")
    out = docker("run", "--rm", "--network", RED, "-v", f"{AQUI.as_posix()}:/lab", "-w", "/lab/app", APP,
                 "python", "carga.py", *a)
    for l in out.splitlines():
        p("  " + l.strip())
    return out


def esperar(url_desde, contenedor_cliente=None):
    for _ in range(120):
        if "ok" in docker("run", "--rm", "--network", RED, APP, "python", "-c",
                          f"import requests;print(requests.get('{url_desde}/salud',timeout=2).text)"):
            return
        time.sleep(1)
    raise SystemExit(f"[X] no contesta {url_desde}")


def app(nombre, **env):
    docker("rm", "-f", nombre)
    args = ["run", "-d", "--name", nombre, "--hostname", nombre, "--network", RED, "-e", f"REPLICA={nombre}"]
    for k, v in env.items():
        args += ["-e", f"{k}={v}"]
    docker(*args, "-v", f"{(AQUI / 'app').as_posix()}:/app:ro", "-w", "/app", APP, "python", "app.py", check=True)
    esperar(f"http://{nombre}:8000")


def nginx(nombre, conf):
    (AQUI / f"_{nombre}.conf").write_text(conf, encoding="utf-8", newline="\n")
    docker("rm", "-f", nombre)
    docker("run", "-d", "--name", nombre, "--network", RED, "-v",
           f"{(AQUI / f'_{nombre}.conf').as_posix()}:/etc/nginx/nginx.conf:ro", NGINX, check=True)
    time.sleep(2)


def lb(*replicas):
    nginx("lb", "events {}\nhttp {\n  upstream app { " + " ".join(f"server {r}:8000;" for r in replicas) +
          " }\n  server { listen 80; location / { proxy_pass http://app; } }\n}\n")


def pg():
    docker("rm", "-f", "pg")
    docker("run", "-d", "--name", "pg", "--network", RED, "-e", "POSTGRES_PASSWORD=lab", "-v", "esc-pg:/var/lib/postgresql/data",
           PG, check=True)
    for _ in range(240):
        if "ok" in docker("exec", "pg", "psql", "-U", "postgres", "-tAc", "SELECT 'ok'") and \
                "ready to accept connections" in docker("logs", "pg"):
            break
        time.sleep(0.5)
    time.sleep(3)
    docker("exec", "pg", "psql", "-U", "postgres", "-c", "CREATE TABLE IF NOT EXISTS pedidos (id serial PRIMARY KEY, creado text)")


def limpiar():
    docker("rm", "-f", "una", "app1", "app2", "lb", "pg", "minio", "cache", "lejos", "cerca")
    docker("volume", "rm", "esc-pg")
    docker("network", "rm", RED)


def main():
    if not docker("images", "-q", APP):
        d = AQUI / "_imagen"
        d.mkdir(exist_ok=True)
        (d / "Dockerfile").write_text("FROM python:3.13-slim\nRUN pip install --no-cache-dir 'psycopg[binary]==3.2.3' "
                                      "boto3==1.35.36 redis==6.4.0 requests==2.32.5\n", encoding="utf-8")
        docker("build", "-t", APP, str(d), check=True)
    limpiar()
    shutil.rmtree(AQUI / "datos", ignore_errors=True)
    (AQUI / "datos").mkdir()
    docker("network", "create", "--subnet", SUBRED, RED, check=True)
    cab = ["# SALIDA — «Cómo escalar un sistema web y hacerlo tolerante a fallos, medido» (cultura-devops, vídeo 396)",
           "", "> Generado por `correr.py`. **No se escribe a mano.**", "",
           f"- fecha: `{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%SZ}`",
           f"- app en Python 3.13 (app/app.py) · {docker('run', '--rm', '--entrypoint', 'postgres', PG, '--version')} · "
           f"nginx 1.30.5 · Valkey 9.1.2 · MinIO · todo en Docker, en una sola máquina."]
    salida.append("\n```")
    try:
        p("== 1 · Todo en una máquina: la app, su base de datos (un fichero) y los ficheros subidos ==")
        app("una", BD="sqlite", FICHEROS="local")
        carga("pedidos", "http://una:8000", "100", mostrar="pedidos http://una:8000 100")
        carga("subir", "http://una:8000", "10")
        p("$ docker rm -f una && docker run ... una   # la máquina se pierde y se crea otra igual")
        app("una", BD="sqlite", FICHEROS="local")
        p("$ curl http://una:8000/pedidos")
        p("  " + docker("run", "--rm", "--network", RED, APP, "python", "-c",
                        "import requests;print(requests.get('http://una:8000/pedidos').text.strip())") + " pedidos")
        carga("bajar", "http://una:8000", "10", "1")
        docker("rm", "-f", "una")

        p("")
        p("== 2 · La base de datos aparte (Postgres con su volumen); los ficheros, todavía en la app ==")
        pg()
        app("una", BD="postgres", FICHEROS="local")
        carga("pedidos", "http://una:8000", "100")
        carga("subir", "http://una:8000", "10")
        p("$ docker rm -f una && docker run ... una")
        app("una", BD="postgres", FICHEROS="local")
        p("$ curl http://una:8000/pedidos")
        p("  " + docker("run", "--rm", "--network", RED, APP, "python", "-c",
                        "import requests;print(requests.get('http://una:8000/pedidos').text.strip())") + " pedidos")
        carga("bajar", "http://una:8000", "10", "1")
        docker("rm", "-f", "una")

        p("")
        p("== 3 · Dos réplicas, cada una con su disco, detrás de nginx (round robin) ==")
        app("app1", BD="postgres", FICHEROS="local")
        app("app2", BD="postgres", FICHEROS="local")
        lb("app1", "app2")
        carga("subir", "http://lb", "20")
        carga("bajar", "http://lb", "20", "5")

        p("")
        p("== 4 · Los ficheros a un almacén de objetos (MinIO, API de S3) ==")
        docker("run", "-d", "--name", "minio", "--network", RED, "-e", "MINIO_ROOT_USER=lab",
               "-e", "MINIO_ROOT_PASSWORD=lab12345", MINIO, "server", "/data", check=True)
        for _ in range(60):
            if "API:" in docker("logs", "minio"):
                break
            time.sleep(1)
        time.sleep(2)
        docker("run", "--rm", "--network", RED, APP, "python", "-c",
               "import boto3;boto3.client('s3',endpoint_url='http://minio:9000',aws_access_key_id='lab',"
               "aws_secret_access_key='lab12345',region_name='us-east-1').create_bucket(Bucket='subidas')")
        app("app1", BD="postgres", FICHEROS="s3")
        app("app2", BD="postgres", FICHEROS="s3")
        carga("subir", "http://lb", "20")
        carga("bajar", "http://lb", "20", "5")

        p("")
        p("== 5 · Se cae una réplica a mitad de carga (a los 3 s), 10 s, 20 clientes ==")
        docker("exec", "pg", "psql", "-U", "postgres", "-q", "-c",
               "CREATE TABLE ventas AS SELECT (random()*999)::int + 1 AS producto_id, round((random()*500)::numeric, 2) "
               "AS total FROM generate_series(1, 3000000); ANALYZE ventas;")
        (AQUI / "datos" / "matar").unlink(missing_ok=True)
        p("$ python carga.py golpe-caida http://lb /pedidos 10 20 3   # y a los 3 s: docker kill app2")
        hilo = subprocess.Popen(["docker", "run", "--rm", "--network", RED, "-v", f"{AQUI.as_posix()}:/lab", "-w", "/lab/app",
                                 APP, "python", "carga.py", "golpe-caida", "http://lb", "/pedidos", "10", "20", "3"],
                                stdout=subprocess.PIPE, text=True, encoding="utf-8", env=ENV)
        while not (AQUI / "datos" / "matar").exists():
            time.sleep(0.05)
        docker("kill", "app2")
        for l in hilo.communicate()[0].splitlines():
            p(l)
        p("  [nginx: chequeo pasivo por defecto, max_fails=1 fail_timeout=10s, y reintento en la otra réplica]")
        docker("rm", "-f", "app2")

        p("")
        p("== 6 · La base de datos se vuelve el cuello de botella: una consulta pesada, 2 réplicas, 20 clientes, 10 s ==")
        app("app2", BD="postgres", FICHEROS="s3")
        p("  [ventas: 3.000.000 de filas sin índice; /ventas/7 suma las ventas del producto 7]")
        carga("golpe", "http://lb", "/ventas/7", "10", "20", mostrar="golpe http://lb /ventas/7 10 20   # sin caché")
        docker("run", "-d", "--name", "cache", "--network", RED, VALKEY, check=True)
        time.sleep(2)
        app("app1", BD="postgres", FICHEROS="s3", CACHE="1")
        app("app2", BD="postgres", FICHEROS="s3", CACHE="1")
        carga("golpe", "http://lb", "/ventas/7", "10", "20", mostrar="golpe http://lb /ventas/7 10 20   # con Valkey delante")

        p("")
        p("== 7 · Una CDN de juguete: el origen está «lejos» (150 ms de latencia añadida) y hay una caché cerca ==")
        # un fichero de 500 KB en el almacén, servido por un nginx «lejos» con 150 ms en su interfaz
        docker("run", "--rm", "--network", RED, APP, "python", "-c",
               "import boto3,os;c=boto3.client('s3',endpoint_url='http://minio:9000',aws_access_key_id='lab',"
               "aws_secret_access_key='lab12345',region_name='us-east-1');c.put_object(Bucket='subidas',Key='foto.jpg',"
               "Body=os.urandom(500*1024));c.put_bucket_policy(Bucket='subidas',Policy='{\"Version\":\"2012-10-17\","
               "\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":\"*\",\"Action\":\"s3:GetObject\","
               "\"Resource\":\"arn:aws:s3:::subidas/*\"}]}')")
        (AQUI / "_lejos.conf").write_text("events {}\nhttp {\n  server { listen 80; location / { proxy_pass http://minio:9000; } }\n}\n",
                                          encoding="utf-8", newline="\n")
        docker("run", "-d", "--name", "lejos", "--network", RED, "--cap-add", "NET_ADMIN", "-v",
               f"{(AQUI / '_lejos.conf').as_posix()}:/etc/nginx/nginx.conf:ro", NGINX, check=True)
        docker("exec", "lejos", "sh", "-c", "apk add --no-cache iproute2 >/dev/null 2>&1; tc qdisc add dev eth0 root netem delay 150ms",
               check=True)
        nginx("cerca", "events {}\nhttp {\n  proxy_cache_path /tmp/cdn keys_zone=cdn:10m;\n  server { listen 80;\n"
                       "    location / { proxy_pass http://lejos; proxy_cache cdn; proxy_cache_valid 200 10m;\n"
                       "      add_header X-Cache $upstream_cache_status; } }\n}\n")
        carga("tiempos", "http://lejos/subidas/foto.jpg", "5", mostrar="tiempos http://lejos/subidas/foto.jpg 5   # al origen")
        carga("tiempos", "http://cerca/subidas/foto.jpg", "5", mostrar="tiempos http://cerca/subidas/foto.jpg 5   # por la caché cercana")
        salida.append("```")
    finally:
        limpiar()
    (AQUI / "SALIDA.md").write_bytes(("\n".join(cab) + "\n" + "\n".join(salida) + "\n").encode("utf-8"))
    print("\n[ok] SALIDA.md")


if __name__ == "__main__":
    main()
