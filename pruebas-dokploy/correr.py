# -*- coding: utf-8 -*-
"""Dokploy — banco de pruebas del vídeo 333 (cultura-devops, serie herramientas).

Dokploy con su instalador oficial, DENTRO de un docker:dind (puertos 3300→3000, 8089→80,
8444→443). ⚠️ El instalador se niega a correr en un contenedor (mira /.dockerenv): en el
laboratorio se borra ese archivo; en un VPS de verdad no hace falta. Se dice en el vídeo.
El resto va por flujo.js (Playwright + la API REST con la sesión del navegador).

    python correr.py
"""
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PUB = Path(r"<proyecto>\motor\remotion\public\om-projects\cultura-devops\dokploy")
D = "dokploy-dind"
salida = []


def sh(cmd, timeout=1800):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return (r.stdout + r.stderr).strip()


def x(script, timeout=1800):
    return sh(["docker", "exec", D, "sh", "-c", script], timeout=timeout)


def anota(titulo, cmd_txt, texto):
    salida.extend(["", f"### {titulo}", "", f"`$ {cmd_txt}`", "", "```", texto.strip(), "```"])
    print(f"--- {titulo}\n{texto.strip()[:1500]}\n", flush=True)


def limpio(t):
    return re.sub(r"\x1b\[[0-9;]*m", "", t)


def main():
    sh(["docker", "rm", "-f", D])
    sh(["docker", "volume", "rm", "-f", "dokploy-dind-data"])
    sh(["docker", "run", "-d", "--privileged", "--name", D, "-p", "3300:3000", "-p", "8089:80",
        "-p", "8444:443", "-v", "dokploy-dind-data:/var/lib/docker", "docker:dind"])
    for _ in range(60):
        if "Server Version" in x("docker info 2>/dev/null | grep 'Server Version'"):
            break
        time.sleep(2)
    x("apk add --no-cache curl openssl bash iproute2 >/dev/null")

    salida.append("\n## 1 · Instalar")
    anota("el instalador dentro de un contenedor", "curl -sSL https://dokploy.com/install.sh | sh",
          limpio(x("curl -sSL https://dokploy.com/install.sh | sh 2>&1 | tail -3; echo codigo=$?")))
    t0 = time.time()
    r = x("rm -f /.dockerenv; IP=$(ip -4 -o addr show eth0 | awk '{print $4}' | cut -d/ -f1); "
          "curl -sSL https://dokploy.com/install.sh | ADVERTISE_ADDR=$IP sh 2>&1", timeout=3600)
    anota("instalar (sin /.dockerenv)", "curl -sSL https://dokploy.com/install.sh | sh",
          "\n".join(l for l in limpio(r).splitlines()
                    if any(k in l for k in ("Swarm initialized", "Network created", "Congratulations",
                                            "Using advertise", "Please go to", "Generated secure")))
          + f"\n(instalado en {time.time() - t0:.0f} s)")
    for _ in range(90):
        if "200" in sh(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://localhost:3300/register"]):
            break
        time.sleep(2)
    time.sleep(10)
    anota("servicios del swarm", "docker service ls", x("docker service ls --format '{{.Name}}  {{.Replicas}}  {{.Image}}'"))
    anota("contenedores", "docker ps", x("docker ps --format '{{.Names}}  {{.Image}}' | sort"))
    anota("memoria (recién instalado)", "docker stats --no-stream",
          x("docker stats --no-stream --format '{{.Name}} {{.MemUsage}}' | sort"))

    salida.append("\n## 2 · Registro, proyecto, aplicación desde Git, despliegue y dominios (flujo.js)")
    PUB.mkdir(parents=True, exist_ok=True)
    r = sh(["node", str(AQUI / "flujo.js"), str(PUB)], timeout=3600)
    anota("flujo.js", "node flujo.js", r)
    app = re.search(r"APPNAME=(\S+)", r)
    app = app.group(1) if app else "web"

    salida.append("\n## 3 · Comprobar desde fuera")
    anota("servicio de la app", "docker service ls | grep app",
          x(f"docker service ls --format '{{{{.Name}}}}  {{{{.Replicas}}}}  {{{{.Image}}}}' | grep -i {app}"))
    anota("imagen construida", "docker images | grep app", x(f"docker images | grep -i {app} | head -3"))
    time.sleep(5)
    anota("HTTP con el dominio tienda.localhost", "curl -H 'Host: tienda.localhost' http://localhost:8089/",
          sh(["curl", "-s", "-i", "-H", "Host: tienda.localhost", "http://localhost:8089/"]))
    anota("HTTPS con tienda.ejemplo.test (Let's Encrypt imposible en local)",
          "curl -k -v --resolve tienda.ejemplo.test:8444:127.0.0.1 https://tienda.ejemplo.test:8444/",
          "\n".join(l for l in sh(["curl", "-k", "-v", "-s", "--resolve", "tienda.ejemplo.test:8444:127.0.0.1",
                                   "https://tienda.ejemplo.test:8444/"]).splitlines()
                    if any(k in l for k in ("subject:", "issuer:", "HTTP/", "message", "SSL connection"))))
    anota("el certificado que intentó pedir", "docker logs dokploy-traefik | grep -i acme",
          x("docker logs dokploy-traefik 2>&1 | grep -i -E 'acme|certificate|unable' | tail -4 | cut -c1-300"))
    anota("memoria (con la app)", "docker stats --no-stream",
          x("docker stats --no-stream --format '{{.Name}} {{.MemUsage}}' | sort"))

    sh(["docker", "rm", "-f", D])
    sh(["docker", "volume", "rm", "-f", "dokploy-dind-data"])
    cab = ["# SALIDA — Dokploy (vídeo 333)", "",
           f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. "
           "Instalador oficial dentro de docker:dind; app de ejemplo: Dokploy/examples, carpeta go-fiber."]
    (AQUI / "SALIDA.md").write_text("\n".join(cab + salida) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
