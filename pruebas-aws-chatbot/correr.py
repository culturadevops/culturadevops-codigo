# -*- coding: utf-8 -*-
"""AWS Chatbot (Amazon Q Developer in chat applications) — demos ejecutables para los vídeos
357, 358 y 359 de cultura-devops. Escribe SALIDA.md.

Qué se ejecuta y qué no:
  · la AWS CLI de verdad: `aws chatbot help` y los esqueletos `--generate-cli-skeleton` (no
    necesitan cuenta, salen del modelo de la API que trae la CLI);
  · SNS, CloudWatch, EventBridge y SQS contra moto (emulador de la API de AWS);
  · el validador de notificaciones personalizadas (validar_notificacion.py).
⚠️ moto NO emula el servicio chatbot, ni ejecuta las acciones de una alarma, y un destino SNS
   con InputTransformer le da un 500 (fallo del emulador): por eso el evento transformado se
   manda a una cola SQS «espía», que enseña exactamente el JSON que recibiría el tema SNS.
⚠️ El tramo Slack/Teams no se puede ejecutar sin un workspace real. No se simula.

    python correr.py
"""
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).resolve().parent
EJ = AQUI / "ejemplos"
PUERTO = 5095
EP = f"http://127.0.0.1:{PUERTO}"
REGION = "us-east-2"
BASE = dict(os.environ, AWS_PAGER="", PYTHONIOENCODING="utf-8", PYTHONUTF8="1",
            AWS_CLI_FILE_ENCODING="UTF-8")  # sin esto la CLI lee file:// en cp1252 y rompe las tildes
ENV = dict(BASE, AWS_ACCESS_KEY_ID="test", AWS_SECRET_ACCESS_KEY="test",
           AWS_DEFAULT_REGION=REGION, AWS_ENDPOINT_URL=EP)
partes = []


def correr(argv, mostrar, env=ENV):
    r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=env, cwd=AQUI)
    return (r.stdout + r.stderr).strip()


def anotar(mostrar, txt):
    partes.extend(["", f"`$ {mostrar}`", "", "```", txt or "(sin salida)", "```"])
    print(f"$ {mostrar}\n{txt}\n", flush=True)


def aws(*args, mostrar=None, guardar=True, env=ENV):
    txt = correr(["aws", *args], mostrar, env)
    if guardar:
        anotar("aws " + (mostrar or " ".join(args)), txt)
    return txt


def titulo(t):
    partes.extend(["", f"## {t}"])
    print(f"\n=== {t}", flush=True)


def nota(t):
    partes.extend(["", f"> {t}"])


def ejemplos():
    EJ.mkdir(exist_ok=True)
    casos = {
        "minima.json": {"version": "1.0", "source": "custom",
                        "content": {"description": ":warning: Falló el despliegue de *pagos*"}},
        "completa.json": {
            "version": "1.0", "source": "custom", "id": "despliegue-pagos-42",
            "content": {"textType": "client-markdown",
                        "title": ":rotating_light: pagos no responde",
                        "description": "El servicio *pagos* devuelve 5xx desde las 12:03.",
                        "nextSteps": ["Revisar el runbook de pagos",
                                      "Si sigue en 30 min, escalar a guardia"],
                        "keywords": ["pagos", "critico", "SRE"]},
            "metadata": {"threadId": "incidente-pagos-42", "summary": "Incidente de pagos",
                         "additionalContext": {"prioridad": "alta"},
                         "enableCustomActions": True}},
        "source_aws.json": {"version": "1.0", "source": "aws",
                            "content": {"description": "hola"}},
        "titulo_largo.json": {"version": "1.0", "source": "custom",
                              "content": {"title": "x" * 300, "description": "hola"}},
        "sin_description.json": {"version": "1.0", "source": "custom",
                                 "content": {"title": "Sin cuerpo"}},
    }
    for nombre, cuerpo in casos.items():
        (EJ / nombre).write_text(json.dumps(cuerpo, ensure_ascii=False, indent=2), encoding="utf-8")
    return list(casos)


