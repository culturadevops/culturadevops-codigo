# -*- coding: utf-8 -*-
"""10 tips para Amazon EBS y EFS — demos ejecutables con la AWS CLI contra moto. Escribe SALIDA.md.

    python correr.py
"""
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
from banco_moto import Banco  # noqa: E402

with Banco(AQUI, "10 tips para Amazon EBS y EFS", puerto=5112) as b:
    b.titulo("Un volumen creado con la CLI, solo con lo obligatorio")
    v1 = b.aws("ec2", "create-volume", "--availability-zone", "us-east-1a", "--size", "100",
               "--query", "VolumeId", "--output", "text", guardar=False)
    b.aws("ec2", "describe-volumes", "--volume-ids", v1,
          "--query", "Volumes[0].{Tipo:VolumeType,GiB:Size,Cifrado:Encrypted}",
          mostrar="ec2 create-volume --availability-zone us-east-1a --size 100\n$ aws ec2 describe-volumes --volume-ids <vol>")

    b.titulo("Cifrado por defecto")
    b.aws("ec2", "get-ebs-encryption-by-default", mostrar="ec2 get-ebs-encryption-by-default")
    b.aws("ec2", "enable-ebs-encryption-by-default", mostrar="ec2 enable-ebs-encryption-by-default")
    # El volumen nuevo tras activar el cifrado por defecto NO se enseña: moto 5.2.3 lo crea sin cifrar
    # (AWS lo cifra: «enforce the encryption of the new EBS volumes»). Tampoco las IOPS: moto da null.

    b.titulo("De gp2 a gp3 sin desmontar nada")
    b.aws("ec2", "modify-volume", "--volume-id", v1, "--volume-type", "gp3",
          "--query", "VolumeModification.{Original:OriginalVolumeType,Destino:TargetVolumeType,Estado:ModificationState}",
          mostrar="ec2 modify-volume --volume-id <vol1> --volume-type gp3")
    b.aws("ec2", "describe-volumes", "--volume-ids", v1, "--query", "Volumes[0].VolumeType",
          mostrar="ec2 describe-volumes --volume-ids <vol1> --query Volumes[0].VolumeType")

    b.titulo("Instantáneas")
    s1 = b.aws("ec2", "create-snapshot", "--volume-id", v1, "--description", "antes-de-actualizar",
               "--query", "SnapshotId", "--output", "text", guardar=False)
    b.aws("ec2", "describe-snapshots", "--snapshot-ids", s1,
          "--query", "Snapshots[0].{Volumen:VolumeId!=null,Desc:Description,Estado:State,Cifrada:Encrypted}",
          mostrar="ec2 create-snapshot --volume-id <vol1> --description antes-de-actualizar\n$ aws ec2 describe-snapshots --snapshot-ids <snap>")
    b.aws("ec2", "modify-snapshot-tier", "--snapshot-id", s1, "--storage-tier", "archive",
          mostrar="ec2 modify-snapshot-tier --snapshot-id <snap> --storage-tier archive")

    b.titulo("Los volúmenes huérfanos")
    b.aws("ec2", "describe-volumes", "--filters", "Name=status,Values=available",
          "--query", "Volumes[].{Id:VolumeId,GiB:Size,Tipo:VolumeType}",
          mostrar="ec2 describe-volumes --filters Name=status,Values=available")

    b.titulo("EFS: un sistema de ficheros creado con la CLI")
    fs = b.aws("efs", "create-file-system", "--creation-token", "compartido",
               "--query", "FileSystemId", "--output", "text", guardar=False)
    b.aws("efs", "describe-file-systems", "--file-system-id", fs,
          "--query", "FileSystems[0].{Cifrado:Encrypted,Rendimiento:PerformanceMode,Throughput:ThroughputMode}",
          mostrar="efs create-file-system --creation-token compartido\n$ aws efs describe-file-systems --file-system-id <fs>")
    b.aws("efs", "describe-lifecycle-configuration", "--file-system-id", fs,
          mostrar="efs describe-lifecycle-configuration --file-system-id <fs>")
    b.aws("efs", "put-lifecycle-configuration", "--file-system-id", fs, "--lifecycle-policies",
          '[{"TransitionToIA":"AFTER_30_DAYS"},{"TransitionToArchive":"AFTER_90_DAYS"},{"TransitionToPrimaryStorageClass":"AFTER_1_ACCESS"}]',
          mostrar="efs put-lifecycle-configuration --file-system-id <fs> --lifecycle-policies IA 30 días · Archive 90 · vuelve al primer acceso")
    b.aws("efs", "create-file-system", "--creation-token", "cifrado", "--encrypted",
          "--query", "{Cifrado:Encrypted}", mostrar="efs create-file-system --creation-token cifrado --encrypted")
