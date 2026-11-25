# -*- coding: utf-8 -*-
"""10 tips para IAM — demos ejecutables con la AWS CLI contra un emulador (moto). SALIDA.md.

⚠️ moto emula la API: las cuentas, fechas e identificadores son del emulador.

    python correr.py
"""
import base64
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PUERTO = 5091
EP = f"http://127.0.0.1:{PUERTO}"
ENV = dict(os.environ, AWS_ACCESS_KEY_ID="test", AWS_SECRET_ACCESS_KEY="test",
           AWS_DEFAULT_REGION="us-east-1", AWS_ENDPOINT_URL=EP, AWS_PAGER="",
           PYTHONIOENCODING="utf-8")
partes = []


def aws(*args, mostrar=None, guardar=True, transformar=None):
    r = subprocess.run(["aws", *args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=ENV, cwd=AQUI)
    txt = (r.stdout + r.stderr).strip()
    if transformar:
        txt = transformar(txt)
    if guardar:
        partes.extend(["", f"`$ aws {mostrar or ' '.join(args)}`", "", "```", txt or "(sin salida)", "```"])
        print(f"$ aws {mostrar or ' '.join(args)}\n{txt}\n", flush=True)
    return txt


def titulo(t):
    partes.extend(["", f"## {t}"])
    print(f"\n=== {t}", flush=True)


def main():
    (AQUI / "confianza.json").write_text(
        '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":'
        '{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}', encoding="utf-8")
    (AQUI / "limite.json").write_text(
        '{"Version":"2012-10-17","Statement":[{"Effect":"Allow",'
        '"Action":["s3:*","logs:*"],"Resource":"*"}]}', encoding="utf-8")
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
        cab = ["# SALIDA — 10 tips para IAM (demos ejecutadas)", "",
               "Generado por `python correr.py`. **No se edita a mano.**", "",
               f"- fecha: {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC",
               f"- {subprocess.run(['aws', '--version'], capture_output=True, text=True).stdout.strip()}",
               f"- moto {moto_pkg.__version__} (emulador de la API de AWS)",
               "- cuentas, fechas e identificadores: los del emulador."]

        titulo("El resumen de la cuenta: ¿tiene MFA el root?")
        aws("iam", "get-account-summary",
            "--query", "SummaryMap.{AccountMFAEnabled:AccountMFAEnabled,"
                       "AccountAccessKeysPresent:AccountAccessKeysPresent,Users:Users}")

        titulo("Claves de acceso que nadie usa")
        aws("iam", "create-user", "--user-name", "ci-antiguo", "--query", "User.UserName")
        aws("iam", "create-access-key", "--user-name", "ci-antiguo",
            "--query", "AccessKey.{Usuario:UserName,Estado:Status}")
        aws("iam", "generate-credential-report", "--query", "State")
        time.sleep(1)

        def csv(t):
            try:
                crudo = base64.b64decode(eval(t)).decode()   # la CLI la devuelve como JSON string
            except Exception:
                crudo = t
            filas = [l.split(",") for l in crudo.strip().splitlines()]
            cab_csv = filas[0]
            keep = ["user", "password_enabled", "mfa_active", "access_key_1_active",
                    "access_key_1_last_used_date"]
            idx = [cab_csv.index(k) for k in keep if k in cab_csv]
            return "\n".join(",".join(f[i] for i in idx) for f in filas)
        aws("iam", "get-credential-report", "--query", "Content",
            mostrar="iam get-credential-report  (columnas: user, password_enabled, mfa_active, "
                    "access_key_1_active, access_key_1_last_used_date)", transformar=csv)

        titulo("Un límite de permisos para delegar")
        aws("iam", "create-policy", "--policy-name", "limite-desarrollo",
            "--policy-document", "file://limite.json", "--query", "Policy.PolicyName")
        arn = aws("iam", "list-policies", "--scope", "Local",
                  "--query", "Policies[?PolicyName=='limite-desarrollo'].Arn | [0]",
                  "--output", "text", guardar=False)
        aws("iam", "create-role", "--role-name", "rol-de-un-dev",
            "--assume-role-policy-document", "file://confianza.json",
            "--permissions-boundary", arn, "--query", "Role.RoleName",
            mostrar="iam create-role --role-name rol-de-un-dev --assume-role-policy-document "
                    "file://confianza.json --permissions-boundary <arn de limite-desarrollo>")
        aws("iam", "get-role", "--role-name", "rol-de-un-dev",
            "--query", "Role.PermissionsBoundary")

        (AQUI / "SALIDA.md").write_text("\n".join(cab + partes) + "\n", encoding="utf-8")
        print("SALIDA.md escrito")
    finally:
        moto.terminate()


if __name__ == "__main__":
    main()
