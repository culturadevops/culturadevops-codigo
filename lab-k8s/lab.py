# -*- coding: utf-8 -*-
"""Laboratorio de Kubernetes en Docker para los vídeos 328 (Argo CD), 332 (k9s) y 335 (Argo vs Flux).

  · k3s   rancher/k3s en un contenedor privilegiado (no hacen falta binarios en Windows: App
          Control bloquea k3d/kind por hash). kubectl se ejecuta DENTRO del contenedor.
  · gitea un Git local por HTTP, con un usuario y un repositorio de manifiestos.
Red `argo-lab` 10.78.0.0/24 con IP fijas: los pods NO resuelven nombres de la red de Docker
(CoreDNS no ve el DNS 127.0.0.11 del contenedor), así que el repo se apunta por IP.
"""
import json
import subprocess
import tempfile
import time
from pathlib import Path

RED = "argo-lab"
K3S_IP, GITEA_IP = "10.78.0.10", "10.78.0.20"
USUARIO, CLAVE = "dev", "Clave-de-prueba-123"
REPO_URL = f"http://{GITEA_IP}:3000/{USUARIO}/app.git"
HOST_REPO = f"http://{USUARIO}:{CLAVE}@localhost:3000/{USUARIO}/app.git"


def sh(cmd, timeout=900, entrada=None, cwd=None):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout, input=entrada, cwd=cwd)
    return (r.stdout + r.stderr).strip()


def k(*a, entrada=None, timeout=600):
    return sh(["docker", "exec", "-i", "k3s", "kubectl", *a], entrada=entrada, timeout=timeout)


def limpiar():
    sh(["docker", "rm", "-f", "k3s", "gitea"])
    sh(["docker", "network", "rm", RED])


def levantar(puertos_k3s=()):
    limpiar()
    sh(["docker", "network", "create", "--subnet", "10.78.0.0/24", RED])
    pk = [x for p in puertos_k3s for x in ("-p", p)]
    sh(["docker", "run", "-d", "--privileged", "--name", "k3s", "--network", RED, "--ip", K3S_IP,
        *pk, "rancher/k3s:latest", "server", "--disable", "traefik"])
    sh(["docker", "run", "-d", "--name", "gitea", "--network", RED, "--ip", GITEA_IP,
        "-p", "3000:3000", "-e", "GITEA__security__INSTALL_LOCK=true",
        "-e", "GITEA__database__DB_TYPE=sqlite3", "-e", f"GITEA__server__ROOT_URL=http://{GITEA_IP}:3000/",
        "gitea/gitea:latest"])
    for _ in range(180):
        if " Ready" in k("get", "nodes"):
            break
        time.sleep(2)
    for _ in range(60):
        if "200" in sh(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://localhost:3000/api/v1/version"]):
            break
        time.sleep(2)
    sh(["docker", "exec", "-u", "git", "gitea", "gitea", "admin", "user", "create", "--admin",
        "--username", USUARIO, "--password", CLAVE, "--email", "dev@ejemplo.test",
        "--must-change-password=false"])
    sh(["curl", "-s", "-u", f"{USUARIO}:{CLAVE}", "-H", "Content-Type: application/json",
        "-d", json.dumps({"name": "app", "default_branch": "main"}),
        "http://localhost:3000/api/v1/user/repos"])


def levantar_gitea():
    """Solo Gitea (para Renovate y compañía), en la misma red y la misma IP."""
    limpiar()
    sh(["docker", "network", "create", "--subnet", "10.78.0.0/24", RED])
    sh(["docker", "run", "-d", "--name", "gitea", "--network", RED, "--ip", GITEA_IP,
        "-p", "3000:3000", "-e", "GITEA__security__INSTALL_LOCK=true",
        "-e", "GITEA__database__DB_TYPE=sqlite3", "-e", f"GITEA__server__ROOT_URL=http://{GITEA_IP}:3000/",
        "gitea/gitea:latest"])
    for _ in range(60):
        if "200" in sh(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://localhost:3000/api/v1/version"]):
            break
        time.sleep(2)
    sh(["docker", "exec", "-u", "git", "gitea", "gitea", "admin", "user", "create", "--admin",
        "--username", USUARIO, "--password", CLAVE, "--email", "dev@ejemplo.test",
        "--must-change-password=false"])
    sh(["curl", "-s", "-u", f"{USUARIO}:{CLAVE}", "-H", "Content-Type: application/json",
        "-d", json.dumps({"name": "app", "default_branch": "main"}),
        "http://localhost:3000/api/v1/user/repos"])


def crear_repo(nombre):
    sh(["curl", "-s", "-u", f"{USUARIO}:{CLAVE}", "-H", "Content-Type: application/json",
        "-d", json.dumps({"name": nombre, "default_branch": "main"}),
        "http://localhost:3000/api/v1/user/repos"])


def token_gitea(nombre="bot"):
    r = sh(["curl", "-s", "-u", f"{USUARIO}:{CLAVE}", "-H", "Content-Type: application/json",
            "-d", json.dumps({"name": nombre, "scopes": ["all"]}),
            f"http://localhost:3000/api/v1/users/{USUARIO}/tokens"])
    return json.loads(r)["sha1"]


def gitea_api(ruta):
    return json.loads(sh(["curl", "-s", "-u", f"{USUARIO}:{CLAVE}", f"http://localhost:3000/api/v1{ruta}"]) or "null")


DEPLOY = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: {replicas}
  selector:
    matchLabels: {{app: web}}
  template:
    metadata:
      labels: {{app: web}}
    spec:
      containers:
        - name: nginx
          image: nginx:1.29-alpine
          ports: [{{containerPort: 80}}]
"""
SERVICE = """apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  selector: {app: web}
  ports: [{port: 80, targetPort: 80}]
"""
CONFIG = """apiVersion: v1
kind: ConfigMap
metadata:
  name: web-config
data:
  saludo: hola
"""


class Repo:
    """Un clon local del repo de Gitea en una carpeta temporal."""

    def __init__(self, nombre="app"):
        if nombre != "app":
            crear_repo(nombre)
        self.dir = Path(tempfile.mkdtemp(prefix=f"{nombre}-"))
        sh(["git", "init", "-q", "-b", "main"], cwd=self.dir)
        sh(["git", "config", "user.email", "dev@ejemplo.test"], cwd=self.dir)
        sh(["git", "config", "user.name", "dev"], cwd=self.dir)
        sh(["git", "remote", "add", "origin", HOST_REPO.replace("/app.git", f"/{nombre}.git")], cwd=self.dir)

    def escribe(self, nombre, texto):
        (self.dir / nombre).write_bytes(texto.encode("utf-8"))

    def borra(self, nombre):
        sh(["git", "rm", "-q", nombre], cwd=self.dir)

    def commit(self, msg):
        sh(["git", "add", "-A"], cwd=self.dir)
        sh(["git", "commit", "-q", "-m", msg], cwd=self.dir)
        print(sh(["git", "push", "-q", "-u", "origin", "main"], cwd=self.dir))
        return sh(["git", "rev-parse", "HEAD"], cwd=self.dir)

    def log(self):
        return sh(["git", "log", "--oneline"], cwd=self.dir)
