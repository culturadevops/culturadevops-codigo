# -*- coding: utf-8 -*-
"""correr.py — banco del vídeo «System design: almacenamiento en bloque, en fichero o de objetos» (cd, 356).

Los tres en memoria, para medir el camino de acceso y no el disco (la máquina renderiza vídeo a la vez):
  · bloque:  un dispositivo loop con ext4, montado en el cliente
  · fichero: NFSv4 desde el contenedor «nfs» (nfsd del kernel, exporta un tmpfs), montado en el cliente
  · objetos: MinIO (datos en tmpfs), API S3 con boto3
Un solo contenedor cliente, privilegiado (monta el loop y el NFS), hace todas las mediciones (lab.py).

  1 escribir 2.000 ficheros de 4 KB · 2 listarlos · 3 renombrar la carpeta · 4 añadir 1.000 líneas a un fichero
  5 leer ficheros sueltos

    python correr.py      -> SALIDA.md
"""
import datetime
import os
import subprocess
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ENV = dict(os.environ, MSYS_NO_PATHCONV="1")
RED, SUBRED = "sd-alm", "10.77.29.0/24"
CLIENTE, MINIO = "sd-alm-cliente:1", "minio/minio:latest"
salida = []
PRIO = ["--cpu-shares", "8192"]


def p(t=""):
    print(t, flush=True)
    salida.append(t)


def docker(*a, check=False):
    r = subprocess.run(["docker", *a], capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)
    if check and r.returncode:
        raise SystemExit(f"[X] docker {' '.join(a[:3])}: {r.stdout}{r.stderr}")
    return (r.stdout + r.stderr).strip()


def limpiar():
    docker("rm", "-f", "nfs", "minio", "alm-cliente")
    docker("network", "rm", RED)


def main():
    if not docker("images", "-q", CLIENTE):
        (AQUI / "_cliente").mkdir(exist_ok=True)
        (AQUI / "_cliente" / "Dockerfile").write_text(
            "FROM python:3.13-slim\nRUN apt-get update && apt-get install -y --no-install-recommends nfs-common e2fsprogs "
            "&& rm -rf /var/lib/apt/lists/* && pip install --no-cache-dir boto3==1.35.36\n", encoding="utf-8")
        docker("build", "-t", CLIENTE, str(AQUI / "_cliente"), check=True)
    # el kernel de la máquina virtual de Docker trae nfs y nfsd como módulos: se cargan una vez
    docker("run", "--rm", "--privileged", "--pid=host", "alpine:3.22", "nsenter", "-t", "1", "-m", "--",
           "sh", "-c", "modprobe nfs; modprobe nfsd")
    limpiar()
    docker("network", "create", "--subnet", SUBRED, RED, check=True)
    try:
        docker("run", "-d", "--name", "nfs", "--hostname", "nfs", "--network", RED, "--privileged", *PRIO,
               "--tmpfs", "/export:size=1g", "alpine:3.22", "sh", "-c",
               "apk add --no-cache nfs-utils >/dev/null && "
               "echo '/export *(rw,fsid=0,no_subtree_check,no_root_squash,sync)' > /etc/exports && "
               "mount -t nfsd nfsd /proc/fs/nfsd && echo 10 > /proc/fs/nfsd/nfsv4gracetime && "
               "echo 10 > /proc/fs/nfsd/nfsv4leasetime && rpc.mountd -N 3 && rpc.nfsd -N 3 8 && exportfs -ra && "
               "echo NFS-LISTO && exec sleep infinity", check=True)
        docker("run", "-d", "--name", "minio", "--hostname", "minio", "--network", RED, *PRIO,
               "--tmpfs", "/data:size=1g", "-e", "MINIO_ROOT_USER=lab", "-e", "MINIO_ROOT_PASSWORD=lab12345",
               MINIO, "server", "/data", check=True)
        for _ in range(120):
            if "NFS-LISTO" in docker("logs", "nfs") and "API:" in docker("logs", "minio"):
                break
            time.sleep(1)
        else:
            raise SystemExit("[X] nfs o minio no arrancan:\n" + docker("logs", "nfs") + "\n" + docker("logs", "minio")[-500:])
        # NFSv4 arranca con un periodo de gracia (90 s por defecto, aquí 10) en el que no deja crear
        # ficheros: la primera tanda medida pagaba ~290 ms por fichero. Se espera a que pase.
        time.sleep(15)
        version_minio = docker("exec", "minio", "minio", "--version").splitlines()[0]
        cab = ["# SALIDA — «System design: almacenamiento en bloque, en fichero o de objetos» (cultura-devops, vídeo 356)",
               "", "> Generado por `correr.py`. **No se escribe a mano.**", "",
               f"- fecha: `{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M:%SZ}`",
               "- bloque: dispositivo loop con ext4 · fichero: NFSv4 (nfsd del kernel, export sync) · objetos: "
               f"{version_minio}, API S3 con boto3 1.35.36",
               "- los tres sobre memoria (tmpfs): se mide el camino de acceso, no el disco. Cliente y servidores en la "
               "misma máquina, por la red de Docker, sin renders a la vez.",
               "- una sola máquina; una sola conexión, operaciones una detrás de otra. NFS: periodo de gracia de 10 s, "
               "y se mide cuando ya pasó."]
        salida.append("\n```")
        out = docker("run", "--rm", "--name", "alm-cliente", "--network", RED, "--privileged", *PRIO,
                     "-v", f"{AQUI.as_posix()}:/lab", "-w", "/lab", CLIENTE,
                     "python", "lab.py", "pequenos", "listar", "renombrar", "anadir", "leer")
        titulos = {"pequenos": "== 1 · Escribir 2.000 ficheros de 4 KB ==", "listar": "== 2 · Listarlos ==",
                   "renombrar": "== 3 · Renombrar la carpeta (fotos → fotos-2026) ==",
                   "anadir": "== 4 · Añadir 1.000 líneas de 35 bytes a un registro ==",
                   "leer": "== 5 · Leer 1.000 ficheros sueltos de 4 KB =="}
        for l in out.splitlines():
            if l.startswith("$ python lab.py "):
                if salida[-1] != "\n```":
                    p("")
                p(titulos[l.split()[-1]])
            p(l)
        salida.append("```")
    finally:
        limpiar()
    (AQUI / "SALIDA.md").write_bytes(("\n".join(cab) + "\n" + "\n".join(salida) + "\n").encode("utf-8"))
    print("\n[ok] SALIDA.md")


if __name__ == "__main__":
    main()
