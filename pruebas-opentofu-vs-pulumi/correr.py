# -*- coding: utf-8 -*-
"""OpenTofu vs Pulumi — banco de pruebas del vídeo 339 (cultura-devops, serie versus).

La MISMA infraestructura (una red + un contenedor nginx) con el proveedor de Docker, escrita en
HCL (OpenTofu) y en Python (Pulumi), las dos contra un Docker aparte (docker:dind). Se compara:
el código, lo que enseña el plan/preview, el apply, el estado, el borrado, y qué hace cada una
cuando algo cambia por fuera (drift). Red Docker `iac`.

    python correr.py
"""
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
TOFU = "ghcr.io/opentofu/opentofu:latest"
PULUMI = "pulumi/pulumi-python:latest"
DH = "tcp://dind:2375"
salida = []

MAIN_TF = """terraform {
  required_providers {
    docker = { source = "kreuzwerker/docker", version = "~> 3.0" }
  }
}
provider "docker" { host = "tcp://dind:2375" }

resource "docker_network" "red" { name = "tienda-tf" }

resource "docker_image" "nginx" {
  name         = "nginx:1.29-alpine"
  keep_locally = true
}

resource "docker_container" "web" {
  name  = "web-tf"
  image = docker_image.nginx.image_id
  networks_advanced {
    name = docker_network.red.name
  }
  ports {
    internal = 80
    external = 8080
  }
}
"""

PULUMI_PY = """import pulumi
import pulumi_docker as docker

red = docker.Network("red", name="tienda-pulumi")
img = docker.RemoteImage("nginx", name="nginx:1.29-alpine", keep_locally=True)
web = docker.Container("web", name="web-pulumi", image=img.image_id,
    networks_advanced=[docker.ContainerNetworksAdvancedArgs(name=red.name)],
    ports=[docker.ContainerPortArgs(internal=80, external=8081)])
pulumi.export("contenedor", web.name)
"""

PULUMI_YAML = """name: tienda
runtime: python
description: la misma infra que OpenTofu
"""


def sh(cmd, timeout=1800):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return (r.stdout + r.stderr).strip()


def anota(titulo, cmd_txt, texto):
    salida.extend(["", f"### {titulo}", "", f"`$ {cmd_txt}`", "", "```", texto.strip(), "```"])
    print(f"--- {titulo}\n{texto.strip()[:1400]}\n", flush=True)


def tofu(script, timeout=1800):
    return sh(["docker", "run", "--rm", "--network", "iac", "-e", f"DOCKER_HOST={DH}",
               "-v", "iac-tofu:/w", "-w", "/w", "--entrypoint", "sh", TOFU, "-c", script], timeout=timeout)


def pulumi(script, timeout=1800, crudo=False):
    pre = "" if crudo else ("export PYTHONPATH=/w/pylibs; pulumi login file:///w >/dev/null 2>&1; "
                            "pulumi stack select dev >/dev/null 2>&1; ")
    return sh(["docker", "run", "--rm", "--network", "iac", "-e", f"DOCKER_HOST={DH}",
               "-e", "PULUMI_CONFIG_PASSPHRASE=prueba", "-v", "iac-pulumi:/w", "-w", "/w",
               "--entrypoint", "bash", PULUMI, "-c", pre + script], timeout=timeout)


def dind(script):
    return sh(["docker", "exec", "iac-dind", "sh", "-c", script])


def limpio(t):
    import re
    return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", t)


def escribir_en_volumen(vol, archivos):
    import base64
    cmd = " && ".join(f"echo {base64.b64encode(c.encode()).decode()} | base64 -d > /w/{n}" for n, c in archivos.items())
    sh(["docker", "run", "--rm", "-v", f"{vol}:/w", "alpine", "sh", "-c", cmd])


