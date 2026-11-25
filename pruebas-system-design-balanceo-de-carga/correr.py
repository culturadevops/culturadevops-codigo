# -*- coding: utf-8 -*-
"""correr.py — banco del vídeo «System design: balanceo de carga, medido» (cultura-devops, vídeo 345).

Tres réplicas de una API (replica/servidor.py): r1 y r2 responden en 10 ms, r3 en 200 ms (la lenta).
Delante, HAProxy 3.4.6 o nginx 1.30.5, y un generador de carga en Go (carga/) que mide p50, p99,
errores y a qué réplica fue cada petición. Todo en una red de Docker (10.77.21.0/24).

  1  cada réplica sola · 2  algoritmos en HAProxy (roundrobin, leastconn, source) y en nginx
  3  una réplica cae a mitad de carga: sin chequeo, chequeo activo (HAProxy), pasivo (nginx)
  4  L4 contra L7 con conexiones que se reutilizan

    python correr.py      -> SALIDA.md
"""
import datetime
import os
import subprocess
import threading
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ENV = dict(os.environ, MSYS_NO_PATHCONV="1")
RED, SUBRED = "sd-lb", "10.77.21.0/24"
HAPROXY, NGINX, PY, GO = "haproxy:3.4.6-alpine", "nginx:1.30.5-alpine", "python:3.13-slim", "golang:1.27.2"
REPLICAS = {"r1": ("10.77.21.11", 10), "r2": ("10.77.21.12", 10), "r3": ("10.77.21.13", 200)}
LB_IP = "10.77.21.10"
# El servidor corre bajo un sh que sigue vivo cuando Python muere: así «se cae el proceso» deja el
# contenedor (y su IP) en pie, y el puerto RECHAZA conexiones, en vez de desaparecer la máquina.
SERVIR = "python /app/servidor.py; echo 'el proceso ha muerto'; sleep infinity"
salida = []


def p(t=""):
    print(t, flush=True)
    salida.append(t)