def main():
    import moto as moto_pkg
    cab = ["# SALIDA — AWS Chatbot / Amazon Q Developer in chat applications (demos ejecutadas)", "",
           "Generado por `python correr.py`. **No se edita a mano.**", "",
           f"- fecha: {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC",
           f"- {correr(['aws', '--version'], '', BASE)}",
           f"- moto {moto_pkg.__version__} (emulador de la API de AWS) · región {REGION}",
           "- moto NO emula chatbot ni ejecuta acciones de alarmas; el tramo Slack/Teams no se ejecuta."]

    # ── 1. La CLI sin cuenta ──────────────────────────────────────────────
    titulo("La CLI sigue diciendo chatbot (sin cuenta, sin emulador)")
    ayuda = correr(["aws", "chatbot", "help"], "", BASE).splitlines()
    regiones = [l.strip() for l in ayuda if l.strip().startswith("* ") and '"' in l]
    i = next(n for n, l in enumerate(ayuda) if "console can only be used" in l)
    consola = [l.strip() for l in ayuda[i:i + 3]]
    anotar("aws chatbot help   # las regiones", "\n".join(regiones + [""] + consola))
    cmds = [l.strip()[2:] for l in ayuda if l.strip().startswith("* ") and '"' not in l]
    anotar("aws chatbot help   # cuántos comandos, y los de Slack",
           f"{len(cmds)} comandos\n" + "\n".join(c for c in cmds if "slack" in c))
    aws("chatbot", "create-slack-channel-configuration", "--generate-cli-skeleton", env=BASE)

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

        # ── 2. El cableado: alarma → SNS ───────────────────────────────────
        titulo("Alarma de CloudWatch → tema SNS (contra moto)")
        tema = aws("sns", "create-topic", "--name", "alertas-produccion", "--query", "TopicArn",
                   "--output", "text")
        aws("cloudwatch", "put-metric-alarm", "--alarm-name", "cpu-alta", "--namespace", "AWS/EC2",
            "--metric-name", "CPUUtilization", "--statistic", "Average", "--period", "300",
            "--evaluation-periods", "1", "--threshold", "80",
            "--comparison-operator", "GreaterThanThreshold", "--alarm-actions", tema,
            mostrar="cloudwatch put-metric-alarm --alarm-name cpu-alta --metric-name CPUUtilization "
                    "--threshold 80 ... --alarm-actions <tema alertas-produccion>")
        aws("cloudwatch", "describe-alarms", "--alarm-names", "cpu-alta", "--query",
            "MetricAlarms[0].{Alarma:AlarmName,Umbral:Threshold,Acciones:AlarmActions}")
        nota("Lo que pasa cuando la alarma dispara (publicar en el tema y que Chatbot lo lleve al "
             "canal) lo hace AWS; moto no ejecuta las acciones de una alarma.")

        # ── 3. Notificaciones personalizadas ───────────────────────────────
        titulo("Notificaciones personalizadas: el validador")
        archivos = ejemplos()
        for a in ("minima.json", "completa.json"):
            anotar(f"cat ejemplos/{a}", (EJ / a).read_text(encoding="utf-8"))
        anotar("python validar_notificacion.py ejemplos/*.json",
               correr([sys.executable, "validar_notificacion.py",
                       *[f"ejemplos/{a}" for a in archivos]], "", BASE))

        titulo("Publicar en SNS y ver lo que llega (cola espía, contra moto)")
        cola = aws("sqs", "create-queue", "--queue-name", "espia", "--query", "QueueUrl",
                   "--output", "text", guardar=False)
        cola_arn = aws("sqs", "get-queue-attributes", "--queue-url", cola, "--attribute-names",
                       "QueueArn", "--query", "Attributes.QueueArn", "--output", "text",
                       guardar=False)
        aws("sns", "subscribe", "--topic-arn", tema, "--protocol", "sqs", "--notification-endpoint",
            cola_arn, "--attributes", "RawMessageDelivery=true", "--query", "SubscriptionArn",
            mostrar="sns subscribe --topic-arn <alertas-produccion> --protocol sqs "
                    "--notification-endpoint <cola espia> --attributes RawMessageDelivery=true")
        aws("sns", "publish", "--topic-arn", tema, "--message", "file://ejemplos/completa.json",
            "--query", "MessageId",
            mostrar="sns publish --topic-arn <alertas-produccion> --message file://ejemplos/completa.json")
        cuerpo = aws("sqs", "receive-message", "--queue-url", cola, "--query", "Messages[0].Body",
                     "--output", "text", guardar=False)
        recibido = json.loads(cuerpo)
        enviado = json.loads((EJ / "completa.json").read_text(encoding="utf-8"))
        anotar("aws sqs receive-message --queue-url <espia>   # y se compara con el archivo",
               f"threadId: {recibido['metadata']['threadId']}\n"
               f"title:    {recibido['content']['title']}\n"
               f"idéntico a ejemplos/completa.json: {'sí' if recibido == enviado else 'NO'}")

        titulo("EventBridge + input transformer → formato de Chatbot (contra moto)")
        aws("events", "put-rule", "--name", "despliegues", "--event-pattern",
            '{"source":["mi.app"],"detail-type":["despliegue"]}', "--query", "RuleArn")
        objetivo = [{"Id": "espia", "Arn": cola_arn, "InputTransformer": {
            "InputPathsMap": {"svc": "$.detail.servicio", "ver": "$.detail.version"},
            "InputTemplate": '{"version":"1.0","source":"custom","content":{"description":'
                             '":rocket: <svc> <ver> desplegado"}}'}}]
        (EJ / "objetivo.json").write_text(json.dumps(objetivo, ensure_ascii=False, indent=2),
                                          encoding="utf-8")
        anotar("cat ejemplos/objetivo.json", (EJ / "objetivo.json").read_text(encoding="utf-8"))
        aws("events", "put-targets", "--rule", "despliegues", "--targets",
            "file://ejemplos/objetivo.json", "--query", "FailedEntryCount")
        aws("events", "put-events", "--entries",
            json.dumps([{"Source": "mi.app", "DetailType": "despliegue",
                         "Detail": json.dumps({"servicio": "pagos", "version": "2.4.1"})}]),
            "--query", "FailedEntryCount",
            mostrar="events put-events --entries '[{\"Source\":\"mi.app\",\"DetailType\":"
                    "\"despliegue\",\"Detail\":\"{\\\"servicio\\\":\\\"pagos\\\",\\\"version\\\":"
                    "\\\"2.4.1\\\"}\"}]'")
        time.sleep(1)
        aws("sqs", "receive-message", "--queue-url", cola, "--query", "Messages[0].Body",
            "--output", "text", mostrar="sqs receive-message --queue-url <espia>")
        nota("En tu cuenta el destino de la regla es el tema SNS suscrito a Chatbot; aquí es una "
             "cola porque moto da un 500 con destino SNS + InputTransformer.")
    finally:
        moto.terminate()

    # ── 4. Lo que se configura (sin cuenta) ───────────────────────────────
    titulo("Preferencias de la cuenta y acciones personalizadas (esqueletos de la CLI)")
    aws("chatbot", "update-account-preferences", "--generate-cli-skeleton", env=BASE)
    aws("chatbot", "create-custom-action", "--generate-cli-skeleton", env=BASE)
    nota("⚠️ Un esqueleto pone `true` o `\"\"` según el TIPO del campo: NO son los valores por "
         "defecto. Los valores por defecto se citan de la referencia de la API, no de aquí.")

    (AQUI / "SALIDA.md").write_text("\n".join(cab + partes) + "\n", encoding="utf-8")
    print("→ SALIDA.md")


if __name__ == "__main__":
    main()
