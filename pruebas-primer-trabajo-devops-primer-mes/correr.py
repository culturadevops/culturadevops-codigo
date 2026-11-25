# -*- coding: utf-8 -*-
"""Tu primer incidente: un 502 de principio a fin — banco del vídeo 390 (cultura-devops). Escribe SALIDA.md.

Un nginx hace de proxy hacia un servicio en 127.0.0.1:8080 que NO está escuchando. Se diagnostica como
el primer día de guardia: qué ve el usuario (curl), qué dice el registro (docker logs), qué escucha la
máquina (netstat), se arranca el servicio (nginx -s reload con su bloque) y se comprueba.

    python correr.py
"""
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
IMG = "nginx:1.30.5-alpine"
N = "incidente-502"
partes = []


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (r.stdout + r.stderr).strip()


def ex(orden):
    return run(["docker", "exec", N, "sh", "-c", orden])


def anotar(titulo, mostrar, txt):
    partes.extend(["", f"## {titulo}", "", f"`$ {mostrar}`", "", "```", txt or "(sin salida)", "```"])
    print(f"== {titulo}\n$ {mostrar}\n{txt}\n")


run(["docker", "rm", "-f", N])
run(["docker", "run", "-d", "--name", N, "-v", f"{AQUI / 'default.conf'}:/etc/nginx/conf.d/default.conf:ro",
     "-v", f"{AQUI / 'servicio.conf.apagado'}:/servicio.conf.apagado:ro", IMG])
time.sleep(2)
anotar("1 · Lo que ve el usuario", "curl -sI http://localhost/ | head -1", ex("curl -sI http://localhost/ | head -1"))
anotar("2 · Lo que dice el registro", "docker logs incidente-502 2>&1 | grep error | tail -1",
       run(["docker", "logs", N]).splitlines()[-1] if run(["docker", "logs", N]) else "")
anotar("3 · Lo que escucha la máquina", "netstat -tln | grep LISTEN", ex("netstat -tln | grep LISTEN"))
anotar("4 · Arrancar el servicio", "cp servicio.conf /etc/nginx/conf.d/ && nginx -s reload",
       ex("cp /servicio.conf.apagado /etc/nginx/conf.d/servicio.conf && nginx -s reload 2>&1; echo recargado"))
time.sleep(1)
anotar("5 · Comprobar", "netstat -tln | grep LISTEN", ex("netstat -tln | grep LISTEN"))
anotar("6 · Lo que ve el usuario ahora", "curl -s -i http://localhost/ | sed -n '1p;$p'",
       ex("curl -s -i http://localhost/ | sed -n '1p;$p'"))
anotar("7 · Otro clásico: un nombre que no resuelve", "nslookup api.interna",
       ex("nslookup api.interna 2>&1 | tail -3"))
anotar("8 · Y lo que ve el programa", "curl -s http://api.interna/; echo \"código de salida: $?\"",
       ex("curl -s http://api.interna/; echo \"código de salida: $?\""))
anotar("9 · El tercero: un certificado caducado", "curl -sS https://expired.badssl.com/ -o /dev/null",
       ex("curl -sS https://expired.badssl.com/ -o /dev/null 2>&1; echo \"código de salida: $?\""))
anotar("10 · Cuándo caducó", "openssl s_client … | openssl x509 -noout -enddate",
       ex("echo | openssl s_client -connect expired.badssl.com:443 -servername expired.badssl.com 2>/dev/null "
          "| openssl x509 -noout -enddate 2>&1 || echo 'sin openssl en la imagen'"))
run(["docker", "rm", "-f", N])
cab = ["# SALIDA — tu primer incidente: un 502 (ejecutado)", "",
       "Generado por `python correr.py`. **No se edita a mano.**", "",
       f"- fecha: {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC", f"- imagen: {IMG}"]
(AQUI / "SALIDA.md").write_text("\n".join(cab + partes) + "\n", encoding="utf-8")
print("→ SALIDA.md")
