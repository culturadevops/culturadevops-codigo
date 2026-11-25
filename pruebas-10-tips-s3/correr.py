# -*- coding: utf-8 -*-
"""10 tips para S3 — las demos que se pueden ejecutar, contra un emulador (moto) con la CLI de AWS.

Todo va a SALIDA.md: lo que sale en el vídeo 281 se copia de ahí. Sin cuenta de AWS.

    python correr.py

⚠️ moto emula la API, no la facturación: que algo «cuesta» lo dice la documentación de AWS
   (citada en la descripción), no este banco. Aquí se demuestra lo que se VE y lo que NO se ve.
"""
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PUERTO = 5088
EP = f"http://127.0.0.1:{PUERTO}"
ENV = dict(os.environ, AWS_ACCESS_KEY_ID="test", AWS_SECRET_ACCESS_KEY="test",
           AWS_DEFAULT_REGION="us-east-1", AWS_ENDPOINT_URL=EP, AWS_PAGER="",
           PYTHONIOENCODING="utf-8")
partes = []


def aws(*args, mostrar=None):
    cmd = ["aws", *args]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=ENV, cwd=AQUI)
    txt = (r.stdout + r.stderr).strip()
    partes.extend(["", f"`$ aws {mostrar or ' '.join(args)}`", "", "```", txt or "(sin salida)", "```"])
    print(f"$ aws {mostrar or ' '.join(args)}\n{txt}\n", flush=True)
    return txt


def titulo(t):
    partes.extend(["", f"## {t}"])
    print(f"\n=== {t}", flush=True)


def main():
    (AQUI / "parte.bin").write_bytes(os.urandom(5 * 1024 * 1024))   # 5 MiB: el mínimo de una parte
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
        cab = ["# SALIDA — 10 tips para S3 (demos ejecutadas)", "",
               "Generado por `python correr.py`. **No se edita a mano.**", "",
               f"- fecha: {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC",
               f"- {subprocess.run(['aws', '--version'], capture_output=True, text=True).stdout.strip()}",
               f"- moto {moto_pkg.__version__} (emulador de la API de AWS, en {EP})",
               "- moto emula la API, no la factura: el coste lo dice la documentación de AWS."]

        # ── Tip: las subidas multiparte incompletas ─────────────────────────────────────────
        titulo("Subidas multiparte incompletas: ocupan y no se ven")
        aws("s3api", "create-bucket", "--bucket", "tips-mpu")
        up = aws("s3api", "create-multipart-upload", "--bucket", "tips-mpu", "--key", "backup.tar",
                 "--query", "UploadId", "--output", "text")
        aws("s3api", "upload-part", "--bucket", "tips-mpu", "--key", "backup.tar",
            "--part-number", "1", "--body", "parte.bin", "--upload-id", up, "--query", "ETag",
            mostrar="s3api upload-part --bucket tips-mpu --key backup.tar --part-number 1 "
                    "--body parte.bin (5 MiB) --upload-id <id> --query ETag")
        aws("s3", "ls", "s3://tips-mpu", "--recursive", "--summarize")
        aws("s3api", "list-multipart-uploads", "--bucket", "tips-mpu",
            "--query", "Uploads[].{Key:Key,Initiated:Initiated}")
        aws("s3api", "list-parts", "--bucket", "tips-mpu", "--key", "backup.tar", "--upload-id", up,
            "--query", "Parts[].{Part:PartNumber,Size:Size}",
            mostrar="s3api list-parts --bucket tips-mpu --key backup.tar --upload-id <id> "
                    "--query Parts[].{Part:PartNumber,Size:Size}")
        (AQUI / "lifecycle-mpu.json").write_text(
            '{"Rules":[{"ID":"limpiar-multiparte","Status":"Enabled","Filter":{"Prefix":""},'
            '"AbortIncompleteMultipartUpload":{"DaysAfterInitiation":7}}]}', encoding="utf-8")
        aws("s3api", "put-bucket-lifecycle-configuration", "--bucket", "tips-mpu",
            "--lifecycle-configuration", "file://lifecycle-mpu.json")
        aws("s3api", "get-bucket-lifecycle-configuration", "--bucket", "tips-mpu")

        # ── Tip: con versionado, borrar no borra ────────────────────────────────────────────
        titulo("Con versionado, borrar no borra")
        aws("s3api", "create-bucket", "--bucket", "tips-versiones")
        aws("s3api", "put-bucket-versioning", "--bucket", "tips-versiones",
            "--versioning-configuration", "Status=Enabled")
        for i in (1, 2, 3):
            aws("s3api", "put-object", "--bucket", "tips-versiones", "--key", "informe.csv",
                "--body", "parte.bin", "--query", "VersionId",
                mostrar=f"s3api put-object --bucket tips-versiones --key informe.csv --body parte.bin (5 MiB) · vez {i}")
        aws("s3", "rm", "s3://tips-versiones/informe.csv")
        aws("s3", "ls", "s3://tips-versiones", "--recursive", "--summarize")
        aws("s3api", "list-object-versions", "--bucket", "tips-versiones",
            "--query", "{Versiones:Versions[].{Key:Key,Size:Size,IsLatest:IsLatest},"
                       "MarcasDeBorrado:DeleteMarkers[].{Key:Key,IsLatest:IsLatest}}")
        (AQUI / "lifecycle-versiones.json").write_text(
            '{"Rules":[{"ID":"versiones-viejas","Status":"Enabled","Filter":{"Prefix":""},'
            '"NoncurrentVersionExpiration":{"NoncurrentDays":30},'
            '"Expiration":{"ExpiredObjectDeleteMarker":true}}]}', encoding="utf-8")
        aws("s3api", "put-bucket-lifecycle-configuration", "--bucket", "tips-versiones",
            "--lifecycle-configuration", "file://lifecycle-versiones.json")
        aws("s3api", "get-bucket-lifecycle-configuration", "--bucket", "tips-versiones")

        (AQUI / "SALIDA.md").write_text("\n".join(cab + partes) + "\n", encoding="utf-8")
        print("SALIDA.md escrito")
    finally:
        moto.terminate()
        for f in ("parte.bin",):
            (AQUI / f).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
