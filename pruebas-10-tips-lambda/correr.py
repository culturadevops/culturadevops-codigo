# -*- coding: utf-8 -*-
"""10 tips para Lambda — demos ejecutables con la AWS CLI contra un emulador (moto). SALIDA.md.

⚠️ moto emula la API, no la factura: los costos y límites los dice la documentación (EXPEDIENTE).

    python correr.py
"""
import io
import os
import subprocess
import sys
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PUERTO = 5090
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
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("app.py", "def handler(event, context):\n    return {'ok': True}\n")
    (AQUI / "funcion.zip").write_bytes(buf.getvalue())
    (AQUI / "confianza.json").write_text(
        '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":'
        '{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}', encoding="utf-8")
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
        cab = ["# SALIDA — 10 tips para Lambda (demos ejecutadas)", "",
               "Generado por `python correr.py`. **No se edita a mano.**", "",
               f"- fecha: {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC",
               f"- {subprocess.run(['aws', '--version'], capture_output=True, text=True).stdout.strip()}",
               f"- moto {moto_pkg.__version__} (emulador de la API de AWS)",
               "- moto emula la API, no la factura: los costos los dice la documentación."]

        rol = aws("iam", "create-role", "--role-name", "rol-lambda",
                  "--assume-role-policy-document", "file://confianza.json",
                  "--query", "Role.Arn", "--output", "text", guardar=False)

        titulo("Los valores por defecto de una función")
        aws("lambda", "create-function", "--function-name", "procesar", "--runtime", "python3.13",
            "--handler", "app.handler", "--role", rol, "--zip-file", "fileb://funcion.zip",
            "--query", "{Timeout:Timeout,MemorySize:MemorySize,Architectures:Architectures}",
            mostrar="lambda create-function --function-name procesar --runtime python3.13 "
                    "--handler app.handler --role <rol> --zip-file fileb://funcion.zip")
        aws("lambda", "update-function-configuration", "--function-name", "procesar",
            "--timeout", "30", "--memory-size", "1769",
            "--query", "{Timeout:Timeout,MemorySize:MemorySize}")
        # La arquitectura va con update-function-code --architectures; moto 5.2.3 la ignora
        # (devuelve x86_64), así que esa demo no se hace: el tip de arm64 va con la documentación.

        titulo("Logs que no caducan nunca")
        aws("logs", "create-log-group", "--log-group-name", "/aws/lambda/procesar")
        aws("logs", "describe-log-groups", "--log-group-name-prefix", "/aws/lambda/procesar",
            "--query", "logGroups[].{Grupo:logGroupName,DiasDeRetencion:retentionInDays}")
        aws("logs", "put-retention-policy", "--log-group-name", "/aws/lambda/procesar",
            "--retention-in-days", "14")
        aws("logs", "describe-log-groups", "--log-group-name-prefix", "/aws/lambda/procesar",
            "--query", "logGroups[].{Grupo:logGroupName,DiasDeRetencion:retentionInDays}")

        titulo("Una Function URL sin autenticación")
        aws("lambda", "create-function-url-config", "--function-name", "procesar",
            "--auth-type", "NONE", "--query", "{Url:FunctionUrl,Auth:AuthType}")

        titulo("Concurrencia reservada: tope y freno")
        aws("lambda", "put-function-concurrency", "--function-name", "procesar",
            "--reserved-concurrent-executions", "10")
        aws("lambda", "put-function-concurrency", "--function-name", "procesar",
            "--reserved-concurrent-executions", "0")
        aws("lambda", "get-function-concurrency", "--function-name", "procesar")

        (AQUI / "SALIDA.md").write_text("\n".join(cab + partes) + "\n", encoding="utf-8")
        print("SALIDA.md escrito")
    finally:
        moto.terminate()


if __name__ == "__main__":
    main()
