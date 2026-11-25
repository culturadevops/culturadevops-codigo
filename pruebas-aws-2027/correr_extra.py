# -*- coding: utf-8 -*-
"""Banco extra del vídeo 413: versionado de S3, el que te salva de un borrado. Contra moto (sin IAM: moto propio).
  · activar el versionado; subir v1 y v2 del mismo archivo; borrarlo; listar versiones; recuperar la v1.
    python correr_extra.py   -> SALIDA-extra.md
"""
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
OUT = []
NET = "lab-aws27"


def run(args):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (p.stdout + p.stderr).strip(), p.returncode


def aws(args):
    return run(["docker", "run", "--rm", "--network", NET, "-e", "AWS_ACCESS_KEY_ID=a", "-e", "AWS_SECRET_ACCESS_KEY=a",
                "-e", "AWS_DEFAULT_REGION=us-east-1", "-v", f"{AQUI.as_posix()}/tmp:/aws", "amazon/aws-cli",
                "--endpoint-url", "http://moto2:5000"] + args)


def bloque(titulo, mostrado, res, nota=None):
    s, rc = res
    OUT.append(f"### {titulo}\n\n`$ {mostrado}`\n\n```\n{s}\n```\n(código de salida {rc})\n" + (f"\n> {nota}\n" if nota else ""))
    print(f"[{rc}] {titulo}")
    return s, rc


def main():
    (AQUI / "tmp").mkdir(exist_ok=True)
    run(["docker", "rm", "-f", "moto2"])
    run(["docker", "network", "create", NET])
    run(["docker", "run", "-d", "--name", "moto2", "--network", NET, "motoserver/moto"])
    time.sleep(4)
    OUT.append(f"# SALIDA extra — versionado de S3 (vídeo 413)\n\nGenerado {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC con `python correr_extra.py`. "
               "CLI oficial contra moto; moto no es AWS.\n")
    aws(["s3api", "create-bucket", "--bucket", "contratos"])
    bloque("activar el versionado", "aws s3api put-bucket-versioning --bucket contratos --versioning-configuration Status=Enabled",
           aws(["s3api", "put-bucket-versioning", "--bucket", "contratos", "--versioning-configuration", "Status=Enabled"]))
    (AQUI / "tmp" / "v1.txt").write_text("contrato firmado: 1.000 USD\n", encoding="utf-8")
    (AQUI / "tmp" / "v2.txt").write_text("contrato BORRADOR\n", encoding="utf-8")
    aws(["s3", "cp", "/aws/v1.txt", "s3://contratos/contrato.txt"])
    aws(["s3", "cp", "/aws/v2.txt", "s3://contratos/contrato.txt"])
    bloque("alguien lo pisa con un borrador, y luego lo borra", "aws s3 cp v2.txt s3://contratos/contrato.txt; aws s3 rm s3://contratos/contrato.txt",
           aws(["s3", "rm", "s3://contratos/contrato.txt"]))
    bloque("¿está?", "aws s3 ls s3://contratos/", aws(["s3", "ls", "s3://contratos/"]))
    s, _ = aws(["s3api", "list-object-versions", "--bucket", "contratos", "--output", "json"])
    d = json.loads(s)
    filas = [f"versión  {v['VersionId'][:8]}…  {v['Size']} bytes  {'(la más reciente)' if v['IsLatest'] else ''}".rstrip()
             for v in d.get("Versions", [])]
    filas += [f"marca de borrado  {m['VersionId'][:8]}…  {'(la más reciente)' if m['IsLatest'] else ''}".rstrip()
              for m in d.get("DeleteMarkers", [])]
    OUT.append("### las versiones que guarda\n\n`$ aws s3api list-object-versions --bucket contratos`\n\n```\n" + "\n".join(filas) + "\n```\n")
    print("[0] versiones")
    vieja = sorted(d["Versions"], key=lambda v: v["LastModified"])[0]["VersionId"]
    bloque("recuperar la primera versión", "aws s3api get-object --bucket contratos --key contrato.txt --version-id … recuperado.txt",
           aws(["s3api", "get-object", "--bucket", "contratos", "--key", "contrato.txt", "--version-id", vieja, "/aws/recuperado.txt",
                "--query", "ContentLength"]))
    bloque("su contenido", "cat recuperado.txt", ((AQUI / "tmp" / "recuperado.txt").read_text(encoding="utf-8").strip(), 0))
    run(["docker", "rm", "-f", "moto2"])
    (AQUI / "SALIDA-extra.md").write_text("\n".join(OUT), encoding="utf-8")
    print("ok SALIDA-extra.md")


if __name__ == "__main__":
    main()