def main():
    sh(["docker", "rm", "-f", "iac-dind"])
    for v in ("iac-tofu", "iac-pulumi"):
        sh(["docker", "volume", "rm", "-f", v])
        sh(["docker", "volume", "create", v])
    sh(["docker", "network", "rm", "iac"])
    sh(["docker", "network", "create", "iac"])
    sh(["docker", "run", "-d", "--privileged", "--name", "iac-dind", "--network", "iac",
        "-e", "DOCKER_TLS_CERTDIR=", "--network-alias", "dind", "docker:dind", "--insecure-registry=0.0.0.0/0"])
    for _ in range(60):
        if "Server Version" in dind("docker info 2>/dev/null | grep 'Server Version'"):
            break
        time.sleep(2)

    salida.append("\n## 1 · La misma infraestructura, dos lenguajes")
    anota("OpenTofu: main.tf (HCL)", "cat main.tf", MAIN_TF)
    anota("Pulumi: __main__.py (Python)", "cat __main__.py", PULUMI_PY)
    anota("líneas de código", "wc -l", f"OpenTofu (HCL): {len(MAIN_TF.strip().splitlines())} líneas\n"
                                        f"Pulumi (Python): {len(PULUMI_PY.strip().splitlines())} líneas")

    escribir_en_volumen("iac-tofu", {"main.tf": MAIN_TF})
    escribir_en_volumen("iac-pulumi", {"__main__.py": PULUMI_PY, "Pulumi.yaml": PULUMI_YAML})

    salida.append("\n## 2 · Preparar")
    anota("OpenTofu: tofu init", "tofu init",
          "\n".join(l for l in limpio(tofu("tofu init -no-color")).splitlines()
                    if "nstall" in l or "initialized" in l or "kreuzwerker" in l)[-800:])
    anota("Pulumi: login local + stack + config", "pulumi login file:// ; stack init ; config set",
          "\n".join(limpio(pulumi(
              "pip install --target=/w/pylibs pulumi_docker -q 2>/dev/null; export PYTHONPATH=/w/pylibs; "
              "pulumi login file:///w 2>&1 | tail -1; "
              "pulumi stack init dev 2>&1 | tail -1; pulumi config set docker:host tcp://dind:2375 2>&1; "
              "echo listo", crudo=True)).splitlines()[-5:]))

    salida.append("\n## 3 · El plan antes de crear nada")
    anota("OpenTofu: tofu plan", "tofu plan",
          "\n".join(l for l in limpio(tofu("tofu plan -no-color")).splitlines()
                    if "will be created" in l or "Plan:" in l or "# docker" in l))
    anota("Pulumi: pulumi preview", "pulumi preview",
          "\n".join(l for l in limpio(pulumi("pulumi preview 2>&1")).splitlines()
                    if "create" in l.lower() or "Resources:" in l or "+ " in l)[-900:])

    salida.append("\n## 4 · Crear")
    t = time.time()
    r = tofu("tofu apply -auto-approve -no-color 2>&1 | tail -4")
    anota("OpenTofu: tofu apply", "tofu apply -auto-approve", limpio(r) + f"\n(en {time.time() - t:.0f} s)")
    t = time.time()
    r = pulumi("pulumi up --yes 2>&1 | tail -6")
    anota("Pulumi: pulumi up", "pulumi up --yes", limpio(r) + f"\n(en {time.time() - t:.0f} s)")
    anota("lo que hay en el Docker destino", "docker ps / network ls",
          dind("docker ps --format '{{.Names}}'; docker network ls --format '{{.Name}}' | grep tienda"))

    salida.append("\n## 5 · El estado")
    anota("OpenTofu: dónde y cómo", "ls; head terraform.tfstate",
          tofu("ls -la terraform.tfstate | awk '{print $5, $9}'; echo ---; "
               "head -c 400 terraform.tfstate"))
    anota("Pulumi: dónde y cómo", "ls .pulumi; stack export | head",
          pulumi("find /w/.pulumi -name '*.json' | head -3; echo ---; pulumi stack export 2>/dev/null | head -c 400"))

    salida.append("\n## 6 · Algo cambia por fuera (drift)")
    dind("docker rm -f web-tf web-pulumi >/dev/null 2>&1; echo borrados")
    anota("borro el contenedor a mano", "docker rm -f web (en el dind)", "contenedor web borrado a mano")
    anota("OpenTofu: lo detecta", "tofu plan",
          "\n".join(l for l in limpio(tofu("tofu plan -no-color 2>&1")).splitlines()
                    if "has been deleted" in l or "will be created" in l or "Plan:" in l or "Note:" in l)[:600])
    anota("Pulumi: lo detecta", "pulumi preview --refresh",
          "\n".join(l for l in limpio(pulumi("pulumi preview --refresh 2>&1")).splitlines()
                    if "create" in l.lower() or "Resources:" in l or "web" in l)[-700:])

    salida.append("\n## 7 · Destruir")
    t = time.time()
    anota("OpenTofu: tofu destroy", "tofu destroy -auto-approve",
          "\n".join(limpio(tofu("tofu apply -auto-approve -no-color >/dev/null 2>&1; tofu destroy -auto-approve -no-color 2>&1 | tail -2")).splitlines()) + f"\n(apply+destroy en {time.time() - t:.0f} s)")
    anota("Pulumi: pulumi destroy", "pulumi destroy --yes",
          "\n".join(limpio(pulumi("pulumi destroy --yes 2>&1 | tail -3")).splitlines()))
    anota("el Docker destino, vacío", "docker ps -a",
          dind("docker ps -a --format '{{.Names}}' | grep -c web | sed 's/^/contenedores web: /' || echo 'contenedores web: 0'"))

    sh(["docker", "rm", "-f", "iac-dind"])
    for v in ("iac-tofu", "iac-pulumi"):
        sh(["docker", "volume", "rm", "-f", v])
    sh(["docker", "network", "rm", "iac"])
    cab = ["# SALIDA — OpenTofu vs Pulumi (vídeo 339)", "",
           f"Generado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr.py`. "
           f"OpenTofu v1.12.7 (HCL) y Pulumi v3.267.0 (Python), la misma infra con el proveedor de Docker."]
    (AQUI / "SALIDA.md").write_text("\n".join(cab + salida) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
