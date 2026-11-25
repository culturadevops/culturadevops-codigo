# -*- coding: utf-8 -*-
"""Demo de «Nginx en 5 minutos» (cultura-devops). Todo en Docker, red propia n5min:
  · dos backends (nginx que responden «backend-a» / «backend-b») y un nginx delante que sirve una web estática
    y reparte /api/ entre los dos;
  · un error de sintaxis que `nginx -t` detecta ANTES de recargar (el servidor sigue con la config buena);
  · recargar con tráfico (`nginx -s reload`) contando códigos HTTP;
  · apagar un backend: cuánto tarda cada petición, y el arreglo con proxy_connect_timeout.
    python correr.py   -> SALIDA.md
"""
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
IMG = "nginx:1.31-alpine"
OUT = []

CONF = """events {}
http {
    upstream api {
        server backend-a;
        server backend-b;
    }
    server {
        listen 80;
        location / {
            root /usr/share/nginx/html;
        }
        location /api/ {
            proxy_pass http://api/;
        }
    }
}
"""
ROTA = CONF.replace("server backend-b;", "server backend-b")   # falta el punto y coma
ARREGLO = CONF.replace("proxy_pass http://api/;", "proxy_pass http://api/;\n            proxy_connect_timeout 2s;")
TIEMPOS = ("for i in $(seq 6); do curl -s -o /tmp/r -w '%{http_code} %{time_total}s ' http://web/api/; cat /tmp/r; done")


def run(args, entrada=None):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", input=entrada)
    return (p.stdout + p.stderr).strip(), p.returncode


def ex(cont, cmd):
    return run(["docker", "exec", cont, "sh", "-c", cmd])


def bloque(titulo, mostrado, cont, cmd, nota=None):
    s, rc = ex(cont, cmd)
    OUT.append(f"### {titulo}\n\n`$ {mostrado}`\n\n```\n{s}\n```\n(código de salida {rc})\n" + (f"\n> {nota}\n" if nota else ""))
    print(f"[{rc}] {titulo}")
    return s, rc


def poner_conf(texto):
    run(["docker", "exec", "-i", "web", "sh", "-c", "cat > /etc/nginx/nginx.conf"], entrada=texto)


def limpiar():
    for c in ("web", "backend-a", "backend-b", "cliente"):
        run(["docker", "rm", "-f", c])
    run(["docker", "network", "rm", "n5min"])


def main():
    limpiar()
    run(["docker", "network", "create", "n5min"])
    for n in ("a", "b"):
        run(["docker", "run", "-d", "--name", f"backend-{n}", "--network", "n5min", IMG, "sh", "-c",
             f"echo backend-{n} > /usr/share/nginx/html/index.html && nginx -g 'daemon off;'"])
    run(["docker", "run", "-d", "--name", "web", "--network", "n5min", IMG])
    run(["docker", "run", "-d", "--name", "cliente", "--network", "n5min", "alpine:3.22", "sleep", "infinity"])
    ex("cliente", "apk add -q curl >/dev/null")
    time.sleep(2)
    poner_conf(CONF)
    ex("web", "echo '<h1>Mi tienda</h1>' > /usr/share/nginx/html/index.html && nginx -s reload")
    time.sleep(1)

    OUT.append(f"# SALIDA — Nginx en 5 minutos (cultura-devops)\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con "
               f"`python correr.py`. Imagen `{IMG}`; red de Docker propia; cliente curl en un contenedor Alpine.\n")
    OUT.append("## 1 · Versión y configuración\n")
    bloque("versión", "nginx -v", "web", "nginx -v")
    bloque("la configuración", "cat /etc/nginx/nginx.conf", "web", "cat /etc/nginx/nginx.conf")

    OUT.append("## 2 · Servidor web y proxy inverso\n")
    bloque("la web estática", "curl http://web/", "cliente", "curl -s http://web/")
    bloque("/api/ cuatro veces", "for i in 1 2 3 4; do curl -s http://web/api/; done", "cliente",
           "for i in 1 2 3 4; do curl -s http://web/api/; done")

    OUT.append("## 3 · Un error de sintaxis\n")
    poner_conf(ROTA)
    bloque("probar antes de recargar", "nginx -t", "web", "nginx -t")
    bloque("¿y la web sigue?", "curl http://web/api/", "cliente", "curl -s http://web/api/")
    poner_conf(CONF)
    bloque("arreglado", "nginx -t", "web", "nginx -t")

    OUT.append("## 4 · Recargar con tráfico\n")
    p = subprocess.Popen(["docker", "exec", "cliente", "sh", "-c",
                          "for i in $(seq 1000); do curl -s -o /dev/null -w '%{http_code}\\n' http://web/api/; done | sort | uniq -c"],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")
    recargas = 0
    while p.poll() is None and recargas < 5:
        time.sleep(0.2)
        ex("web", "nginx -s reload")
        recargas += 1
    salida = p.communicate()[0].strip()
    OUT.append(f"### 1000 peticiones a /api/ mientras se recarga {recargas} veces\n\n"
               f"`$ (1000 x curl -w %{{http_code}} http://web/api/) & nginx -s reload x{recargas}`\n\n```\n{salida}\n```\n")
    print(f"[ok] recargas={recargas} -> {salida!r}")

    OUT.append("## 5 · Se cae un backend\n")
    run(["docker", "stop", "backend-a"])
    bloque("backend-a apagado: 6 peticiones, con su tiempo",
           "docker stop backend-a; for i in $(seq 6); do curl -w '%{http_code} %{time_total}s' http://web/api/; done", "cliente", TIEMPOS)
    logs, _ = run(["docker", "logs", "--tail", "40", "web"])
    err = [l for l in logs.splitlines() if "[error]" in l][-1:]
    OUT.append("### lo que dejó nginx en su registro\n\n`$ docker logs web | grep error | tail -1`\n\n```\n" + "\n".join(err) + "\n```\n")

    OUT.append("## 6 · El arreglo: no esperar tanto\n")
    # ⚠️ Con backend-a parado su nombre no resuelve y `nginx -s reload` falla (host not found): se vuelve a arrancar,
    # se aplica el arreglo y se para otra vez, para medir lo mismo que en la sección 5.
    run(["docker", "start", "backend-a"])
    time.sleep(2)
    poner_conf(ARREGLO)
    bloque("la línea nueva", "grep -n proxy_connect_timeout /etc/nginx/nginx.conf", "web", "grep -n proxy_connect_timeout /etc/nginx/nginx.conf")
    bloque("probar y recargar", "nginx -t && nginx -s reload", "web", "nginx -t && nginx -s reload && echo recargado")
    time.sleep(1)
    run(["docker", "stop", "backend-a"])
    bloque("backend-a apagado otra vez: las mismas 6 peticiones",
           "docker stop backend-a; for i in $(seq 6); do curl -w '%{http_code} %{time_total}s' http://web/api/; done", "cliente", TIEMPOS)

    (AQUI / "SALIDA.md").write_text("\n".join(OUT), encoding="utf-8")
    limpiar()
    print("ok SALIDA.md")


if __name__ == "__main__":
    main()
