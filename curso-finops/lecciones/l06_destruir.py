# -*- coding: utf-8 -*-
"""Lección 6 · El guion de destrucción: `tofu destroy` y la factura en cero... ¿seguro?

Un entorno de pruebas entero con OpenTofu, contra moto en modo servidor. Mientras está encendido,
alguien hace «una prueba rápida» a mano: un disco y una IP. `tofu destroy` dice que lo ha borrado
todo, y es verdad: todo lo SUYO. Lo hecho a mano no lo conoce, y sigue cobrando.
La defensa: default_tags marca lo que crea tofu, y el cazador busca lo que no lleva la marca.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import boto3

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import cazador as CZ  # noqa: E402
import precios as PR  # noqa: E402

PUERTO = 5055
EP = f"http://127.0.0.1:{PUERTO}"
servidor = subprocess.Popen([sys.executable, "-m", "moto.server", "-p", str(PUERTO)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    ec2 = CZ.cliente(EP)
    for _ in range(50):
        try:
            ami = ec2.describe_images(Owners=["amazon"])["Images"][0]["ImageId"]
            break
        except Exception:
            time.sleep(0.2)
    dirt = Path(tempfile.mkdtemp(prefix="finops-"))
    shutil.copy(RAIZ / "infra" / "main.tf", dirt)
    env = dict(os.environ, TF_IN_AUTOMATION="1", TF_VAR_ami=ami, TF_VAR_endpoint=EP)

    def tofu(*args):
        r = subprocess.run(["tofu", *args, "-no-color"], cwd=dirt, capture_output=True, text=True, env=env)
        if r.returncode != 0:
            raise SystemExit(f"tofu {args[0]}: {r.stderr[-800:]}")
        return r.stdout

    tofu("init", "-input=false")
    print("\n== 6.1 · tofu apply: el entorno de pruebas ==")
    print("  " + next(l for l in tofu("apply", "-auto-approve", "-input=false").splitlines() if "Apply complete" in l))
    CZ.informe(CZ.cazar(ec2, "Gestion"), "lo que cobra (dueño = etiqueta Gestion)")

    print("\n== 6.2 · «Una prueba rápida», a mano ==")
    v = ec2.create_volume(AvailabilityZone="us-east-1a", Size=100, VolumeType="gp3")["VolumeId"]
    ip = ec2.allocate_address(Domain="vpc")["PublicIp"]
    print(f"  aws ec2 create-volume --size 100  -> {v}")
    print(f"  aws ec2 allocate-address          -> {ip}")

    print("\n== 6.3 · tofu destroy ==")
    print("  " + next(l for l in tofu("destroy", "-auto-approve", "-input=false").splitlines() if "Destroy complete" in l))
    restos = CZ.cazar(ec2, "Gestion")
    total = CZ.informe(restos, "lo que SIGUE cobrando")
    print(f"  cazador: código de salida {1 if restos else 0} · en un año: {PR.usd(total * 12)}")

    print("\n== 6.4 · Lo que no lleva la marca de tofu: se hizo a mano ==")
    for tipo, rid, det, dueno, coste in restos:
        if dueno == "(sin etiqueta)":
            print(f"  {tipo:15s} {rid:24s} sin «Gestion» -> nadie lo va a destruir con tofu")
finally:
    servidor.terminate()
