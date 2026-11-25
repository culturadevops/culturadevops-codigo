# -*- coding: utf-8 -*-
"""correr.py — banco del vídeo «System design: el proxy inverso, qué hace de verdad» (cultura-devops, vídeo 349).

nginx 1.30.5 delante de dos instancias de app/ (Go), que comparten datos/ para contar lo que se hizo de
verdad (pagos, procesados). Clientes: curl. Red de Docker 10.77.25.0/24. Una sola máquina.

  1 la IP que ve la aplicación · 2 el 504 a los 60 s · 3 el cliente lento, con y sin buffering
  4 reintentos: un GET con efectos y un POST · 5 el límite de 1 MB · 6 TLS en el proxy

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
RED, SUBRED = "sd-proxy", "10.77.25.0/24"
NGINX, CURL = "nginx:1.30.5-alpine", "curlimages/curl:8.11.1"
salida = []

UPSTREAM = "upstream api { server app1:8000; server app2:8000; }"


def conf(location_extra="", server_extra=""):
    return f"""events {{}}
http {{
  {UPSTREAM}
  server {{
    listen 80;
    listen 443 ssl;
    ssl_certificate /certs/proxy.crt;
    ssl_certificate_key /certs/proxy.key;
    {server_extra}
    location / {{
      proxy_pass http://api;
      {location_extra}
    }}
  }}
}}
"""


def p(t=""):
    print(t, flush=True)
    salida.append(t)


def docker(*a, check=False):
    r = subprocess.run(["docker", *a], capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    if check and r.returncode:
        raise SystemExit(f"[X] docker {' '.join(a[:3])}: {r.stdout}{r.stderr}")
    return (r.stdout + r.stderr).strip()


def curl(args, mostrar):
    p(f"$ curl {mostrar}")
    for l in docker("run", "--rm", "--network", RED, CURL, "-sS", *args).splitlines():
        p("  " + l)


def nginx(texto, etiqueta):
    (AQUI / "nginx.conf").write_text(texto, encoding="utf-8", newline="\n")
    docker("rm", "-f", "proxy")
    docker("run", "-d", "--name", "proxy", "--network", RED, "-v", f"{(AQUI / 'nginx.conf').as_posix()}:/etc/nginx/nginx.conf:ro",
           "-v", f"{(AQUI / 'certs').as_posix()}:/certs:ro", NGINX, check=True)
    time.sleep(2)
    p(f"  [nginx: {etiqueta}]")


def datos(fichero):
    f = AQUI / "datos" / fichero
    return f.read_text(encoding="utf-8").strip().splitlines() if f.exists() else []


def limpiar_datos():
    shutil.rmtree(AQUI / "datos", ignore_errors=True)
    (AQUI / "datos").mkdir()


def limpiar():
    docker("rm", "-f", "proxy", "app1", "app2")
    docker("network", "rm", RED)


def main():
    docker("run", "--rm", "-v", f"{(AQUI / 'app').as_posix()}:/w", "-w", "/w", "-e", "CGO_ENABLED=0", "golang:1.27.2",
           "sh", "-c", "[ -f go.mod ] || go mod init ejemplo.com/app >/dev/null 2>&1; go build -o app .", check=True)
    (AQUI / "certs").mkdir(exist_ok=True)
    docker("run", "--rm", "-v", f"{(AQUI / 'certs').as_posix()}:/c", "alpine/openssl:3.5.4", "req", "-x509", "-newkey", "rsa:2048",
           "-nodes", "-days", "30", "-subj", "/CN=proxy", "-keyout", "/c/proxy.key", "-out", "/c/proxy.crt", check=True)
    cab = ["# SALIDA — «System design: el proxy inverso» (cultura-devops, vídeo 349)", "",
           "> Generado por `correr.py`. **No se escribe a mano.**", "",
           f"- fecha: `{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%SZ}`",
           f"- `{docker('run', '--rm', '--entrypoint', 'nginx', NGINX, '-v')}` · curl 8.11.1 · app en Go 1.27.2 (dos instancias)",
           "- una sola máquina; los tiempos son de esta."]
    limpiar()
    limpiar_datos()
    docker("network", "create", "--subnet", SUBRED, RED, check=True)
    try:
        for n in ("app1", "app2"):
            docker("run", "-d", "--name", n, "--network", RED, "-e", f"NOMBRE={n}", "-v", f"{(AQUI / 'app').as_posix()}:/w:ro",
                   "-v", f"{(AQUI / 'datos').as_posix()}:/datos", "alpine:3.22", "/w/app", check=True)
        salida.append("\n```")
        p("== 1 · ¿Qué IP de cliente ve la aplicación? ==")
        nginx(conf(), "proxy_pass y nada más")
        curl(["http://app1:8000/ip"], "http://app1:8000/ip   # directo")
        curl(["http://proxy/ip"], "http://proxy/ip   # por el proxy")
        nginx(conf("proxy_set_header X-Real-IP $remote_addr;\n      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
                   "      proxy_set_header X-Forwarded-Proto $scheme;"), "con X-Real-IP, X-Forwarded-For y X-Forwarded-Proto")
        curl(["http://proxy/ip"], "http://proxy/ip")
        curl(["-k", "https://proxy/ip"], "-k https://proxy/ip   # TLS termina en el proxy; la app sigue en HTTP")

        p("")
        p("== 2 · Una respuesta que tarda 70 s ==")
        nginx(conf(), "por defecto (proxy_read_timeout 60s)")
        curl(["-o", "/dev/null", "-w", "HTTP %{http_code} a los %{time_total} s\\n", "http://proxy/lento?s=70"],
             "http://proxy/lento?s=70   # por el proxy")
        curl(["-o", "/dev/null", "-w", "HTTP %{http_code} a los %{time_total} s\\n", "http://app1:8000/lento?s=70"],
             "http://app1:8000/lento?s=70   # directo")

        p("")
        p("== 3 · Un cliente lento (2 MB/s) descarga 40 MB: ¿cuánto queda ocupada la aplicación? ==")
        nginx(conf(), "por defecto (proxy_buffering on)")
        curl(["-o", "/dev/null", "--limit-rate", "2M", "-w", "el cliente tardó %{time_total} s\\n", "http://proxy/grande?mb=40"],
             "--limit-rate 2M http://proxy/grande?mb=40")
        p("  la app: " + (datos("grande.log") or ["(nada)"])[-1])
        nginx(conf("proxy_buffering off;"), "proxy_buffering off")
        curl(["-o", "/dev/null", "--limit-rate", "2M", "-w", "el cliente tardó %{time_total} s\\n", "http://proxy/grande?mb=40"],
             "--limit-rate 2M http://proxy/grande?mb=40")
        p("  la app: " + (datos("grande.log") or ["(nada)"])[-1])

        p("")
        p("== 4 · Reintentos: la app tarda 3 s y el proxy espera 2 s ==")
        corto = "proxy_read_timeout 2s;"
        nginx(conf(corto), "proxy_read_timeout 2s · proxy_next_upstream por defecto (error timeout)")
        limpiar_datos()
        curl(["-o", "/dev/null", "-w", "HTTP %{http_code} a los %{time_total} s\\n", "http://proxy/procesar?s=3"],
             "http://proxy/procesar?s=3   # un GET con efectos")
        time.sleep(4)
        for l in datos("procesados.log"):
            p("  procesados.log: " + l)
        curl(["-o", "/dev/null", "-X", "POST", "-w", "HTTP %{http_code} a los %{time_total} s\\n", "http://proxy/pagar?s=3"],
             "-X POST http://proxy/pagar?s=3")
        time.sleep(4)
        for l in datos("pagos.log"):
            p("  pagos.log: " + l)
        nginx(conf(corto + "\n      proxy_next_upstream error timeout non_idempotent;"),
              "… y proxy_next_upstream error timeout non_idempotent")
        limpiar_datos()
        curl(["-o", "/dev/null", "-X", "POST", "-w", "HTTP %{http_code} a los %{time_total} s\\n", "http://proxy/pagar?s=3"],
             "-X POST http://proxy/pagar?s=3")
        time.sleep(4)
        for l in datos("pagos.log"):
            p("  pagos.log: " + l)

        p("")
        p("== 5 · Subir un fichero de 2 MB ==")
        nginx(conf(), "por defecto (client_max_body_size 1m)")
        curl(["-o", "/dev/null", "-w", "HTTP %{http_code}\\n", "-X", "POST", "--data-binary", "@/etc/ssl/certs/ca-certificates.crt",
              "-H", "Content-Type: application/octet-stream", "http://proxy/subir"],
             "--data-binary @ca-certificates.crt http://proxy/subir   # unos 200 KB")
        docker("run", "--rm", "-v", f"{(AQUI / 'datos').as_posix()}:/d", "alpine:3.22", "sh", "-c",
               "head -c 2097152 /dev/urandom > /d/2mb.bin")
        p("$ curl --data-binary @2mb.bin http://proxy/subir")
        for l in docker("run", "--rm", "--network", RED, "-v", f"{(AQUI / 'datos').as_posix()}:/d:ro", CURL, "-sS",
                        "-o", "/dev/null", "-w", "HTTP %{http_code}\\n", "-X", "POST", "--data-binary", "@/d/2mb.bin",
                        "http://proxy/subir").splitlines():
            p("  " + l)
        nginx(conf(server_extra="client_max_body_size 10m;"), "client_max_body_size 10m")
        p("$ curl --data-binary @2mb.bin http://proxy/subir")
        for l in docker("run", "--rm", "--network", RED, "-v", f"{(AQUI / 'datos').as_posix()}:/d:ro", CURL, "-sS",
                        "-X", "POST", "--data-binary", "@/d/2mb.bin", "http://proxy/subir").splitlines():
            p("  " + l)

        p("")
        p("== 6 · TLS en el proxy: lo que cuesta abrir la conexión ==")
        nginx(conf(), "TLS con un certificado autofirmado (RSA 2048)")
        curl(["-k", "-o", "/dev/null", "-w", "conectar %{time_connect} s · TLS listo %{time_appconnect} s · total %{time_total} s\\n",
              "https://proxy/ip"], "-k https://proxy/ip   # una conexión nueva")
        curl(["-o", "/dev/null", "-w", "conectar %{time_connect} s · total %{time_total} s\\n", "http://proxy/ip"],
             "http://proxy/ip   # sin TLS")
        salida.append("```")
    finally:
        limpiar()
    (AQUI / "SALIDA.md").write_bytes(("\n".join(cab) + "\n" + "\n".join(salida) + "\n").encode("utf-8"))
    print("\n[ok] SALIDA.md")


if __name__ == "__main__":
    main()
