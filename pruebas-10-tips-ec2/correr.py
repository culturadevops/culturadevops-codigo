# -*- coding: utf-8 -*-
"""10 tips para EC2 — demos ejecutables con la AWS CLI contra un emulador (moto). SALIDA.md.

⚠️ moto emula la API, no la factura ni todos los valores por defecto de AWS. Lo que cuesta y los
   valores por defecto los dice la documentación (EXPEDIENTE.md). Aquí se enseña lo que se VE.

    python correr.py
"""
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PUERTO = 5089
EP = f"http://127.0.0.1:{PUERTO}"
ENV = dict(os.environ, AWS_ACCESS_KEY_ID="test", AWS_SECRET_ACCESS_KEY="test",
           AWS_DEFAULT_REGION="us-east-1", AWS_ENDPOINT_URL=EP, AWS_PAGER="",
           PYTHONIOENCODING="utf-8")
partes = []


def aws(*args, mostrar=None, guardar=True):
    r = subprocess.run(["aws", *args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=ENV, cwd=AQUI)
    txt = (r.stdout + r.stderr).strip()
    if guardar:
        partes.extend(["", f"`$ aws {mostrar or ' '.join(args)}`", "", "```", txt or "(sin salida)", "```"])
        print(f"$ aws {mostrar or ' '.join(args)}\n{txt}\n", flush=True)
    return txt


def titulo(t):
    partes.extend(["", f"## {t}"])
    print(f"\n=== {t}", flush=True)


def main():
    moto = subprocess.Popen([sys.executable, "-m", "moto.server", "-p", str(PUERTO)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(EP + "/moto-api/", timeout=1)
                break
            except Exception:
                time.sleep(0.5)
        urllib.request.urlopen(urllib.request.Request(EP + "/moto-api/reset", method="POST"))
        import moto as moto_pkg
        ami = aws("ec2", "describe-images", "--owners", "amazon", "--query", "Images[0].ImageId",
                  "--output", "text", guardar=False)
        cab = ["# SALIDA — 10 tips para EC2 (demos ejecutadas)", "",
               "Generado por `python correr.py`. **No se edita a mano.**", "",
               f"- fecha: {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC",
               f"- {subprocess.run(['aws', '--version'], capture_output=True, text=True).stdout.strip()}",
               f"- moto {moto_pkg.__version__} (emulador de la API de AWS)",
               "- moto emula la API, no la factura: los costos los dice la documentación."]

        titulo("Un volumen que sobrevive a su instancia")
        inst = aws("ec2", "run-instances", "--image-id", ami, "--instance-type", "t3.micro",
                   "--query", "Instances[0].InstanceId", "--output", "text",
                   mostrar="ec2 run-instances --image-id <ami> --instance-type t3.micro")
        vol = aws("ec2", "create-volume", "--availability-zone", "us-east-1a", "--size", "100",
                  "--volume-type", "gp2", "--query", "VolumeId", "--output", "text")
        aws("ec2", "attach-volume", "--volume-id", vol, "--instance-id", inst, "--device", "/dev/sdf",
            "--query", "State", mostrar="ec2 attach-volume --volume-id <vol> --instance-id <i> --device /dev/sdf")
        aws("ec2", "terminate-instances", "--instance-ids", inst,
            "--query", "TerminatingInstances[0].CurrentState.Name",
            mostrar="ec2 terminate-instances --instance-ids <i>")
        aws("ec2", "describe-volumes", "--filters", "Name=status,Values=available",
            "--query", "Volumes[].{Id:VolumeId,GiB:Size,Tipo:VolumeType,Estado:State}")

        titulo("gp2 a gp3 sin parar nada")
        aws("ec2", "describe-volumes", "--filters", "Name=volume-type,Values=gp2",
            "--query", "Volumes[].{Id:VolumeId,GiB:Size,Tipo:VolumeType}")
        aws("ec2", "modify-volume", "--volume-id", vol, "--volume-type", "gp3",
            "--query", "VolumeModification.{De:OriginalVolumeType,A:TargetVolumeType,Estado:ModificationState}",
            mostrar="ec2 modify-volume --volume-id <vol> --volume-type gp3")

        titulo("Una IP elástica sin asociar")
        aws("ec2", "allocate-address", "--domain", "vpc", "--query", "PublicIp", "--output", "text")
        aws("ec2", "describe-addresses",
            "--query", "Addresses[?AssociationId==null].{IP:PublicIp,Asociada:AssociationId}")

        titulo("IMDSv2 obligatorio al lanzar")
        i2 = aws("ec2", "run-instances", "--image-id", ami, "--instance-type", "t3.micro",
                 "--metadata-options", "HttpEndpoint=enabled,HttpTokens=required,HttpPutResponseHopLimit=2",
                 "--query", "Instances[0].InstanceId", "--output", "text",
                 mostrar="ec2 run-instances --image-id <ami> --instance-type t3.micro "
                         "--metadata-options HttpEndpoint=enabled,HttpTokens=required,HttpPutResponseHopLimit=2")
        aws("ec2", "describe-instances", "--instance-ids", i2,
            "--query", "Reservations[0].Instances[0].MetadataOptions.{HttpTokens:HttpTokens,Hops:HttpPutResponseHopLimit}",
            mostrar="ec2 describe-instances --instance-ids <i> --query ...MetadataOptions")

        titulo("Cifrado de EBS por defecto (por región)")
        aws("ec2", "get-ebs-encryption-by-default")
        aws("ec2", "enable-ebs-encryption-by-default")
        aws("ec2", "get-ebs-encryption-by-default")

        (AQUI / "SALIDA.md").write_text("\n".join(cab + partes) + "\n", encoding="utf-8")
        print("SALIDA.md escrito")
    finally:
        moto.terminate()


if __name__ == "__main__":
    main()