def docker(*a, check=False):
    r = subprocess.run(["docker", *a], capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    if check and r.returncode:
        raise SystemExit(f"[X] docker {' '.join(a[:3])}: {r.stdout}{r.stderr}")
    return (r.stdout + r.stderr).strip()


def limpiar():
    docker("rm", "-f", "sd-lb", *REPLICAS)
    docker("network", "rm", RED)


def replicas():
    for n, (ip, ms) in REPLICAS.items():
        docker("run", "-d", "--name", n, "--network", RED, "--ip", ip, "-e", f"NOMBRE={n}", "-e", f"RETRASO_MS={ms}",
               "-v", f"{(AQUI / 'replica').as_posix()}:/app:ro", PY, "sh", "-c", SERVIR, check=True)
    time.sleep(2)


def compilar_carga():
    """El generador se compila UNA vez (binario estático en carga/carga): así cada medición arranca al
    momento, y «a los 3 s» es a los 3 s de carga y no de compilar."""
    docker("run", "--rm", "-v", f"{(AQUI / 'carga').as_posix()}:/w", "-w", "/w", "-e", "CGO_ENABLED=0",
           "-v", "fab-go-mod:/go/pkg/mod", "-v", "fab-go-cache:/root/.cache/go-build", GO,
           "go", "build", "-o", "carga", ".", check=True)


def carga(*args):
    """El generador, dentro de la red."""
    return docker("run", "--rm", "--network", RED, "-v", f"{(AQUI / 'carga').as_posix()}:/w:ro", "alpine:3.22",
                  "/w/carga", *args)


def haproxy(balance, modo="http", check=False, extra="", pesos=None):
    chk = " check inter 1s fall 3 rise 2" if check else ""
    pesos = pesos or {}
    servidores = "\n".join(f"  server {n} {ip}:8000{chk}" + (f" weight {pesos[n]}" if n in pesos else "")
                           for n, (ip, _) in REPLICAS.items())
    cfg = f"""global
  log stdout format raw local0 info
defaults
  mode {modo}
  log global
  timeout connect 1s
  timeout client 10s
  timeout server 10s
frontend web
  bind :80
  default_backend api
backend api
  balance {balance}
{"  option httpchk GET /salud" if check and modo == "http" else ""}
{extra}
{servidores}
"""
    (AQUI / "haproxy" / "haproxy.cfg").write_text(cfg, encoding="utf-8", newline="\n")
    docker("rm", "-f", "sd-lb")
    docker("run", "-d", "--name", "sd-lb", "--network", RED, "--ip", LB_IP,
           "-v", f"{(AQUI / 'haproxy').as_posix()}:/usr/local/etc/haproxy:ro", HAPROXY, check=True)
    time.sleep(2)
    return cfg


def nginx(metodo=""):
    servidores = "\n".join(f"    server {ip}:8000;" for _, (ip, _) in REPLICAS.items())
    conf = f"""events {{}}
http {{
  upstream api {{
    {metodo + ";" if metodo else "# round robin (por defecto)"}
{servidores}
  }}
  server {{
    listen 80;
    location / {{
      proxy_pass http://api;
      proxy_http_version 1.1;
      proxy_set_header Connection "";
      proxy_connect_timeout 1s;
    }}
  }}
}}
"""
    (AQUI / "nginx" / "nginx.conf").write_text(conf, encoding="utf-8", newline="\n")
    docker("rm", "-f", "sd-lb")
    docker("run", "-d", "--name", "sd-lb", "--network", RED, "--ip", LB_IP,
           "-v", f"{(AQUI / 'nginx' / 'nginx.conf').as_posix()}:/etc/nginx/nginx.conf:ro", NGINX, check=True)
    time.sleep(2)
    return conf


def caida(etiqueta):
    """Carga durante 12 s; a los 3 s, el proceso de r2 muere (el contenedor sigue: conexión rechazada)."""
    p(f"$ carga -durante 12s   ({etiqueta}; a los 3 s muere el proceso de r2)")
    # Python no es el PID 1 (lo es el sh de SERVIR), así que muere de verdad; el contenedor sigue vivo
    # y su puerto rechaza conexiones, como un proceso que se cae en una máquina sana.
    o = carga("-url", f"http://{LB_IP}/", "-c", "10", "-durante", "12s",
              "-morir-a", "3s", "-morir-url", f"http://{REPLICAS['r2'][0]}:8000/morir")
    for l in o.splitlines():
        p(l)
    # Revivir r2 DENTRO del mismo contenedor (sigue vivo por el sh de SERVIR). Borrarlo y crear otro con
    # la misma IP al momento lo dejaba inalcanzable en la prueba siguiente (medido: 0 peticiones a r2).
    docker("exec", "-d", "r2", "python", "/app/servidor.py")
    time.sleep(2)
    p(f"  (r2 vuelve a arrancar para la prueba siguiente: {docker('exec', 'r2', 'cat', '/tmp/pid') and 'en marcha'})")


def main():
    cab = ["# SALIDA — «System design: balanceo de carga, medido» (cultura-devops, vídeo 345)", "",
           "> Generado por `correr.py`. **No se escribe a mano.**", "",
           f"- fecha: `{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%SZ}`",
           f"- `{docker('run', '--rm', HAPROXY, 'haproxy', '-v').splitlines()[0]}`",
           f"- `{docker('run', '--rm', '--entrypoint', 'nginx', NGINX, '-v')}`",
           "- réplicas: r1 y r2 responden en 10 ms, r3 en 200 ms (la lenta). Una sola máquina: los "
           "tiempos son de esta, y lo que cuenta es la comparación."]
    limpiar()
    docker("network", "create", "--subnet", SUBRED, RED, check=True)
    compilar_carga()
    try:
        replicas()
        salida.append("\n```")
        p("== 1 · Cada réplica, sin balanceador ==")
        for n, (ip, _) in REPLICAS.items():
            p(f"$ carga -url http://{n}:8000/ -n 200 -c 5")
            for l in carga("-url", f"http://{ip}:8000/", "-n", "200", "-c", "5").splitlines():
                p(l)

        p("")
        p("== 2 · Tres algoritmos en HAProxy (3.000 peticiones, 30 clientes) ==")
        for b in ("roundrobin", "leastconn", "source"):
            haproxy(b)
            p(f"$ HAProxy · balance {b}")
            for l in carga("-url", f"http://{LB_IP}/", "-n", "3000", "-c", "30").splitlines():
                p(l)

        p("")
        p("== 2b · Lo mismo en nginx ==")
        for m in ("", "least_conn", "ip_hash"):
            nginx(m)
            p(f"$ nginx · {m or 'round robin (por defecto)'}")
            for l in carga("-url", f"http://{LB_IP}/", "-n", "3000", "-c", "30").splitlines():
                p(l)

        p("")
        p("== 3 · Una réplica se cae a mitad de carga ==")
        haproxy("roundrobin")
        caida("HAProxy sin chequeos")
        haproxy("roundrobin", check=True)
        caida("HAProxy con chequeo activo: GET /salud cada 1 s, 3 fallos = fuera")
        p("$ docker logs sd-lb | grep -i down")
        p(docker("logs", "sd-lb").count("is DOWN") and
          "\n".join(l for l in docker("logs", "sd-lb").splitlines() if "is DOWN" in l)[:300] or "(nada)")
        nginx()
        caida("nginx: chequeo pasivo (max_fails=1, fail_timeout=10s) y reintento en otra réplica")

        p("")
        p("== 4 · L4 contra L7, con 2 clientes que reutilizan su conexión (300 peticiones) ==")
        haproxy("roundrobin", modo="tcp")
        p("$ HAProxy · mode tcp (L4): reparte CONEXIONES")
        for l in carga("-url", f"http://{LB_IP}/", "-n", "300", "-c", "2", "-keepalive=true").splitlines():
            p(l)
        haproxy("roundrobin", modo="http")
        p("$ HAProxy · mode http (L7): reparte PETICIONES")
        for l in carga("-url", f"http://{LB_IP}/", "-n", "300", "-c", "2", "-keepalive=true").splitlines():
            p(l)
        salida.append("```")
    finally:
        limpiar()
    (AQUI / "SALIDA.md").write_bytes(("\n".join(cab) + "\n" + "\n".join(salida) + "\n").encode("utf-8"))
    print("\n[ok] SALIDA.md")


if __name__ == "__main__":
    main()
