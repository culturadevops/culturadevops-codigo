# -*- coding: utf-8 -*-
"""10 tips para RDS — demos ejecutables con la AWS CLI contra un emulador (moto). SALIDA.md.

⚠️ moto emula la API, no la factura ni todos los valores por defecto de AWS: si un valor del
   emulador no coincide con la documentación de la API, NO se presenta como el de AWS.

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
PUERTO = 5092
EP = f"http://127.0.0.1:{PUERTO}"
ENV = dict(os.environ, AWS_ACCESS_KEY_ID="test", AWS_SECRET_ACCESS_KEY="test",
           AWS_DEFAULT_REGION="us-east-1", AWS_ENDPOINT_URL=EP, AWS_PAGER="",
           PYTHONIOENCODING="utf-8")
partes = []
Q = ("DBInstances[0].{BackupRetentionPeriod:BackupRetentionPeriod,"
     "DeletionProtection:DeletionProtection,StorageEncrypted:StorageEncrypted,"
     "PubliclyAccessible:PubliclyAccessible,StorageType:StorageType,"
     "EngineLifecycleSupport:EngineLifecycleSupport}")


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
        cab = ["# SALIDA — 10 tips para RDS (demos ejecutadas)", "",
               "Generado por `python correr.py`. **No se edita a mano.**", "",
               f"- fecha: {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC",
               f"- {subprocess.run(['aws', '--version'], capture_output=True, text=True).stdout.strip()}",
               f"- moto {moto_pkg.__version__} (emulador de la API de AWS)",
               "- moto emula la API, no la factura ni todos los valores por defecto."]

        titulo("Una base creada solo con lo obligatorio")
        aws("rds", "create-db-instance", "--db-instance-identifier", "pruebas",
            "--engine", "postgres", "--db-instance-class", "db.t4g.micro",
            "--allocated-storage", "20", "--master-username", "admin_app",
            "--master-user-password", "Contrasena-de-prueba-1", "--query", "DBInstance.DBInstanceIdentifier",
            mostrar="rds create-db-instance --db-instance-identifier pruebas --engine postgres "
                    "--db-instance-class db.t4g.micro --allocated-storage 20 "
                    "--master-username admin_app --master-user-password ****")
        aws("rds", "describe-db-instances", "--db-instance-identifier", "pruebas", "--query", Q,
            mostrar="rds describe-db-instances --db-instance-identifier pruebas --query <valores por defecto>")

        titulo("Protección contra el borrado")
        aws("rds", "create-db-instance", "--db-instance-identifier", "produccion",
            "--engine", "postgres", "--db-instance-class", "db.t4g.micro",
            "--allocated-storage", "20", "--master-username", "admin_app",
            "--master-user-password", "Contrasena-de-prueba-1", "--deletion-protection",
            "--storage-encrypted", "--backup-retention-period", "14", "--no-publicly-accessible",
            "--query", "DBInstance.DBInstanceIdentifier",
            mostrar="rds create-db-instance --db-instance-identifier produccion ... "
                    "--deletion-protection --storage-encrypted --backup-retention-period 14 "
                    "--no-publicly-accessible")
        aws("rds", "describe-db-instances", "--db-instance-identifier", "produccion", "--query", Q,
            mostrar="rds describe-db-instances --db-instance-identifier produccion --query <los mismos campos>")
        aws("rds", "delete-db-instance", "--db-instance-identifier", "produccion",
            "--skip-final-snapshot")

        titulo("El snapshot que sobrevive a la base")
        aws("rds", "create-db-snapshot", "--db-instance-identifier", "pruebas",
            "--db-snapshot-identifier", "antes-de-borrar", "--query", "DBSnapshot.Status")
        aws("rds", "delete-db-instance", "--db-instance-identifier", "pruebas",
            "--skip-final-snapshot", "--query", "DBInstance.DBInstanceStatus")
        aws("rds", "describe-db-snapshots",
            "--query", "DBSnapshots[].{Snapshot:DBSnapshotIdentifier,Base:DBInstanceIdentifier,"
                       "Tipo:SnapshotType,GiB:AllocatedStorage}")

        (AQUI / "SALIDA.md").write_text("\n".join(cab + partes) + "\n", encoding="utf-8")
        print("SALIDA.md escrito")
    finally:
        moto.terminate()


if __name__ == "__main__":
    main()
