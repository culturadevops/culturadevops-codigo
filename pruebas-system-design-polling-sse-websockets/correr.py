# -*- coding: utf-8 -*-
"""correr.py — banco del vídeo «System design: polling, long polling, SSE y WebSockets»
(cultura-devops, vídeo 355).

lab/servidor publica una notificación cada 3 s; lab/cliente la recibe de cuatro maneras con 100
clientes durante 30 s y mide eventos recibidos, retraso medio y peor, peticiones por minuto y
conexiones abiertas a la vez. Después, lo mismo detrás de nginx 1.30.5 con su configuración por
defecto y con el arreglo. Red de Docker 10.77.24.0/24. Una sola máquina.

    python correr.py      -> SALIDA.md
"""
import datetime
import os
import subprocess
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ENV = dict(os.environ, MSYS_NO_PATHCONV="1")
RED, SUBRED = "sd-notif", "10.77.24.0/24"
NGINX = "nginx:1.30.5-alpine"
salida = []

POR_DEFECTO = """events {}
http {
  server {
    listen 80;
    location / {
      proxy_pass http://srv:8080;   # tal cual: lo que se suele copiar
    }
  }
}
"""
CON_GZIP = """events {}
http {
  gzip on;
  gzip_types text/event-stream application/json;   # «comprimir también lo de la API»
  server {
    listen 80;
    location / {
      proxy_pass http://srv:8080;
    }
  }
}
"""
ARREGLADO = """events {}
http {
  map $http_upgrade $connection_upgrade { default upgrade; '' close; }
  server {
    listen 80;
    location / {
      proxy_pass http://srv:8080;
      proxy_http_version 1.1;
      proxy_set_header Upgrade $http_upgrade;          # WebSocket
      proxy_set_header Connection $connection_upgrade; # WebSocket
      proxy_read_timeout 1h;                            # conexiones largas
    }
  }
}
"""


def p(t=""):
    print(t, flush=True)
    salida.append(t)


def docker(*a, check=False):
    r = subprocess.run(["docker", *a], capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    if check and r.returncode:
        raise SystemExit(f"[X] docker {' '.join(a[:3])}: {r.stdout}{r.stderr}")
    return (r.stdout + r.stderr).strip()


def cliente(*args, mostrar=None):
    p(f"$ cli {mostrar or ' '.join(args)}")
    for l in docker("run", "--rm", "--network", RED, "-v", f"{(AQUI / 'lab').as_posix()}:/w:ro", "alpine:3.22",
                    "/w/cli", *args).splitlines():
        p(l)


def nginx(conf):
    (AQUI / "nginx.conf").write_text(conf, encoding="utf-8", newline="\n")
    docker("rm", "-f", "sd-proxy")
    docker("run", "-d", "--name", "sd-proxy", "--network", RED, "-v",
           f"{(AQUI / 'nginx.conf').as_posix()}:/etc/nginx/nginx.conf:ro", NGINX, check=True)
    time.sleep(2)


def limpiar():
    docker("rm", "-f", "srv", "sd-proxy")
    docker("network", "rm", RED)


def main():
    docker("run", "--rm", "-v", f"{(AQUI / 'lab').as_posix()}:/w", "-w", "/w", "-e", "CGO_ENABLED=0",
           "-v", "fab-go-mod:/go/pkg/mod", "-v", "fab-go-cache:/root/.cache/go-build", "golang:1.27.2",
           "sh", "-c", "go build -o srv ./servidor && go build -o cli ./cliente", check=True)
    cab = ["# SALIDA — «System design: polling, long polling, SSE y WebSockets» (cultura-devops, vídeo 355)", "",
           "> Generado por `correr.py`. **No se escribe a mano.**", "",
           f"- fecha: `{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%SZ}`",
           f"- servidor y clientes en Go 1.27.2 (coder/websocket v1.8.15) · `{docker('run', '--rm', '--entrypoint', 'nginx', NGINX, '-v')}`",
           "- una notificación cada 3 s; 100 clientes durante 30 s. Una sola máquina."]
    limpiar()
    docker("network", "create", "--subnet", SUBRED, RED, check=True)
    try:
        docker("run", "-d", "--name", "srv", "--network", RED, "-v", f"{(AQUI / 'lab').as_posix()}:/w:ro",
               "alpine:3.22", "/w/srv", check=True)
        time.sleep(2)
        salida.append("\n```")
        p("== 1 · Las cuatro maneras, directas al servidor (100 clientes, 30 s, un evento cada 3 s) ==")
        cliente("-modo", "poll", "-cada", "5s")
        cliente("-modo", "poll", "-cada", "1s")
        cliente("-modo", "longpoll")
        cliente("-modo", "sse")
        cliente("-modo", "ws")
        p("")
        p("== 1b · Lo que pesa tener conexiones abiertas: 2.000 a la vez ==")
        docker("restart", "srv")
        time.sleep(2)
        cliente("-modo", "memoria-sse", "-clientes", "2000", mostrar="-modo memoria-sse -clientes 2000")
        docker("restart", "srv")
        time.sleep(2)
        cliente("-modo", "memoria-ws", "-clientes", "2000", mostrar="-modo memoria-ws -clientes 2000")
        p("")
        p("== 2 · Detrás de nginx, con la configuración que se suele copiar ==")
        p("$ cat nginx.conf   # location / { proxy_pass http://srv:8080; }")
        nginx(POR_DEFECTO)
        cliente("-url", "http://sd-proxy", "-modo", "sse", mostrar="-url http://sd-proxy -modo sse")
        cliente("-url", "http://sd-proxy", "-modo", "ws", mostrar="-url http://sd-proxy -modo ws")
        p("")
        p("== 2b · El mismo nginx con gzip para text/event-stream ==")
        nginx(CON_GZIP)
        cliente("-url", "http://sd-proxy", "-modo", "sse", mostrar="-url http://sd-proxy -modo sse   # gzip on")
        p("")
        p("== 2c · Un flujo SSE que pasa 75 s sin eventos ==")
        nginx(POR_DEFECTO)
        cliente("-url", "http://sd-proxy", "-modo", "silencio", "-durante", "75s",
                mostrar="-url http://sd-proxy -modo silencio -durante 75s   # nginx por defecto")
        cliente("-modo", "silencio", "-durante", "75s", mostrar="-modo silencio -durante 75s   # directo, sin nginx")
        p("")
        p("== 3 · El arreglo ==")
        nginx(CON_GZIP)
        cliente("-url", "http://sd-proxy", "-modo", "sse", "-sin-buffer",
                mostrar="-url http://sd-proxy -modo sse -sin-buffer   # gzip on, y el servidor manda X-Accel-Buffering: no")
        p("$ cat nginx.conf   # sin gzip para text/event-stream · Upgrade y Connection · proxy_read_timeout 1h")
        nginx(ARREGLADO)
        cliente("-url", "http://sd-proxy", "-modo", "sse", mostrar="-url http://sd-proxy -modo sse")
        cliente("-url", "http://sd-proxy", "-modo", "ws", mostrar="-url http://sd-proxy -modo ws")
        cliente("-url", "http://sd-proxy", "-modo", "silencio", "-durante", "75s",
                mostrar="-url http://sd-proxy -modo silencio -durante 75s")
        salida.append("```")
    finally:
        limpiar()
    (AQUI / "SALIDA.md").write_bytes(("\n".join(cab) + "\n" + "\n".join(salida) + "\n").encode("utf-8"))
    print("\n[ok] SALIDA.md")


if __name__ == "__main__":
    main()
